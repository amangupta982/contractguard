"""pytest integration for contractguard.

Provides :func:`assert_no_drift`, a drop-in assertion for test suites that
consume external data. Point it at a frozen contract and a fresh payload;
if the payload's structure has drifted, the test fails with a readable
breakdown of exactly what changed.

Usage in a test::

    from contractguard.pytest_plugin import assert_no_drift

    def test_user_api_shape(httpx_response):
        assert_no_drift("contracts/user.json", httpx_response.json())

The contract argument may be a path to a saved contract file, a loaded
:class:`~contractguard.profile.Contract`, or a raw list of sample payloads
to learn from on the fly.
"""

from __future__ import annotations

from typing import Any, Union

from .profile import Contract, learn

ContractLike = Union[str, Contract, list]


def _resolve_contract(contract: ContractLike, strict: bool) -> Contract:
    """Coerce the various accepted contract inputs into a Contract."""
    if isinstance(contract, Contract):
        return contract
    if isinstance(contract, str):
        return Contract.load(contract)
    if isinstance(contract, list):
        return learn(contract, strict=strict)
    raise TypeError(
        "contract must be a file path, a Contract, or a list of samples; "
        f"got {type(contract).__name__}"
    )


def assert_no_drift(
    contract: ContractLike,
    payload: Any,
    *,
    strict: bool = False,
) -> None:
    """Assert that ``payload`` matches ``contract`` structurally.

    Raises ``AssertionError`` (which pytest renders nicely) listing every
    structural change if drift is found. Does nothing on a clean match.

    ``contract`` accepts a saved-contract file path, a Contract instance, or
    a list of sample payloads to learn from. ``strict`` only applies when
    learning from samples here.
    """
    resolved = _resolve_contract(contract, strict=strict)
    report = resolved.check(payload)
    if report.drifted:
        raise AssertionError(f"contractguard detected drift:\n{report}")
