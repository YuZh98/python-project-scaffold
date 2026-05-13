# Changelog

Scaffold-repo evolution. The template's own CHANGELOG (`template/CHANGELOG.md`) is what new projects inherit; this file is for the scaffold itself.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · SemVer.

## [Unreleased]

<!--
Keep-a-Changelog conventions (see GUIDELINES.md §10):
  - One change → one bullet, imperative mood (e.g. "Add foo").
  - Six legal section headings, in this order — omit empty ones before releasing:
    Added · Changed · Fixed · Removed · Deprecated · Security.
  - Add the PR number or commit hash at the end of each entry.
  - On release: rotate this block to ## [vX.Y.Z] - YYYY-MM-DD, then re-add empty [Unreleased] above.
-->

### Added

### Changed

### Fixed

## [v1.6.0] - 2026-05-12

### Added
- `tooling/` directory at scaffold-repo root — opt-in editor / AI-assistant integrations layer. Framework-neutral umbrella; scaffold engine (`scripts/`, `template/`) does not depend on anything here.
- `tooling/claude-code/new-project.md` — canonical in-repo copy of the Claude Code `/new-project` skill. Source of truth for the skill; users `cp` from here to `~/.claude/skills/new-project/SKILL.md`.
- `tooling/README.md` — explains the opt-in nature of the integrations layer and how to add new ones.

### Changed
- Scaffold-repo `README.md` Quick Start now lists Options A + B only (Use template + `git clone`). Claude Code skill moved to a standalone "Claude Code users (optional)" callout below "What you get" — opt-in framing.
- `README.md` "Claude Code users (optional)" section gains an explicit `mkdir + cp` install snippet pointing at `tooling/claude-code/new-project.md` with the v1.6.0 tag.

### Removed
- `tests/test_skill_flow.py` — obsolete drift guard. The skill was rewritten in v1.4.0 to delegate to `init-project.py` rather than duplicate its placeholder list; the `keys = [...]` block the test parsed no longer exists in SKILL.md. No drift surface remains for this test to guard.

## Migrating from v1.5.0

Existing skill users (i.e. those who installed `~/.claude/skills/new-project/SKILL.md` from a prior scaffold release): the v1.6.0 release ships the same SKILL.md content as v1.5.0 with two stale-prose fixes (frontmatter "4 questions" → "3 questions"; tail comment "v1.4.0" → "v1.5.0"). To pick up the fixes and the v1.6.0 scaffold pin:

```bash
git clone --depth 1 --branch v1.6.0 https://github.com/YuZh98/python-project-scaffold.git /tmp/scaffold
cp /tmp/scaffold/tooling/claude-code/new-project.md ~/.claude/skills/new-project/SKILL.md
# Edit SCAFFOLD_VERSION in the installed file from v1.5.0 to v1.6.0 if you want the skill
# to clone the v1.6.0 scaffold release when invoked.
```

No breaking changes to the scaffold engine, template tree, or `init-project.py` interface in this release.

## [v1.2.0] - 2026-05-12

### Added
- `template/SECURITY.md`: vulnerability reporting policy; uses `<<AUTHOR_EMAIL>>` placeholder.
- `template/CONTRIBUTING.md`: dev setup, check commands, commit conventions; uses project placeholders.
- `template/.github/ISSUE_TEMPLATE/bug_report.md` and `feature_request.md`: GitHub issue templates.
- `template/.github/pull_request_template.md`: PR checklist (test, lint, CHANGELOG, type-hints gate).
- `template/Makefile`: `make format` (ruff format), `make typecheck` (pyright), `make coverage` (pytest + 95% gate).

### Changed
- `template/Makefile`: `make lint` now runs ruff only; `make typecheck` is a separate target (mirrors CI step separation).
- `template/.pre-commit-config.yaml`: bump ruff pre-commit hook from v0.6.0 to v0.15.12.

## [v1.1.0] - 2026-05-12

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
