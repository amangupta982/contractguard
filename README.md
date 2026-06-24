# contractguard

[![PyPI version](https://img.shields.io/pypi/v/contractguard.svg)](https://pypi.org/project/contractguard/)
[![Python versions](https://img.shields.io/pypi/pyversions/contractguard.svg)](https://pypi.org/project/contractguard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-23%20passing-brightgreen.svg)](https://github.com/amangupta982/contractguard)
[![tests](https://github.com/amangupta982/contractguard/actions/workflows/tests.yml/badge.svg)](https://github.com/amangupta982/contractguard/actions/workflows/tests.yml)

**Structural drift detection for nested JSON / dict data.**

Learn the shape of your nested payloads from real samples, freeze it as a
contract, and catch breaking structural changes *before* they silently break
your code.

```python
import contractguard as cg

# 1. Learn the shape from known-good samples
contract = cg.learn([sample_a, sample_b, sample_c])
contract.save("api_contract.json")

# 2. Later: check new payloads against the frozen contract
report = contract.check(new_payload)
if report.drifted:
    print(report)
```

```text
3 change(s) detected:
  - TypeChanged: items[0].price  (float -> str)
  - TypeChanged: user.age  (int -> str)
  - NewKey: user.phone  (unexpected str)
```

---

## Why this exists

APIs and config files break silently. A backend renames a field, flips an
`int` to a `str`, drops a key, or turns a list into an object — your code
doesn't crash immediately, but something downstream quietly goes wrong, and
you lose an afternoon finding it.

`contractguard` learns the **structure** of your data from real examples and
tells you, in plain language, exactly what changed and where.

## Installation

```bash
pip install contractguard
```

No dependencies — pure Python standard library. Works on Python 3.8+.

## How it's different

| Tool | What it does | What contractguard does |
|------|--------------|-------------------------|
| **genson** | Infers a JSON schema from data | Infers it *and enforces it over time* |
| **data-drift-detector** | Statistical drift on flat dataframes | **Structural** drift on **nested** JSON |
| **pydantic / jsonschema** | You hand-write the schema | It **learns** the schema from real data |

The key gap it fills: every statistical drift tool assumes flat rows and
columns. `contractguard` walks arbitrarily nested dicts and lists, so it works
on real API payloads, event streams, and config files.

## Features

- **Zero dependencies** — pure standard library.
- **Nested-aware** — reports dotted paths like `user.address.zip`.
- **Lenient by default** — fields missing from some learning samples are
  treated as optional, so you don't get false alarms.
- **Nullable-aware** — if `null` was seen during learning, `null` is allowed.
- **No cascade noise** — a `list -> dict` change reports one root cause, not a
  flood of child errors.
- **Saveable contracts** — freeze a contract to JSON, commit it, check against
  it in CI.
- **CLI included** — use it without writing Python.
- **pytest plugin** — guard your test suite against API shape changes.

## Library usage

```python
import contractguard as cg

samples = [
    {"user": {"id": 1, "name": "ana", "email": "ana@x.com"}},
    {"user": {"id": 2, "name": "bob"}},
]

# Learn a contract (lenient: 'email' becomes optional since it's missing above)
contract = cg.learn(samples)

# Persist it
contract.save("user_contract.json")

# Later, check a fresh payload
report = contract.check({"user": {"id": 3, "name": "cleo", "age": "thirty"}})

print(report.drifted)   # True
print(report)           # human-readable breakdown
for change in report.changes:
    print(change.kind, change.path, change.detail)
```

## Command-line usage

`contractguard` ships a CLI, so you can use it without writing any Python:

```bash
# Learn a contract from sample payloads
contractguard learn sample1.json sample2.json -o contract.json

# Check a new payload against it
contractguard check payload.json --against contract.json
```

`check` exits with status `1` when drift is found and `0` when clean, so it
drops straight into CI pipelines:

```bash
contractguard check response.json --against contract.json || echo "API changed!"
```

Add `--strict` to `learn` to mark every observed field as required.

## pytest integration

Guard against API shape changes inside your own test suite:

```python
from contractguard import assert_no_drift

def test_user_endpoint_shape(client):
    response = client.get("/api/user/1").json()
    assert_no_drift("contracts/user.json", response)
```

If the response structure drifts, the test fails with a readable breakdown of
exactly what changed. The contract argument accepts a saved-contract path, a
`Contract` instance, or a list of sample payloads to learn from on the fly.

## What it detects

| Change kind | Meaning |
|-------------|---------|
| `TypeChanged` | A value's type changed (e.g. `int -> str`) |
| `KeyMissing` | A required key disappeared |
| `NewKey` | A key appeared that wasn't in the learned shape |
| `CardinalityChanged` | A list element's type changed, or a container's kind changed (`list -> dict`) |

## Strict vs lenient

By default, learning is **lenient**: a field missing from some samples is
treated as optional and won't trigger drift later. Pass `strict=True` (or
`--strict` on the CLI) to require every field that was ever observed:

```python
contract = cg.learn(samples, strict=True)
```

## Roadmap

- HTML / JSON report output
- GitHub Action for CI
- Configurable type coercion (e.g. treat `int` and `float` as compatible)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to
set up a dev environment and run the tests.

## License

MIT — see [LICENSE](LICENSE).

## Author

Built and maintained by [Aman Gupta](https://github.com/amangupta982).