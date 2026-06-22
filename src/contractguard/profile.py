"""Shape inference and contract profiling for nested JSON / dict data.

The core idea: walk one or more sample payloads, record the *structure*
(which keys exist, what type each value is, how deep it nests, whether a
field is consistently present), and freeze that into a reusable Contract.

This is deliberately about structure, not statistical distribution. We do
not care whether ``age`` is usually 30 vs 40 — we care whether ``age``
stops being an int, or disappears entirely.
"""

from __future__ import annotations

import json
from typing import Any


# Canonical type names we report. Keeping these stable matters because they
# show up in user-facing diffs and in saved contract files.
def type_name(value: Any) -> str:
    """Return a canonical, JSON-friendly type label for a Python value.

    ``bool`` is checked before ``int`` because in Python ``bool`` is a
    subclass of ``int`` and ``isinstance(True, int)`` is ``True`` — we do
    not want ``True`` reported as an int.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    # Fallback for anything exotic (e.g. a Decimal that slipped in).
    return type(value).__name__


class FieldShape:
    """The learned shape of a single field across all samples.

    Tracks every concrete type seen for this field, how many samples
    contained it (to decide optional vs required), and — for nested
    containers — the shapes underneath it.
    """

    __slots__ = ("types", "seen_count", "children", "item_shape")

    def __init__(self) -> None:
        # Set of type labels observed, e.g. {"int"} or {"int", "null"}.
        self.types: set[str] = set()
        # How many samples actually contained this field.
        self.seen_count: int = 0
        # For dict values: mapping of child key -> FieldShape.
        self.children: dict[str, FieldShape] = {}
        # For list values: a single merged FieldShape describing elements.
        self.item_shape: FieldShape | None = None

    def observe(self, value: Any) -> None:
        """Fold one observed value for this field into the shape."""
        self.seen_count += 1
        tname = type_name(value)
        self.types.add(tname)

        if tname == "dict":
            for key, child_value in value.items():
                child = self.children.get(key)
                if child is None:
                    child = FieldShape()
                    self.children[key] = child
                child.observe(child_value)
        elif tname == "list":
            if self.item_shape is None:
                self.item_shape = FieldShape()
            for element in value:
                self.item_shape.observe(element)

    def to_dict(self, total_samples: int, strict: bool = False) -> dict[str, Any]:
        """Serialize to a plain dict for saving as a contract.

        By default ``required`` is computed leniently: a field is required
        only if it appeared in every sample that reached its parent. Anything
        missing from some samples is recorded as optional, so we do not raise
        false alarms later.

        When ``strict`` is True, every field that was ever observed is marked
        required. Use this when your samples are known to be complete and you
        want any missing field to count as drift.
        """
        node: dict[str, Any] = {
            "types": sorted(self.types),
            "required": True if strict else self.seen_count >= total_samples,
        }
        if self.children:
            node["children"] = {
                key: child.to_dict(self.seen_count, strict=strict)
                for key, child in sorted(self.children.items())
            }
        if self.item_shape is not None:
            # List elements: "total" is the number of elements observed,
            # but we treat element presence leniently, so required is not
            # meaningful per-element. We still recurse to capture types.
            node["items"] = self.item_shape.to_dict(
                self.item_shape.seen_count, strict=strict
            )
        return node


class Contract:
    """A frozen, comparable description of a payload's structure.

    Build one with :func:`learn`, persist with :meth:`save`, reload with
    :meth:`load`, and compare new data against it with :meth:`check`.
    """

    def __init__(self, root: dict[str, Any]) -> None:
        # ``root`` is the serialized shape of the top-level value.
        self.root = root

    # -- persistence -------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {"contractguard_version": 1, "root": self.root}

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Contract":
        if "root" not in data:
            raise ValueError("Not a valid contractguard contract: missing 'root'.")
        return cls(data["root"])

    @classmethod
    def load(cls, path: str) -> "Contract":
        with open(path, encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    # -- comparison --------------------------------------------------------
    def check(self, payload: Any):
        """Compare a new payload against this contract.

        Returns a :class:`~contractguard.report.DriftReport`.
        """
        # Imported here to avoid a circular import at module load time.
        from .report import diff_against

        return diff_against(self.root, payload)


def learn(samples: list[Any], strict: bool = False) -> Contract:
    """Learn a :class:`Contract` from one or more sample payloads.

    Pass a list even if you only have one sample. The more representative
    samples you provide, the better optional-field detection works.

    Set ``strict=True`` to mark every observed field as required, so any
    missing field in later payloads is reported as drift. Leave it False
    (the default) for lenient learning that tolerates optional fields.
    """
    if not samples:
        raise ValueError("learn() needs at least one sample payload.")

    root_shape = FieldShape()
    for sample in samples:
        root_shape.observe(sample)

    return Contract(root_shape.to_dict(total_samples=len(samples), strict=strict))