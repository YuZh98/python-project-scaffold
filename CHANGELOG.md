# Changelog

Scaffold-repo evolution. The template's own CHANGELOG (`template/CHANGELOG.md`) is what new projects inherit; this file is for the scaffold itself.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · SemVer.

## [Unreleased]

### Added

### Changed

### Fixed

## [v1.0.0] - 2026-05-12

### Added
- Initial stable release.
- 23-file template tree (config, docs, src/, tests/) with placeholder-based substitution.
- `scripts/scaffold.sh` orchestrator: copy → substitute → git init → venv → install → pre-commit → pytest gate → first commit.
- `scripts/substitute.py` atomic placeholder substitution with manifest validation and path-traversal guard.
- `template.manifest.json` declaring 10 placeholders (9 required + 1 auto-derived).
- 5-rule pinning starter suite in `template/tests/test_rules.py`: no-print, no-secrets, type-hints-on-public-fns, no-mutable-default-args, import-contract placeholder.
- `template/tests/test_cohesion.py::TestSrcLayoutPresent` structural pinning test.
- Self-test CI (`.github/workflows/ci.yml`) running `tests/test_scaffold.py` end-to-end smoke test.
- Drift guard test (`tests/test_skill_flow.py`) — parses SKILL.md and asserts manifest parity.
- Worked-example ADR-0000 doubling as the template for ADR-0001.
- `[build-system]` block in `template/pyproject.toml` enabling editable installs.

### Notes
- Branch protection on `main` requires 1 review + passing `smoke` CI before merge.
- GitHub Actions pinned to SHAs (Dependabot tracks weekly).
