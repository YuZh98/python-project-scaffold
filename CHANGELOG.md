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

## [v1.7.1] - 2026-05-13

### Fixed
- `template/src/<<PACKAGE_NAME>>/__init__.py` single-line docstring overflows ruff E501 for non-trivial descriptions; changed to multi-line format. (#10)
- Skill Step 6: `gh repo create --push` defaults to SSH, failing for users without SSH keys configured; decoupled create and push, now pushes via HTTPS explicitly. (#10)

### Changed
- Skill Step 3 pre-clone summary table now shows the pinned scaffold version. (#10)
- Skill Step 5 error handler now includes a recovery path (delete and re-invoke, or complete manually with `make install`). (#10)
- `tests/test_scaffold.py` SAMPLE_VALUES description lengthened to realistic ~65 chars — ensures CI catches E501-class issues in the template. (#10)

## [v1.7.0] - 2026-05-13

### Fixed
- `scripts/scaffold.sh`: `<<PYTHON_FLOOR>>` read from values.json for floor assertion; missing parse caused assertion to silently pass with empty value. (#9)
- `scripts/scaffold.sh`: `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL`/`GIT_COMMITTER_*` env vars now exported before the first commit; bare CI runners with no global git identity no longer fail with exit 128. (#9)

### Added
- `tooling/claude-code/new-project.md`: skill now builds a full `values.json` and passes `--values` to `init-project.py --target`; eliminated double-prompt where script re-asked all fields despite `--yes`. (#9)
- `template/.pre-commit-config.yaml`: Conventional Commits 13-type canonical list enforced via `conventional-pre-commit` hook on commit-msg stage. (#9)
- `SECURITY.md`, `CONTRIBUTING.md`, `.github/pull_request_template.md` added for OSS hygiene. (#9)

### Changed
- `CHANGELOG.md`: backfilled entries for v1.3.0, v1.4.0, v1.5.0 which were shipped without changelog entries. (#9)

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

### Migration

Existing skill users (i.e. those who installed `~/.claude/skills/new-project/SKILL.md` from a prior scaffold release): the v1.6.0 release ships the same SKILL.md content as v1.5.0 with two stale-prose fixes (frontmatter "4 questions" → "3 questions"; tail comment "v1.4.0" → "v1.5.0"). To pick up the fixes and the v1.6.0 scaffold pin:

```bash
git clone --depth 1 --branch v1.6.0 https://github.com/YuZh98/python-project-scaffold.git /tmp/scaffold
cp /tmp/scaffold/tooling/claude-code/new-project.md ~/.claude/skills/new-project/SKILL.md
# Edit SCAFFOLD_VERSION in the installed file from v1.5.0 to v1.6.0 if you want the skill
# to clone the v1.6.0 scaffold release when invoked.
```

No breaking changes to the scaffold engine, template tree, or `init-project.py` interface in this release.

## [v1.5.0] - 2026-05-12

### Added
- `template/docs/setup-branch-protection.md`: 57-line how-to covering both `gh` CLI and GitHub UI paths, verification command, and three gotchas; cross-links to `template/docs/enforcement-model.md`. (#7)
- `template/tests/test_rules.py::TestNoStringConcatenatedSQL`: AST scan of `src/**/*.py` for `execute()`/`executemany()` calls whose SQL argument is built via f-string or `+` concatenation; vacuous-pass when no DB library is imported. Promotes GUIDELINES §5 "parameterised SQL only" from prose to Tier 1. (#7)

### Changed
- `template/.pre-commit-config.yaml`: add `default_install_hook_types: [pre-commit, commit-msg]` and `conventional-pre-commit` v3.6.0 hook on the `commit-msg` stage. Conventional Commits + ≤72 char subject now enforced mechanically (promoted from Tier 3 prose to Tier 2 pre-commit). (#7)
- `template/.github/pull_request_template.md`: add ADR-required checklist row prompting documentation for hard-to-reverse architectural decisions. (#7)
- `template/tests/test_cohesion.py`: add `TestChangelogFormat` asserting exactly one `## [Unreleased]` heading and that all `###` subsection headings are one of the six legal Keep-a-Changelog tokens. Promotes GUIDELINES §10 from prose to Tier 1. (#7)

### Fixed
- `template/README.md`: replace `<<AUTHOR_NAME>>` with `<<GITHUB_USERNAME>>` in both GitHub URL contexts — previous URLs included spaces from the user's display name, producing 404s and broken clone commands in every scaffolded project. (#7)
- `template/src/<<PACKAGE_NAME>>/__init__.py`: change docstring separator from `— X.` (em-dash + literal period) to `: X` (colon, no trailing punctuation) to avoid double-period when `<<DESCRIPTION>>` ends with `.`. (#7)
- `scripts/init-project.py` `_prompt()`: catch `EOFError` and abort cleanly with a message pointing at `--values <json>`. Non-TTY pipes (CI/scripted) no longer crash with an uncaught traceback. (#7)
- `scripts/init-project.py` `_derive_silent()`: every silent fallback (AUTHOR_NAME, AUTHOR_EMAIL, GITHUB_USERNAME) now prints an `ℹ` notice naming the resolved value and its source (git config / gh CLI). (#7)

## [v1.4.0] - 2026-05-12

### Added
- `scripts/init-project.py`: Python 3.11+ stdlib bootstrap CLI with tmpdir staging, atomic swap, and in-memory rollback on failure. Supports `--in-place` (default) and `--target <dir>` modes. (#6)
- Flags: `--values <json>` (non-interactive), `--dry-run`, `--keep-history`, `--reset-history`, `--no-install`, `--yes`. (#6)
- `tests/test_init_project.py`: smoke test for `--in-place` mode using `shutil.copytree` fork into tmpdir; asserts no stray placeholders, scaffold-only files removed, template files at root, and first commit present. (#6)
- `examples/values.example.json`: pre-filled placeholder values template for non-interactive bootstrap. (#6)
- `examples/README.md`: placeholder reference and derivation notes for direct-clone users. (#6)

### Changed
- Scaffold-repo `README.md` Quick Start reframed to three paths: Option A (`Use this template` + `init-project.py`), Option B (`git clone` + `init-project.py --target`), Option C (Claude Code skill — optional convenience). Demotes the Claude skill from primary path to opt-in callout. (#6)
- `template/CLAUDE.md`: gains "Optional file" header; marks the file as Claude Code-specific and safe to delete otherwise. (#6)
- `template/docs/enforcement-model.md`: Tier 2 reframes the Claude Code `rule-check-bash.sh` hook as an optional editor-specific addition rather than a primary enforcement mechanism. (#6)

## [v1.3.0] - 2026-05-12

### Added
- `template/docs/concepts.md`: 10-entry glossary covering venv, src layout, type hints, ruff, pyright, pre-commit, pytest fixtures, pinning tests, Conventional Commits, ADR, and Keep-a-Changelog + coverage gate. One short paragraph and canonical link per entry. (#5)
- `template/docs/enforcement-model.md`: four-tier rule-hierarchy reference (CI/tests → pre-commit → prose → memory) with worked example for CI failure diagnosis. (#5)
- `template/src/<<PACKAGE_NAME>>/example.py`: deletable hello-world with `greet()` function and `Greeter` dataclass demonstrating type hints, docstrings, and dataclass usage. Paired deletion header references `template/tests/test_example.py`. (#5)
- `template/tests/test_example.py`: `TestGreet` and `TestGreeter` covering 100% branch coverage so the 95% coverage gate stays green after scaffolding. (#5)

### Changed
- `template/README.md`: add callout linking `concepts.md` and `enforcement-model.md`; reorder Next Steps to lead with `make test` and end with "delete the example pair"; add collapsible `<details>` TDD walkthrough. (#5)
- `scripts/scaffold.sh`: add `pip install -e .` after dependency install and before pre-commit install and pytest gate, enabling `from <pkg> import …` in tests without manual pythonpath configuration. (#5)

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

### Security
- Branch protection on `main` requires 1 review + passing `smoke` CI before merge.
- GitHub Actions pinned to SHAs; Dependabot tracks weekly.
