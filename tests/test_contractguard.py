"""Tests for contractguard's learn/check engine."""

import contractguard as cg
from contractguard.report import (
    CARDINALITY_CHANGED,
    KEY_MISSING,
    NEW_KEY,
    TYPE_CHANGED,
)


def test_identical_payload_has_no_drift():
    sample = {"user": {"id": 1, "name": "ana"}}
    contract = cg.learn([sample])
    report = contract.check({"user": {"id": 2, "name": "bob"}})
    assert not report.drifted
    assert report.changes == []


def test_type_change_is_detected():
    contract = cg.learn([{"age": 30}])
    report = contract.check({"age": "thirty"})
    assert report.drifted
    changes = report.by_kind(TYPE_CHANGED)
    assert len(changes) == 1
    assert changes[0].path == "age"
    assert "int" in changes[0].detail and "str" in changes[0].detail


def test_missing_required_key_is_detected():
    contract = cg.learn([{"id": 1, "email": "a@b.com"}])
    report = contract.check({"id": 2})
    missing = report.by_kind(KEY_MISSING)
    assert len(missing) == 1
    assert missing[0].path == "email"


def test_new_key_is_detected():
    contract = cg.learn([{"id": 1}])
    report = contract.check({"id": 2, "phone": "555"})
    new = report.by_kind(NEW_KEY)
    assert len(new) == 1
    assert new[0].path == "phone"


def test_optional_field_is_lenient():
    # 'email' present in one sample, absent in another -> optional.
    contract = cg.learn([{"id": 1, "email": "a@b.com"}, {"id": 2}])
    # A later payload without email must NOT be flagged.
    report = contract.check({"id": 3})
    assert not report.drifted


def test_nested_type_change_path():
    contract = cg.learn([{"user": {"address": {"zip": 12345}}}])
    report = contract.check({"user": {"address": {"zip": "12345"}}})
    changes = report.by_kind(TYPE_CHANGED)
    assert len(changes) == 1
    assert changes[0].path == "user.address.zip"


def test_container_kind_change_does_not_cascade():
    contract = cg.learn([{"items": [1, 2, 3]}])
    report = contract.check({"items": {"a": 1}})
    # Exactly one change: list -> dict at 'items'. No spurious child noise.
    assert len(report.changes) == 1
    assert report.changes[0].path == "items"


def test_list_element_type_drift():
    contract = cg.learn([{"tags": ["a", "b"]}])
    report = contract.check({"tags": ["a", 99]})
    card = report.by_kind(CARDINALITY_CHANGED)
    assert len(card) == 1
    assert card[0].path == "tags[1]"


def test_nullable_field_not_flagged():
    # null seen during learning -> null is allowed later.
    contract = cg.learn([{"middle_name": None}, {"middle_name": "lee"}])
    report = contract.check({"middle_name": None})
    assert not report.drifted


def test_save_and_load_roundtrip(tmp_path):
    contract = cg.learn([{"id": 1, "name": "ana"}])
    path = tmp_path / "contract.json"
    contract.save(str(path))
    reloaded = cg.Contract.load(str(path))
    report = reloaded.check({"id": 2})  # missing required 'name'
    assert report.by_kind(KEY_MISSING)[0].path == "name"


def test_report_bool_and_str():
    contract = cg.learn([{"x": 1}])
    clean = contract.check({"x": 2})
    assert not clean
    assert "No drift" in str(clean)
    drifted = contract.check({"x": "two"})
    assert drifted
    assert "change(s) detected" in str(drifted)


def test_learn_requires_samples():
    try:
        cg.learn([])
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError for empty samples")
