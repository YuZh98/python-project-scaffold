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

## 9. Git Workflow
- Conventional Commits. `<type>/<short-description>` branches. Pre-commit + CI gates green.

## 10. CHANGELOG Discipline
- Keep-a-Changelog. `[Unreleased]` at top. Six section headings only: Added · Changed · Fixed · Removed · Deprecated · Security.
