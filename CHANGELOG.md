# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.2] - 2026-06-25

### Fixed
- Corrected project URLs to point at the real repository.
- Clarified author/maintainer metadata.

## [0.2.0] - 2026-06-25

### Added
- Command-line interface with `learn` and `check` subcommands. `check` returns
  a non-zero exit code on drift, making it usable as a CI gate.
- pytest plugin exposing `assert_no_drift()` for guarding test suites against
  API shape changes.
- Strict mode (`learn(strict=True)` / `--strict`) to mark every observed field
  as required.

## [0.1.0] - 2026-06-25

### Added
- Initial release.
- `learn()` to infer a structural contract from sample payloads.
- `Contract.check()` to detect drift in nested JSON / dict data.
- Detection of type changes, missing keys, new keys, and cardinality changes
  at any nesting depth.
- Lenient optional-field handling and nullable-awareness.
- Saveable / loadable JSON contracts.

[0.2.2]: https://github.com/amangupta982/contractguard/releases/tag/v0.2.2
[0.2.0]: https://github.com/amangupta982/contractguard/releases/tag/v0.2.0
[0.1.0]: https://github.com/amangupta982/contractguard/releases/tag/v0.1.0
