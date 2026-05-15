# Dimension: conventions

**Tier:** CORE (always evaluated)

## Purpose

**Lint-tier mechanical, not judgment.** Catch what the formatter, linter, and type
checker *should* catch but might miss in the diff. Naming, type hints on public API,
debug-print scrubbing, magic numbers, GUIDELINES.md rule violations that are mechanical
in nature.

If you find yourself making judgment calls here, you're in `design`. Move the finding.

## Surface triggers

Not applicable — always evaluated.

## Checklist

1. **snake_case for functions, variables, modules.** Audit any added identifier. Class
   names are PascalCase; constants are UPPER_SNAKE.

2. **Type hints on public API.** Every public (non-`_`-prefixed) function/method has
   type hints on parameters and return value. Private helpers should have hints but
   not necessarily docstrings.

3. **No `print()` in committed code.** Use `logging`. The only exception is CLI entry
   points where `print` to stdout is the *interface*; flag everywhere else.

4. **No magic numbers in business logic.** Numeric literals other than `0`, `1`, `-1`
   in business logic are flags. Allowed in tests, in obvious constants (e.g. HTTP 200,
   port 8080 wrapped in a name), and in formatter-determined widths.

5. **Formatter clean.** Trailing whitespace, missing EOF newline, inconsistent
   indentation. (CI catches these; flag here only if the diff was committed without
   the formatter running — usually a CI gate misconfiguration.)

6. **GUIDELINES.md rule violations that are mechanical.** Examples:
   - "Parameterised SQL always" — flag `cursor.execute(f"SELECT ...")` or
     `.execute("..." % var)` or `.format()` in SQL strings.
   - "Validate input at boundaries" — flag write paths that don't reject
     whitespace-only required fields.
   - Commit-message prefix outside the project's documented type list (visible in
     `git log` of the diff). Treat as a minor unless the project explicitly pins
     the list as a hard rule.

7. **Imports.** Unused imports introduced by the diff. Wildcard imports. Import order
   if the project enforces one (isort, ruff-isort).

8. **Docstring presence on public API.** (Quality of docstring belongs in `docs`; this
   dim only checks presence and basic format.)

## Drift sweep

What in conventions's scope drifted from another source?

- `pyproject.toml` declares ruff rule X but a passing-CI file in the diff violates it
  (CI may be misconfigured or the diff may have bypassed pre-commit).
- `.pre-commit-config.yaml` references a hook the diff disabled inline with `# noqa`
  comments lacking a justification.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Unparameterised SQL with user input (overlaps with `security`). GUIDELINES rule with a passing pinning test, violated and committed. |
| major    | Multiple public functions missing type hints; `print()` left in non-CLI code; magic-number-rich business logic. |
| minor    | One missing type hint; one minor naming inconsistency; one magic number. |
| nit      | Trailing whitespace; import order quibble. |

## Common patterns

**Good.** Public API has full type hints and short docstrings. Constants live in a
config module. Logging via the project's standard logger.

**Bad.** A new public function with `def process(d, x=10):` (no hints, magic number,
single-letter param). Mixed-style imports. A `print("debug:", state)` left in source.
SQL strings built with `f"..."` over user input.
