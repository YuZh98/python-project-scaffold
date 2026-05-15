# Contributing to <<PROJECT_TITLE>>

## Development Setup

```bash
git clone https://github.com/<<GITHUB_USERNAME>>/<<PROJECT_NAME>>.git
cd <<PROJECT_NAME>>
make install
```

## Running Checks

```bash
make test        # pytest + deprecation-strict pass
make lint        # ruff linting
make format      # apply ruff formatter to all .py files
make typecheck   # pyright type checking
make coverage    # pytest + coverage gate (default 80%, configurable in pyproject.toml)
```

## Submitting Changes

1. Fork the repo and create a feature branch: `git checkout -b feat/your-feature`
2. Write tests first (TDD: red → green → refactor).
3. Ensure checks pass: `make test && make lint && make typecheck`
4. Open a PR against `main` with a clear description of what changed and why.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## Code Style

- **Formatter / linter:** ruff (auto-applied on commit via pre-commit)
- **Type checker:** pyright (basic mode)
- Public functions must have type annotations on all parameters and return values
- No `print()` debug statements — use `logging` instead
- No mutable default arguments (use `None` + instantiate in body)

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `style:`, `perf:`, `build:`, `ci:`, `schema:`, `config:`, `review:`

Subject ≤ 72 characters; imperative mood; body explains the WHY when not obvious.
