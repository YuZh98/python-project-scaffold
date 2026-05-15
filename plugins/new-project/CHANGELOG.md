# Changelog

All notable changes to the new-project plugin. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed
- `audit-runner` report template gains COMPACT and FULL modes selected by finding count — small diffs (≤2 findings, no blockers) emit only Verdict + Executive summary + Findings table. (dc8b1af)
- `audit-runner` docs dim CHANGELOG checklist trimmed to content-only checks, routing format concerns to `changelog-normalizer` and eliminating the apparent inconsistency when both skills run back-to-back. (73f2afa)
- `audit-runner` dimension checklists no longer cite v1.8.0-demoted rules as binding — ADR-for-architectural, Conventional Commits prefix list, and TDD cadence are now framed as recommendations matching the demotion. (2cba225)
- `audit-runner` SKILL.md "Recommended workflow when invoked manually" reduced to a pointer plus shell snippet, removing prose that duplicated `coordinator_brief.md` Steps 0-5. (2cba225)
- `audit-runner` coordinator brief Step 1 and Step 3 dispatch language reframed from "spawn sub-agents" to "focused pass, sub-agent dispatch where the runtime supports it" — matches SKILL.md's runtime-agnostic stance. (2cba225)
- `audit-runner` coordinator brief Step 6 cross-checks made mode-qualified after the COMPACT/FULL split — previously required N/A and blind-spot sections that COMPACT mode omits. (2cba225)
- `changelog-normalizer` workflow adds a fast-path that reports clean and stops for a conformant CHANGELOG, with ambiguity asks batched into a single round-trip on the non-clean path. (806b54f)
- `changelog-normalizer` SKILL.md Example A replaced with a before/after revision, enumerating the recurring drift patterns the skill exists to catch. (0ddcbba)
- `changelog-normalizer` SKILL.md Examples B and C strip the source-attribution prefix; the code blocks now stand alone as canonical patterns rather than excerpts. (37fd641)
- `new-project` SKILL.md compressed — execution-order comments no longer re-document `write_license.py` internals, meta-narration about doc structure dropped from intro and concrete-output sections. (d9a1668)
- `release-helper` SKILL.md trimmed by ~46 lines — design narration, self-justification framing, and verbose multi-sentence bullets removed. (06e6af0)
- `changelog-normalizer` SKILL.md consolidated after an independent evaluator scored the file Drift for teaching the same rules in four places; rule list lives only in Content rules now, with examples pointing at it. (3fbc10a)
- `audit-runner` SKILL.md trimmed by ~50 lines — ASCII pipeline diagram dropped, 8 of 12 meta-principle `*Why:*` lines cut as restating their bullet, "Recommended workflow when invoked manually" footer compressed to a pointer. (3b6c31d)
- `new-project` SKILL.md trimmed by ~23 lines — dry-run and refusal stubs removed (already shown inline in IO examples), Rust drift-example removed (already covered by Drift policy bullet). (e1e6f0b)

### Deprecated

### Removed

### Fixed

### Security

## [0.1.1] - 2026-05-14

Scope re-alignment: drops taste-pinning rules (imperative mood, ADR-for-decisions, summary-paragraph format), lowers the default coverage threshold to 80%, and repositions the README around what the scaffold pins versus what's configurable.

### Changed
- Default coverage threshold lowered from 95% to 80%, sourced from `pyproject.toml [tool.coverage.report] fail_under` as the single source of truth. (#22)
- Summary-paragraph-before-bullets rule in template CHANGELOG sections demoted from pinning test to recommendation in the comment block. (#22)
- Conventional Commits prescribed type list demoted from "must use these types" to "common examples". (#22)
- ADR-for-hard-to-reverse-decisions wording softened from "required" to "strongly recommended" across template docs. (#22)
- `changelog-normalizer` no longer rewrites past-tense verbs to imperative mood; voice is the author's choice. (#22)
- README repositioned with explicit "Universal rules enforced" and "What's left to your taste" sections so readers can see what the scaffold pins versus what's configurable. (#22)

### Removed
- Imperative-mood pinning test in `changelog-normalizer`. (#22)

### Security
- Internal-process docs (`docs/superpowers/`, `docs/dev-notes/`, session logs, agent briefs) added to `.gitignore` for both scaffold and template. (#21)
- `plugin-v0.1.0` tag scrubbed via `git filter-repo` to remove leaked `docs/superpowers/` paths from history; tag force-pushed and GitHub release recreated. (64e6db5)

## [0.1.0] - 2026-05-14

Initial plugin release. Packages four skills — `new-project`, `release-helper`, `changelog-normalizer`, `audit-runner` — distributed via a self-hosted marketplace.

### Added
- `new-project` skill scaffolds a fresh Python repo via natural-language invocation; thin orchestrator plus `scripts/*.sh` reduce per-invocation context load over the prior hand-written version. (64e6db5)
- `release-helper` skill automates the release sequence (rotate `[Unreleased]`, commit, annotated tag, push, version bump), composing `changelog-normalizer` as its pre-step. (64e6db5)
- `changelog-normalizer` skill normalizes `CHANGELOG.md` entries to Keep-a-Changelog style, strips process narrative, enforces subheading order, and refuses to fabricate refs. (64e6db5)
- `audit-runner` skill runs pre-PR audits across 11 dimensions with two-axis mode flags (scope + depth); coordinator walks 6 core dims and spawns on-demand sub-agents when diff triggers fire. (64e6db5)

[Unreleased]: https://github.com/YuZh98/python-project-scaffold/compare/plugin-v0.1.1...HEAD
[0.1.1]: https://github.com/YuZh98/python-project-scaffold/compare/plugin-v0.1.0...plugin-v0.1.1
[0.1.0]: https://github.com/YuZh98/python-project-scaffold/releases/tag/plugin-v0.1.0
