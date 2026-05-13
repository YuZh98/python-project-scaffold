# Contributing

Contributions to `python-project-scaffold` itself (NOT to projects scaffolded FROM it) welcome.

## What does belong here

- Bug fixes in `scripts/`, `template/`, `tests/`, `tooling/`.
- New rule promotions (e.g. moving a prose rule to a pinning test or pre-commit hook).
- Documentation improvements in `README.md`, `template/docs/`, or `CHANGELOG.md`.
- New integration subdirectories under `tooling/` (e.g. VS Code config, Cursor pack).

## What does NOT belong here

- Project-specific code that should live in a scaffolded project, not the scaffold itself.
- Speculative additions to `template/` without a clear use case.
- Removing rules without a deletion-rationale ADR.

## Dev setup

```bash
git clone https://github.com/YuZh98/python-project-scaffold.git
cd python-project-scaffold
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install pytest ruff pyright
```

The scaffold has no `requirements.txt` of its own — `tests/test_scaffold.py` and `tests/test_init_project.py` only need `pytest`.

## Running checks

```bash
ruff check .
ruff format --check .
pytest tests/ -v
```

CI runs the smoke test on every push + weekly. See `.github/workflows/ci.yml`.

## Branch + commit conventions

- Branch: `<type>/<short-description>` (e.g. `fix/scaffold-git-identity`, `docs/changelog-backfill`).
- Conventional Commits: `<type>(<scope>): <subject>`. Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`, `build`, `ci`, `schema`, `config`, `review`. Subject ≤ 72 chars, imperative mood.
- Add a one-line entry to `CHANGELOG.md` `[Unreleased]` under the relevant section.

## Pull requests

- Tests must pass. Branch protection requires `smoke` CI green + 1 review before merge.
- PR description: WHAT changed + WHY. No process narrative ("ran audit", "asked AI"); no `Co-Authored-By` trailers for AI assistants.

## License

By contributing, you agree your contributions are licensed under MIT (see `template/LICENSE`).
