# contractguard

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

```
3 change(s) detected:
  - TypeChanged: items[0].price  (float -> str)
  - TypeChanged: user.age  (int -> str)
  - NewKey: user.phone  (unexpected str)
```

## Why this exists

APIs and config files break silently. A backend renames a field, flips an
`int` to a `str`, drops a key, or turns a list into an object — your code
doesn't crash immediately, but something downstream quietly goes wrong, and
you lose an afternoon finding it.

`contractguard` learns the **structure** of your data from real examples and
tells you, in plain language, exactly what changed and where.

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

## Install

```bash
pip install contractguard
```

## What it detects

- `TypeChanged` — a value's type changed (`int -> str`)
- `KeyMissing` — a required key disappeared
- `NewKey` — a key appeared that wasn't in the learned shape
- `CardinalityChanged` — a list element's type changed, or a container's kind
  changed (`list -> dict`)

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

## License

MIT