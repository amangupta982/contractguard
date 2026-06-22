"""Comparing a payload against a learned contract and reporting drift.

The diff walks the contract and the new payload in lockstep, emitting a
flat list of :class:`Change` objects. Each change carries a dotted path
(e.g. ``user.address.zip``) so a human can locate the problem instantly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .profile import type_name


# Kinds of structural drift we detect. Strings, not an enum, so that saved
# reports and printed output stay trivially readable.
TYPE_CHANGED = "TypeChanged"
KEY_MISSING = "KeyMissing"
NEW_KEY = "NewKey"
CARDINALITY_CHANGED = "CardinalityChanged"


@dataclass
class Change:
    """A single structural difference at a specific path."""

    kind: str
    path: str
    detail: str

    def __str__(self) -> str:
        location = self.path or "<root>"
        return f"{self.kind}: {location}  ({self.detail})"


@dataclass
class DriftReport:
    """The result of checking a payload against a contract."""

    changes: list[Change] = field(default_factory=list)

    @property
    def drifted(self) -> bool:
        return bool(self.changes)

    def __bool__(self) -> bool:
        # Truthy when there IS drift, so ``if report:`` reads naturally.
        return self.drifted

    def __str__(self) -> str:
        if not self.changes:
            return "No drift detected."
        lines = [f"{len(self.changes)} change(s) detected:"]
        lines.extend(f"  - {change}" for change in self.changes)
        return "\n".join(lines)

    def by_kind(self, kind: str) -> list[Change]:
        """Return only the changes of a given kind."""
        return [change for change in self.changes if change.kind == kind]


def _join(prefix: str, key: str) -> str:
    return f"{prefix}.{key}" if prefix else key


def _node_types(node: dict[str, Any]) -> set[str]:
    return set(node.get("types", []))


def diff_against(contract_node: dict[str, Any], value: Any, path: str = "") -> DriftReport:
    """Diff a payload value against a contract node, recursively."""
    report = DriftReport()
    _walk(contract_node, value, path, report)
    return report


def _walk(node: dict[str, Any], value: Any, path: str, report: DriftReport) -> None:
    expected_types = _node_types(node)
    actual_type = type_name(value)

    # A contract that allowed null here means the field is genuinely
    # nullable; seeing null is not drift in that case.
    if actual_type not in expected_types:
        report.changes.append(
            Change(
                kind=TYPE_CHANGED,
                path=path,
                detail=f"{' | '.join(sorted(expected_types))} -> {actual_type}",
            )
        )
        # If the top-level kind changed (e.g. dict -> list), recursing into
        # children would produce a cascade of confusing sub-changes. Report
        # the single root cause and stop descending here.
        return

    if actual_type == "dict":
        _walk_dict(node, value, path, report)
    elif actual_type == "list":
        _walk_list(node, value, path, report)


def _walk_dict(node: dict[str, Any], value: dict, path: str, report: DriftReport) -> None:
    children: dict[str, Any] = node.get("children", {})

    # Missing keys: in the contract (and required) but absent from payload.
    for key, child_node in children.items():
        child_path = _join(path, key)
        if key in value:
            _walk(child_node, value[key], child_path, report)
        elif child_node.get("required", False):
            report.changes.append(
                Change(
                    kind=KEY_MISSING,
                    path=child_path,
                    detail=f"expected {' | '.join(child_node.get('types', []))}",
                )
            )
        # Optional + absent => no drift. This is the lenient default.

    # New keys: in the payload but never seen during learning.
    for key in value:
        if key not in children:
            child_path = _join(path, key)
            report.changes.append(
                Change(
                    kind=NEW_KEY,
                    path=child_path,
                    detail=f"unexpected {type_name(value[key])}",
                )
            )


def _walk_list(node: dict[str, Any], value: list, path: str, report: DriftReport) -> None:
    item_node = node.get("items")
    if item_node is None:
        # Contract saw only empty lists here; we cannot judge element shape.
        return

    item_types = set(item_node.get("types", []))
    for index, element in enumerate(value):
        element_path = f"{path}[{index}]"
        element_type = type_name(element)
        if element_type not in item_types:
            report.changes.append(
                Change(
                    kind=CARDINALITY_CHANGED,
                    path=element_path,
                    detail=f"element {' | '.join(sorted(item_types))} -> {element_type}",
                )
            )
            continue
        if element_type in ("dict", "list"):
            _walk(item_node, element, element_path, report)
