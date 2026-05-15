# Changelog

All notable changes to the new-project plugin. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2026-05-14

### Added
- Scaffold a fresh Python repo via natural-language invocation. Refactored from the existing hand-written skill into a thin orchestrator plus `scripts/*.sh`; reduces context load per invocation. (4297435)
- Automate the release sequence (rotate `[Unreleased]`, commit, annotated tag, push, version bump). Composes the changelog-normalizer skill as a pre-step. (4297435)
- Normalize `CHANGELOG.md` entries to a consistent Keep-a-Changelog style. Strips process narrative, enforces subheading order, refuses to fabricate refs. (4297435)
- Run pre-PR audits using an 11-dimension framework with two-axis mode flags (scope + depth). Coordinator agent walks 6 core dims; on-demand sub-agents spawn for context-aware dims when surface triggers are detected in the diff. (4297435)

[Unreleased]: https://github.com/YuZh98/python-project-scaffold/compare/plugin-v0.1.0...HEAD
[0.1.0]: https://github.com/YuZh98/python-project-scaffold/releases/tag/plugin-v0.1.0
