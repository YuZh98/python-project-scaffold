# ADR-0000: Scaffold Foundational Choices

**Status:** Accepted
**Date:** <<YEAR>>-01-01
**Deciders:** <<AUTHOR_NAME>>

---

## Context

A new Python project needs structural decisions made before the first line of
business logic is written. Left implicit, these choices drift over time and
require expensive retrofits. This ADR documents the decisions baked into the
`python-project-scaffold` template so that every project that uses it starts
from an explicit, reasoned baseline rather than arbitrary defaults.

Deciding context: a single-developer or small-team Python application or
library, targeting Python <<PYTHON_FLOOR>>+, expected to grow to 5–20 modules
and 200–2 000 tests over its lifetime. The scaffold must be learnable in one
session and enforceable via CI without heroics.

Trigger criteria met:
- **Architectural** — affects every module, test, and CI step.
- **Hard to reverse** — switching src-layout after 50 modules costs a full
  refactor of imports and CI configuration.
- **Had alternatives** — flat layout, monorepo, no enforcement are all viable;
  the choice needed to be argued, not assumed.

---

## Decision

**D1 — Package layout: `src/` layout**

All importable package code lives under `src/<package_name>/`. Tests live at
`tests/` at the repo root, outside `src/`. The project is installed as an
editable package (`pip install -e .`) so imports always go through the installed
package, not the raw filesystem.

**D2 — Convention enforcement: pinning-test-driven**

Every rule in `GUIDELINES.md` that can be machine-checked gets a pinning test
in `tests/test_rules.py` before the rule-authoring PR merges. No rule lands as
prose-only. New rules that need a grace period ship as `@pytest.mark.xfail`
(bridge pattern) with a tracked follow-on PR.

**D3 — Commit format: Conventional Commits**

All commits use `<type>(<scope>): <subject>` format. Types: `feat`, `fix`,
`chore`, `docs`, `refactor`, `test`, `ci`. This enables automated CHANGELOG
generation and makes `git log --oneline` scannable.

**D4 — Changelog format: Keep-a-Changelog**

`CHANGELOG.md` uses the Keep-a-Changelog spec. An `[Unreleased]` section sits
at the top at all times. The six legal headings are: Added, Changed, Fixed,
Removed, Deprecated, Security. No free-form entries.

---

## Alternatives considered

**Flat layout (package at repo root)**
- Pro: simpler `sys.path`; no editable install required during development.
- Con: `import <package>` in tests resolves to the source directory, not the
  installed package — import-time bugs that only appear after packaging are
  silently missed. The `src/` layout forces an `editable install`, making test
  imports identical to production imports.
- Rejected: the false-confidence risk outweighs the setup simplicity.

**No pinning tests — rely on linters / code review only**
- Pro: zero test infrastructure cost upfront.
- Con: rules written only in prose drift within weeks. Code review catches some
  violations but not systematically. Linters (ruff, mypy) cover syntax and
  types but not project-specific structural rules (e.g. import contract layers,
  no `print()` in production code).
- Rejected: "no rule without enforcement" is a hard requirement for a scaffold
  intended to be used across multiple projects.

**Monorepo with multiple packages**
- Pro: easier cross-package refactoring; one CI pipeline.
- Con: workspace tooling (uv workspaces, hatch envs) adds surface area that
  distracts from the project's own domain. Multi-package dependency resolution
  errors are subtle.
- Rejected for scaffold default: a per-project single-package layout is the
  right starting point. Teams that need a monorepo already know it and can
  adapt.

**No commit convention (free-form messages)**
- Pro: no author friction.
- Con: `git log` becomes narrative noise; automated CHANGELOG generation is
  impossible; PR titles require manual categorisation.
- Rejected: Conventional Commits is low-overhead once it is a habit, and the
  payoff compounds.

**Changelog-as-code (generated from git log only)**
- Pro: zero manual maintenance.
- Con: generated changelogs include every chore/refactor commit, making
  user-facing release notes unreadable. Keep-a-Changelog requires curation
  but produces a document readable by non-engineers.
- Rejected: human curation is worth it for public-facing projects.

---

## Consequences

### Positive

- New contributors find the project structure immediately recognisable
  (src-layout is the Python Packaging Authority recommendation since 2020).
- Rule violations are caught in CI, not in code review — feedback loop is
  minutes, not days.
- CHANGELOG entries are consistently formatted; release notes can be
  extracted without parsing.
- Conventional Commits enable `git log --oneline --grep='^feat'` to list all
  feature commits instantly.

### Negative

- `src/` layout requires an editable install step (`pip install -e .`) that
  new contributors sometimes forget; the README must document this prominently.
- Pinning tests require authors to write a test *before* merging a new
  guideline, which adds 10–30 minutes per rule. This is intentional friction.
- Conventional Commits add a learning curve (~15 min) for authors new to the
  convention.

### Neutral

- Keep-a-Changelog's six headings occasionally feel constraining (e.g. "what
  type is a dependency bump?"). Convention: use `Changed` for dependency
  bumps unless the bump fixes a security issue (`Security`).
- The xfail-bridge pattern for aspirational rules means some tests pass
  vacuously until the follow-on PR lands. This is visible in the test output
  (`xpassed` / `xfailed`) and is intentional — see `TestImportContract`.

### Enforcement

| Decision | Enforced by |
|----------|-------------|
| D1 — src/ layout | `tests/test_cohesion.py::TestSrcLayoutPresent` (structural pinning test); src/ layout declared in `pyproject.toml [tool.setuptools.packages.find]` |
| D2 — pinning tests | GUIDELINES §8 convention + `tests/test_rules.py` itself (rules cannot land without a test) |
| D3 — Conventional Commits | pre-commit hook (`conventional-pre-commit` or equivalent); CI branch-name lint |
| D4 — Keep-a-Changelog | GUIDELINES §10 (every PR appends one line under `[Unreleased]` in `CHANGELOG.md`) |

---

## How to write ADR-0001

1. Copy this file to `docs/adr/ADR-0001-<short-slug>.md`.
2. Replace the content with your decision.
3. Update the `Status`, `Date`, `Deciders` header fields.
4. List the trigger criteria you met (architectural / hard-to-reverse / had-alternatives).
5. Always fill the **Enforcement** line (or table row) for each decision —
   point to a pinning test, a pre-commit hook, a GUIDELINES §N convention,
   or explicitly state "none — <reason>".
