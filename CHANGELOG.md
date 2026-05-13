# Changelog

Scaffold-repo evolution. The template's own CHANGELOG (`template/CHANGELOG.md`) is what new projects inherit; this file is for the scaffold itself.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · SemVer.

## [Unreleased]

### Added
- `<<GITHUB_USERNAME>>` placeholder (10th required). `template/pyproject.toml [project.urls]` now uses the GitHub login instead of `<<AUTHOR_NAME>>`. Manifest now 10 required + 1 auto-derived (was 9 + 1).
- `.scaffold-version` provenance file written into every scaffolded repo at commit 1 (`manifest_version` + `scaffold_sha` + `scaffolded_at`).
- SIGINT/SIGTERM cleanup trap in `scripts/scaffold.sh` — partial `$TARGET` is removed if interrupted before first commit; left in place if work exists.
- Scaffold-repo root `README.md` (this repo's GitHub landing page previously showed only file listings).
- Weekly scheduled CI run on scaffold repo (`cron: '0 9 * * 1'`) — catches environmental drift even when no commits land.
- `template/docs/dev-notes/README.md` documenting the capture-pin-comment workflow.
- `template/CLAUDE.md` four-layer rule-enforcement model section.
- `template/CHANGELOG.md` inline Keep-a-Changelog conventions comment + empty `Added/Changed/Fixed` subsection scaffolds.

### Changed
- `<<PYTHON_FLOOR>>` / `<<RUFF_TARGET>>` validate regex opened to 3.11–3.99 / py311–py3xx. No more annual edit when 3.15+ ships.
- `template/requirements-dev.txt` adds upper-bound guards (`<2`, `<10`, `<8`, `<6`) so silent major-version bumps land as review PRs.
- `scripts/scaffold.sh` commit message reads `MANIFEST_VERSION` from the manifest (no more hardcoded `v1`).
- `~/.claude/skills/new-project/SKILL.md`: surface `ACTIVE_GH_LOGIN` + confirmation prompt before push; replace raw-regex error on project name with human-readable message; license options gain one-line parentheticals; pass `<<GITHUB_USERNAME>>` as 10th value.

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
