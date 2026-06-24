# Contributing to contractguard

Thanks for your interest in contributing! This guide covers how to get set up
and what's expected.

## Development setup

Clone the repo and create a virtual environment:

```bash
git clone https://github.com/amangupta982/contractguard.git
cd contractguard
python3 -m venv env
source env/bin/activate          # Windows: env\Scripts\activate
pip install -e ".[dev]"
```

## Running the tests

```bash
python3 -m pytest -v
```

All tests should pass before you open a pull request. The suite covers the
core engine, strict mode, the pytest plugin, and the CLI.

## Project layout

```
src/contractguard/
  __init__.py        public API
  profile.py         shape inference + Contract
  report.py          diff engine + DriftReport
  pytest_plugin.py   assert_no_drift helper
  cli.py             command-line interface
tests/
  test_contractguard.py   core engine tests
  test_features.py        strict mode, plugin, CLI tests
```

## Guidelines

- Keep the library dependency-free (standard library only).
- Add tests for any new behavior.
- Match the existing code style (clear names, docstrings on public functions).
- Update the README and CHANGELOG if your change is user-facing.

## Reporting bugs

Open an issue with a minimal reproduction: the samples you learned from, the
payload you checked, what you expected, and what you got. The more concrete,
the faster it can be fixed.
