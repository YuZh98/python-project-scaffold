# Dev Notes

Reproduction + workaround records for library / framework gotchas discovered during development. Pinned by tests in `tests/` so the workaround doesn't regress.

## Capture-pin-comment workflow

When a library or framework behaves unexpectedly and you have to work around it:

1. **Reproduce** in isolation — strip the surprise to a minimal example you can paste into a comment or this file.
2. **Write up** as `docs/dev-notes/<short-slug>.md` with three sections: **Symptom** (what you saw), **Cause** (what's actually happening), **Workaround** (the code you wrote to handle it).
3. **Comment at the source site** — add a one-line `# see docs/dev-notes/<slug>.md` at the line in production code that implements the workaround.
4. **Pin with a test** — add an assertion in `tests/` that verifies the workaround still works. If the upstream library fixes the bug, the workaround can be removed and the test deleted.

## Why this workflow exists

Gotchas are expensive to learn and easy to forget. Six months later, someone (including you) will look at the workaround code and wonder why it exists. Steps 2-4 ensure the answer is one click away.

## File naming

`<lib-or-feature>-<short-symptom>.md`. Examples:
- `streamlit-session-state-on-rerun.md`
- `pandas-nan-truthy.md`
- `pytest-fixture-scope-confusion.md`

## Empty by default

This directory ships empty in new projects. Populate as you encounter and pin gotchas.
