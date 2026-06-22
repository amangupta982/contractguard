"""Command-line interface for contractguard.

Two subcommands:

  contractguard learn  sample1.json sample2.json -o contract.json [--strict]
  contractguard check  payload.json --against contract.json

``learn`` reads one or more JSON sample files, infers a contract, and writes
it to disk. ``check`` compares a payload against a saved contract and prints
any structural drift. ``check`` exits with status 1 when drift is found, so
it drops straight into CI pipelines and shell scripts.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import __version__
from .profile import Contract, learn


def _load_json(path: str) -> Any:
    """Read and parse a JSON file, exiting cleanly on common errors."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON ({exc})")


def _cmd_learn(args: argparse.Namespace) -> int:
    samples = [_load_json(path) for path in args.samples]
    contract = learn(samples, strict=args.strict)
    contract.save(args.output)
    mode = "strict" if args.strict else "lenient"
    print(
        f"Learned contract from {len(samples)} sample(s) ({mode}) "
        f"-> {args.output}"
    )
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    contract = Contract.load(args.against)
    payload = _load_json(args.payload)
    report = contract.check(payload)
    print(report)
    # Non-zero exit on drift makes this usable as a CI gate.
    return 1 if report.drifted else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contractguard",
        description="Structural drift detection for nested JSON / dict data.",
    )
    parser.add_argument(
        "--version", action="version", version=f"contractguard {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    learn_parser = sub.add_parser(
        "learn", help="Learn a contract from one or more JSON sample files."
    )
    learn_parser.add_argument(
        "samples", nargs="+", help="One or more JSON sample files."
    )
    learn_parser.add_argument(
        "-o",
        "--output",
        default="contract.json",
        help="Where to write the learned contract (default: contract.json).",
    )
    learn_parser.add_argument(
        "--strict",
        action="store_true",
        help="Mark every observed field as required.",
    )
    learn_parser.set_defaults(func=_cmd_learn)

    check_parser = sub.add_parser(
        "check", help="Check a JSON payload against a saved contract."
    )
    check_parser.add_argument("payload", help="JSON payload file to check.")
    check_parser.add_argument(
        "--against",
        required=True,
        help="Path to the saved contract file to check against.",
    )
    check_parser.set_defaults(func=_cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
