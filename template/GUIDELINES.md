# Implementation Guidelines
_Read at the start of every coding session. Scannable checklist, not a tutorial._

**Version:** v0.1 | **Last updated:** <<YEAR>> | **Status:** draft

## 1. Environment
- Python <<PYTHON_FLOOR>>+; venv at `.venv/`; activate before coding.

## 2. Module Import Contract
- See `docs/adr/ADR-0001` (write it). Layered; one direction.

## 3. Naming Conventions
- PEP 8. snake_case fns/vars; UPPER_SNAKE_CASE constants; PascalCase classes.

## 4. Type Hints & Docstrings
- Public fns: hints + docstring. Private `_helpers`: hints, no docstring required.

## 5. Database / IO
- (fill in if applicable)

## 6. Config
- Single source of truth for constants/vocab. No hardcoded magic in business logic.

## 7. Error Handling
- User-facing: catch broadly, log, never re-raise. Non-UI: propagate.

## 8. Testing Conventions
- `tests/test_<module>.py`; class-level constants for copy/keys; pinning tests in `tests/test_rules.py`.
  - **No rule lands without its enforcement.** Every convention added to GUIDELINES.md needs a pinning test (or `xfail` bridge with a tracked follow-on PR) before the rule-authoring PR merges. Aspirational prose-only rules drift faster than they get enforced.
  - **Capture-pin-comment workflow** for newly discovered library/framework gotchas: (1) reproduce in isolation, (2) write up in `docs/dev-notes/<gotcha>.md` with Symptom/Cause/Workaround, (3) add a one-line comment at the source workaround site referencing the dev-note, (4) add a pinning test that locks in the fix.

## 9. Git Workflow
- Conventional Commits. `<type>/<short-description>` branches. Pre-commit + CI gates green.

## 10. CHANGELOG Discipline
- Keep-a-Changelog. `[Unreleased]` at top. Six section headings only: Added · Changed · Fixed · Removed · Deprecated · Security.
