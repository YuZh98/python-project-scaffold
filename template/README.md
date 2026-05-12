# <<PROJECT_TITLE>>

<<DESCRIPTION>>

## Status

Early development. Scaffolded from [python-project-scaffold](https://github.com/<<AUTHOR_NAME>>/python-project-scaffold).

## Quick start

```bash
git clone https://github.com/<<AUTHOR_NAME>>/<<PROJECT_NAME>>.git
cd <<PROJECT_NAME>>
make install
make test
```

### Development

Run `make lint` before committing. The repo enforces ruff, pyright (basic), and pinning tests (see `tests/test_rules.py`). Pre-commit hooks installed by `make install` block obvious mistakes (formatting drift, AI-attribution trailers, secrets, status literals).

## Documentation

- [Design](DESIGN.md) — architecture
- [Guidelines](GUIDELINES.md) — coding conventions
- [Changelog](CHANGELOG.md)

## Next steps

After `make install && make test` is green:

1. Write `docs/adr/ADR-0001-import-contract.md` — your first architectural decision. (See the worked example at `docs/adr/ADR-0000-scaffold-choices.md`.)
2. Rename `src/<<package_name>>` to your actual package name (the scaffold tooling already did this if you used the `/new-project` skill).
3. Fill in `DESIGN.md` — Problem / Solution / Non-goals. The placeholders show the kind of content expected.
4. Run `make lint` to check ruff + pyright.
5. Open your first real issue or write the first feature test in `tests/`.

## License

<<LICENSE_ID>> — see [LICENSE](LICENSE).
