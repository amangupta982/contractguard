"""contractguard — structural drift detection for nested JSON / dict data.

Learn the shape of your nested payloads from real samples, freeze it as a
contract, and get readable structural diffs when new data drifts.

Quick start::

    import contractguard as cg

    contract = cg.learn([sample_a, sample_b, sample_c])
    contract.save("api_contract.json")

    report = contract.check(new_payload)
    if report.drifted:
        print(report)

Unlike statistical drift tools (which target flat dataframes), contractguard
cares about *structure*: a field changing type, disappearing, appearing, or a
container changing kind — at any nesting depth.
"""

from .profile import Contract, learn
from .pytest_plugin import assert_no_drift
from .report import (
    CARDINALITY_CHANGED,
    KEY_MISSING,
    NEW_KEY,
    TYPE_CHANGED,
    Change,
    DriftReport,
)

__all__ = [
    "learn",
    "Contract",
    "DriftReport",
    "Change",
    "assert_no_drift",
    "TYPE_CHANGED",
    "KEY_MISSING",
    "NEW_KEY",
    "CARDINALITY_CHANGED",
]

__version__ = "0.2.1"