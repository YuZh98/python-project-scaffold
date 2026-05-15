# Concepts

Quick reference for concepts the scaffold uses. One paragraph each; click the link for depth. Not exhaustive — see [`enforcement-model.md`](enforcement-model.md) for how these concepts compose.

---

## venv (virtual environment)

A per-project Python install with its own dependencies. `python -m venv .venv` creates one in the current directory; `source .venv/bin/activate` enters it. Without a venv, `pip install` mutates the system Python — packages collide across projects and "works on my machine" becomes unfixable.

→ [Python docs: venv](https://docs.python.org/3/library/venv.html)

## src layout

Project source code lives in `src/<your-package>/` rather than at the repo root. The advantage: tests cannot import the package by accident from the working directory — they must use the installed copy, which is exactly what end users will get. Without `src/`, a half-broken install can still pass tests.

→ [pytest src layout discussion](https://docs.pytest.org/en/stable/explanation/goodpractices.html#choosing-a-test-layout-import-rules)

## Type hints

Annotations on function parameters and return values that declare expected types. `def add(a: int, b: int) -> int:` says both args and the return are ints. Hints have no runtime effect by themselves; tools like `pyright` check them at lint time.

→ [PEP 484](https://peps.python.org/pep-0484/)

## Static analysis (ruff + pyright)

Two complementary checkers that run without executing your code. `ruff` enforces formatting and lint rules (unused imports, line length, naming). `pyright basic` enforces type-hint correctness. Both run in CI; ruff also runs as a pre-commit hook with `--fix` so trivial issues are auto-corrected.

→ [ruff docs](https://docs.astral.sh/ruff/) · [pyright docs](https://microsoft.github.io/pyright/#/)

## Pre-commit hooks

Scripts that run automatically before `git commit` finalises. The scaffold ships hooks that run ruff (lint+autofix), trim trailing whitespace, fix end-of-file newlines, and reject merge-conflict markers and malformed YAML/TOML. A failing hook blocks the commit until you fix the issue or amend.

→ [pre-commit docs](https://pre-commit.com/)

## pytest fixtures

Reusable test setup defined with `@pytest.fixture`. A fixture function's return value is injected into any test that names it as a parameter. Fixtures replace `setUp`/`tearDown` from `unittest` and compose cleanly — small fixtures can depend on other fixtures.

→ [pytest fixtures docs](https://docs.pytest.org/en/stable/explanation/fixtures.html)

## Pinning tests

Tests that assert structural invariants about the code rather than functional behaviour — e.g. "no `print()` in production code", "every public function has type hints", "imports follow the layered contract". The scaffold ships five in `tests/test_rules.py` plus `tests/test_cohesion.py::TestSrcLayoutPresent`. Pinning tests catch drift that human review and ad-hoc lint rules miss.

→ This scaffold's [`tests/test_rules.py`](../tests/test_rules.py) — start there.

## Conventional Commits

A commit-message format some projects adopt: `<type>(<scope>): <subject>`. Common type values include `feat`, `fix`, `docs`, `chore`, `refactor`, `test` — pick whichever subset fits your project, or skip the prefix entirely. Subject ≤ 72 chars; voice is your choice. The format is useful when paired with automated changelog generation tools.

→ [Conventional Commits spec](https://www.conventionalcommits.org/)

## ADR (Architectural Decision Record)

A short markdown document recording a hard-to-reverse architectural choice: context, decision, alternatives considered, consequences, enforcement. Strongly recommended (not mechanically enforced) when (a) the decision is architectural, (b) it would be expensive to undo, (c) at least one alternative was viable. The scaffold ships `docs/adr/ADR-0000-scaffold-choices.md` as a worked example you can copy.

→ [Michael Nygard's original ADR essay](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

## Keep-a-Changelog + coverage gate

`CHANGELOG.md` follows a fixed format: latest version at top, `[Unreleased]` collects in-progress work, six legal subsection headings (`Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`, in Keep-a-Changelog 1.1.0 order). Coverage gate: the CI fails if `pytest --cov` reports below the threshold configured in `pyproject.toml` `[tool.coverage.report] fail_under` (default 80%). Together they make every release auditable and force tests for new code.

→ [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [pytest-cov](https://pytest-cov.readthedocs.io/)
