# Changelog

All notable changes to the new-project plugin. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.1] - 2026-05-14

Scope re-alignment patch. Removes enforcement of taste-level rules so the plugin sticks to industry-universally-agreed conventions plus a small set of explicitly-chosen opinions. No runtime behavior changes outside the changelog normalizer's mood-rewrite path.

### Changed
- `changelog-normalizer` no longer rewrites past-tense verbs to imperative mood. Voice is your choice; structural validation (KaC vocabulary + order) and process-narrative detection are unchanged. (c735557)
- `README.md` repositioned: dropped beginner framing, added explicit "Universal rules enforced" and "What's left to your taste" sections so readers can see what the scaffold pins versus what's configurable. (439ca88)

### Removed
- Hardcoded 95% coverage threshold replaced with default 80% sourced from `pyproject.toml [tool.coverage.report] fail_under`. Makefile and CI now read from pyproject instead of hardcoding the value in three places. (8e21aec)
- Imperative-mood pinning test in `tests/skills/changelog_normalizer/`. (c735557)
- Summary-paragraph-before-bullets pinning test in `template/tests/test_cohesion.py`. Demoted to a recommendation in the template's `CHANGELOG.md` HTML comment. (9ba9eed)
- Conventional-commits prescribed type list (13 types) in `template/docs/concepts.md`. Demoted to "common examples". (8e21aec)
- ADR-for-hard-to-reverse-decisions wording changed from "required" to "strongly recommended" across template docs. (8e21aec)

### Security
- Internal-process docs (`docs/superpowers/`, `docs/dev-notes/`, session logs, agent briefs) added to `.gitignore` for both scaffold and template. (#21)
- `plugin-v0.1.0` tag scrubbed via `git filter-repo` to remove the leaked `docs/superpowers/` paths from its history; tag force-pushed and GitHub release recreated. (64e6db5)

## [0.1.0] - 2026-05-14

### Added
- Scaffold a fresh Python repo via natural-language invocation. Refactored from the existing hand-written skill into a thin orchestrator plus `scripts/*.sh`; reduces context load per invocation. (4297435)
- Automate the release sequence (rotate `[Unreleased]`, commit, annotated tag, push, version bump). Composes the changelog-normalizer skill as a pre-step. (4297435)
- Normalize `CHANGELOG.md` entries to a consistent Keep-a-Changelog style. Strips process narrative, enforces subheading order, refuses to fabricate refs. (4297435)
- Run pre-PR audits using an 11-dimension framework with two-axis mode flags (scope + depth). Coordinator agent walks 6 core dims; on-demand sub-agents spawn for context-aware dims when surface triggers are detected in the diff. (4297435)

[Unreleased]: https://github.com/YuZh98/python-project-scaffold/compare/plugin-v0.1.1...HEAD
[0.1.1]: https://github.com/YuZh98/python-project-scaffold/compare/plugin-v0.1.0...plugin-v0.1.1
[0.1.0]: https://github.com/YuZh98/python-project-scaffold/releases/tag/plugin-v0.1.0
