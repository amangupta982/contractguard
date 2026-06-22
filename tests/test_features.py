"""Tests for strict mode, the pytest plugin, and the CLI."""

import json

import pytest

import contractguard as cg
from contractguard.cli import main as cli_main
from contractguard.pytest_plugin import assert_no_drift


# -- strict mode ----------------------------------------------------------
def test_strict_marks_optional_as_required():
    # 'email' is missing from the second sample, so lenient learning would
    # mark it optional. Strict learning must require it.
    samples = [{"id": 1, "email": "a@b.com"}, {"id": 2}]

    lenient = cg.learn(samples)
    assert not lenient.check({"id": 3}).drifted  # optional -> no drift

    strict = cg.learn(samples, strict=True)
    report = strict.check({"id": 3})
    assert report.drifted
    assert report.by_kind("KeyMissing")[0].path == "email"


def test_strict_nested_required():
    strict = cg.learn([{"user": {"id": 1, "name": "ana"}}], strict=True)
    report = strict.check({"user": {"id": 2}})  # missing nested 'name'
    assert report.by_kind("KeyMissing")[0].path == "user.name"


# -- pytest plugin --------------------------------------------------------
def test_assert_no_drift_passes_on_match():
    contract = cg.learn([{"id": 1, "name": "ana"}])
    # Should not raise.
    assert_no_drift(contract, {"id": 2, "name": "bob"})


def test_assert_no_drift_raises_on_drift():
    contract = cg.learn([{"id": 1}])
    with pytest.raises(AssertionError) as excinfo:
        assert_no_drift(contract, {"id": "one"})
    assert "drift" in str(excinfo.value).lower()


def test_assert_no_drift_accepts_samples_list():
    # Passing raw samples should learn on the fly.
    assert_no_drift([{"id": 1}], {"id": 2})


def test_assert_no_drift_accepts_file_path(tmp_path):
    contract = cg.learn([{"id": 1, "name": "ana"}])
    path = tmp_path / "contract.json"
    contract.save(str(path))
    with pytest.raises(AssertionError):
        assert_no_drift(str(path), {"id": 2})  # missing required 'name'


def test_assert_no_drift_rejects_bad_type():
    with pytest.raises(TypeError):
        assert_no_drift(42, {"id": 1})


# -- CLI ------------------------------------------------------------------
def _write_json(path, obj):
    path.write_text(json.dumps(obj))
    return str(path)


def test_cli_learn_then_check_clean(tmp_path, capsys):
    s1 = _write_json(tmp_path / "s1.json", {"id": 1, "name": "ana"})
    s2 = _write_json(tmp_path / "s2.json", {"id": 2, "name": "bob"})
    contract_path = str(tmp_path / "contract.json")

    rc = cli_main(["learn", s1, s2, "-o", contract_path])
    assert rc == 0
    assert "Learned contract" in capsys.readouterr().out

    payload = _write_json(tmp_path / "good.json", {"id": 3, "name": "cleo"})
    rc = cli_main(["check", payload, "--against", contract_path])
    assert rc == 0
    assert "No drift" in capsys.readouterr().out


def test_cli_check_reports_drift_and_exits_nonzero(tmp_path, capsys):
    s1 = _write_json(tmp_path / "s1.json", {"age": 30})
    contract_path = str(tmp_path / "contract.json")
    cli_main(["learn", s1, "-o", contract_path])
    capsys.readouterr()  # clear

    bad = _write_json(tmp_path / "bad.json", {"age": "thirty"})
    rc = cli_main(["check", bad, "--against", contract_path])
    assert rc == 1  # non-zero on drift, for CI
    assert "TypeChanged" in capsys.readouterr().out


def test_cli_strict_flag(tmp_path, capsys):
    s1 = _write_json(tmp_path / "s1.json", {"id": 1, "email": "a@b.com"})
    s2 = _write_json(tmp_path / "s2.json", {"id": 2})
    contract_path = str(tmp_path / "contract.json")
    cli_main(["learn", s1, s2, "-o", contract_path, "--strict"])
    capsys.readouterr()

    payload = _write_json(tmp_path / "p.json", {"id": 3})
    rc = cli_main(["check", payload, "--against", contract_path])
    assert rc == 1  # strict -> missing email is drift
    assert "KeyMissing" in capsys.readouterr().out


def test_cli_missing_file_errors(tmp_path):
    contract_path = str(tmp_path / "contract.json")
    _write_json(tmp_path / "s1.json", {"id": 1})
    cli_main(["learn", str(tmp_path / "s1.json"), "-o", contract_path])
    with pytest.raises(SystemExit):
        cli_main(["check", "does_not_exist.json", "--against", contract_path])
