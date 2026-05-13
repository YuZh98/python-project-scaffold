# <<PROJECT_TITLE>>

<<DESCRIPTION>>

## Status

Early development. Scaffolded from [python-project-scaffold](https://github.com/<<AUTHOR_NAME>>/python-project-scaffold).

> **New to these concepts?** See [`docs/concepts.md`](docs/concepts.md) for a glossary of every scaffold-shipped term (venv, src layout, pinning tests, ADRs, etc.). For the architecture of how these concepts compose, see [`docs/enforcement-model.md`](docs/enforcement-model.md).

## Quick start

```bash
git clone https://github.com/<<AUTHOR_NAME>>/<<PROJECT_NAME>>.git
cd <<PROJECT_NAME>>
make install
make test
```

### Development

Run `make lint` before committing. The repo enforces ruff, pyright (basic), and pinning tests (see `tests/test_rules.py`). Pre-commit hooks installed by `make install` block obvious mistakes: ruff lint+autofix, trailing whitespace, missing EOF newline, malformed YAML/TOML, and merge-conflict markers.

## Documentation

- [Design](DESIGN.md) — architecture
- [Guidelines](GUIDELINES.md) — coding conventions
- [Changelog](CHANGELOG.md)

## Next steps

After `make install`:

1. Run `make test` — confirm everything is green from minute zero.
2. Read [`src/<your-package>/example.py`](src/) and [`tests/test_example.py`](tests/) — the paired hello-world demonstrating idiomatic patterns the pinning tests enforce.
3. Replace the example with your first real module (see the TDD walkthrough below).
4. Write `docs/adr/ADR-0001-import-contract.md` for your first architectural decision. Use [`docs/adr/ADR-0000-scaffold-choices.md`](docs/adr/ADR-0000-scaffold-choices.md) as the worked-example template.
5. **Delete `src/<your-package>/example.py` and `tests/test_example.py` together** once your first real module + test pair lands.
6. Add one line to `CHANGELOG.md` under `[Unreleased]` for any user-observable change.

<details>
<summary><strong>Your first feature — TDD walkthrough</strong> (click to expand)</summary>

The scaffold ships test-first patterns. For a beginner-friendly first feature:

1. **Write a failing test first.** Add a new test class to `tests/test_example.py` (or replace it). Example:
   ```python
   class TestMyFeature:
       def test_does_the_thing(self) -> None:
           from <your-package>.my_feature import do_the_thing
           assert do_the_thing(2) == 4
   ```
   Run `make test` — it MUST be red (`ImportError` or `AssertionError`).

2. **Write the minimum code to make it green.** Create `src/<your-package>/my_feature.py`:
   ```python
   def do_the_thing(x: int) -> int:
       return x * 2
   ```
   Run `make test` — it should pass.

3. **Commit.** `git add`, `git commit -m "feat: add my_feature.do_the_thing"`. The pre-commit hook will auto-format your code; if it modifies anything, `git add` again and re-commit.

4. **Iterate.** Add the next test, watch it fail, write code, watch it pass.

When you have your own first module + test pair, **delete `example.py` and `test_example.py` together** (deleting only one leaves an unresolved import in the test suite).

</details>

## License

<<LICENSE_ID>> — see [LICENSE](LICENSE).
