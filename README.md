# python-project-scaffold

A Python project scaffold with mature rule-guarding wired from commit 1. Fork or clone, run one command, get a green-CI project ready for your first feature.

## Why use this

Starting a new Python project well takes ~30 minutes of repetitive setup: venv, ruff, pyright, pytest, coverage, pre-commit hooks, GitHub Actions matrix, dependabot, issue templates, CHANGELOG scaffolding, ADR ledger, type-hint discipline, src layout. Get it wrong and you spend the first week of every project hunting drift instead of writing code. This scaffold ships every convention pre-wired so you start at "first feature" instead of "first config."

## What this is

A Python scaffold + Claude Code plugin for developers who want a well-structured, well-rule-guarded baseline from commit 1, plus AI helpers that automate lifecycle steps (scaffold a new project, normalize CHANGELOG, run releases, audit pre-PR diffs).

The scaffold ships with the conventions the SE discipline broadly agrees on, wired up from commit 1 — tests, CI, CHANGELOG, ADRs, type hints, pre-commit hooks. The plugin layers on AI-assisted helpers for the steps you do repeatedly.

This is not a tutorial. It assumes you already know Python and SE practices and want a working example to start from rather than configuring from scratch. Pair it with [`docs/concepts.md`](template/docs/concepts.md) (glossary) and [`docs/enforcement-model.md`](template/docs/enforcement-model.md) (architecture) inside any scaffolded project.

## Universal rules enforced from day 1

Non-negotiable hygiene/safety rules the scaffold pins via tests, hooks, and CI:

| Rule | Why |
|---|---|
| No `print()` in production code | Use `logging` — `print()` pollutes stdout and indicates leftover debug. |
| No secrets in repo | Pattern scan for API keys, AWS access IDs, OpenAI-style keys, bearer tokens. |
| Type hints on public functions | Self-documenting API; catches signature mistakes at type-check time. |
| No mutable default args | Python language gotcha — shared state across calls. |
| Parameterized SQL only | SQL injection is a bad habit even in personal tools. |
| `src/` layout exists | Structural — many downstream pinning tests assume this layout. |
| Keep-a-Changelog structural format | `[Unreleased]` section; subheadings drawn from the KaC vocabulary (`Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`, in 1.1.0 spec order). Voice and tone are your choice. |
| Pre-commit hooks | Formatting, EOF newline, merge-conflict markers, YAML/TOML validity — all configured. |
| CI matrix across `requires-python` | Every supported runtime gets exercised. |
| Linter + formatter + type checker + test runner + coverage gate exist | Tools wired into CI from commit 1. The specific values (coverage %, line length, etc.) are configurable. |

These rules are pinned by `tests/test_rules.py` and `tests/test_cohesion.py` and run on every commit.

## What's left to your taste

These have sensible defaults but no mechanical enforcement — change without forking:

| Default | How to change |
|---|---|
| Coverage threshold = 80% | Edit `[tool.coverage.report] fail_under` in `pyproject.toml`. |
| Conventional-commit prefixes (suggested) | Use them, skip them, or pick a different convention — the scaffold doesn't lint commit messages. |
| CHANGELOG entry voice (recommended: describe WHAT changed and WHY it matters) | Document your project's preferred voice in your `CONTRIBUTING.md`. The plugin's `changelog-normalizer` validates structure but doesn't rewrite voice. |
| Summary paragraph before bullets in CHANGELOG versions | Recommended for top-down readability, not enforced. |
| ADR for hard-to-reverse architectural decisions | Strongly recommended — `docs/adr/` template included. Not mechanically enforced. |
| Bullet glyph (`-` vs `*`) | Pick one and be consistent within your project. |
| Line wrap width, prose style, etc. | Pick what fits your project. |

The plugin (separately versioned in `plugins/new-project/`) layers on more opinionated tooling — see its `README.md` for what it adds and how to override.

## Quick start

### Option A — GitHub "Use this template" (recommended for new repos)

1. Click **"Use this template"** at the top of [this repo on GitHub](https://github.com/YuZh98/python-project-scaffold) → create a new repo under your account.
2. Clone the new repo locally.
3. Run the interactive bootstrap:
   ```bash
   python3 scripts/init-project.py
   ```
   You'll be asked for project name, description, license, Python floor. Everything else (package name, year, author, GitHub username) is auto-derived from `git config` and `gh` CLI. The script stages the substituted tree to a tmpdir, atomically swaps it to the repo root, removes scaffold-only files, optionally resets git history, and makes the first commit.
4. Run `make test` to confirm the green CI baseline.

The `init-project.py` script supports `--dry-run` (preview without writing), `--values <path.json>` (non-interactive), `--keep-history` (preserve scaffold commits), and `--no-install` (skip `make install`).

### Option B — Clone + scaffold to a separate directory

If you prefer to keep the scaffold and the project in separate trees:

```bash
git clone --depth 1 --branch v1.7.0 https://github.com/YuZh98/python-project-scaffold.git /tmp/scaffold
python3 /tmp/scaffold/scripts/init-project.py --target /path/to/new-project
```

This copies the substituted template to `/path/to/new-project` and leaves the scaffold checkout untouched.

## What you get

A new project bootstrapped from this scaffold ships with, on day 0:

- **CI**: ruff + pyright (basic) + pytest + deprecation-strict pass + coverage gate (default 80%, configurable in `pyproject.toml`) across Python 3.11–3.14.
- **Pre-commit hooks**: ruff (lint + autofix), trailing whitespace, EOF newline, YAML/TOML validity, merge-conflict markers.
- **Pinning tests** (`tests/test_rules.py`): no `print()` debug, no secrets in tree, public functions have type hints, no mutable default args, import-contract placeholder.
- **Documentation scaffolds**: `README.md`, `DESIGN.md`, `GUIDELINES.md`, `CHANGELOG.md` (Keep-a-Changelog), `docs/concepts.md` (glossary), `docs/enforcement-model.md` (4-tier rule architecture), `docs/adr/` ledger with a worked-example ADR-0000.
- **Hello-world example**: `src/<your-package>/example.py` + `tests/test_example.py` paired demonstration. Delete both when you write your first real module.
- **Dependabot** for `pip` + `github-actions` (weekly, grouped minor/patch).
- **OSS hygiene**: LICENSE (MIT default), SECURITY.md, CONTRIBUTING.md, issue + PR templates.

## Claude Code plugin

If you use [Claude Code](https://claude.com/claude-code), install the new-project plugin to get a 4-question UX with automatic GitHub repo creation and branch protection on top of the scaffold's own bootstrap. The plugin also ships sibling skills for releases, changelog normalization, and pre-PR audits.

```bash
/plugin marketplace add YuZh98/python-project-scaffold
/plugin install new-project@python-project-scaffold
```

See `plugins/new-project/README.md` for details.

## Placeholders

10 placeholders, listed in `template.manifest.json`. Required: project name, title, package name, description, author name + email, year, license id, GitHub username, Python floor. Auto-derived: ruff target (from Python floor).

## Versioning

This scaffold uses release tags (`v1.0.0`, `v1.1.0`, ...). Pin your clone or skill to a specific tag — never use latest `main`. See [CHANGELOG.md](CHANGELOG.md) for what each release changed.

## Maintenance

| Concern | Approach |
|---------|----------|
| Python version coverage | CI matrix hardcoded `3.11`–`3.14`. When 3.15+ ships, manually add to matrix + bump scaffold version. Manifest regex is open-ended; the matrix is the only hardcoded list. |
| Action SHA pins | Dependabot tracks `github-actions` weekly. |
| Pre-commit hook versions | Manual `pre-commit autoupdate` quarterly. |
| Pinning test rules | New universal rules land in this repo, then propagate to new projects only. Existing scaffolded projects sync manually. |

## License

MIT — see [LICENSE](LICENSE).

## See also

- [`template.manifest.json`](template.manifest.json) — placeholder registry
- [`scripts/init-project.py`](scripts/init-project.py) — interactive bootstrap (primary entry point)
- [`scripts/scaffold.sh`](scripts/scaffold.sh) — non-interactive target-dir orchestrator (used by CI + skill)
- [`scripts/substitute.py`](scripts/substitute.py) — substitution engine
- [`tests/test_init_project.py`](tests/test_init_project.py) — smoke test for the bootstrap flow
- [`tests/test_scaffold.py`](tests/test_scaffold.py) — smoke test for the target-dir flow
- [`tooling/`](tooling/) — opt-in editor / AI-assistant integrations (e.g. Claude Code skill)
