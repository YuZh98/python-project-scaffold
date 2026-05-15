# python-project-scaffold

A Python project scaffold with mature rule-guarding wired from commit 1. Fork or clone, run one command, get a green-CI project ready for your first feature.

## Why use this

Starting a new Python project well takes ~30 minutes of repetitive setup: venv, ruff, pyright, pytest, coverage, pre-commit hooks, GitHub Actions matrix, dependabot, issue templates, CHANGELOG scaffolding, ADR ledger, type-hint discipline, src layout. Get it wrong and you spend the first week of every project hunting drift instead of writing code. This scaffold ships every convention pre-wired so you start at "first feature" instead of "first config."

## Who is this for

**Beginners** picking up software engineering practices on a real project. The scaffold ships every convention the discipline expects (tests, type hints, CHANGELOG, ADRs) wired up from commit 1, so you learn by editing a working example rather than configuring from scratch. Pair this with [`docs/concepts.md`](template/docs/concepts.md) (glossary) and [`docs/enforcement-model.md`](template/docs/enforcement-model.md) (architecture) inside any scaffolded project.

**Experienced devs** starting a new project. Skip ~30 minutes of repetitive setup. Pin to a release tag (`v1.3.0`+), customize four values, get a green-CI repo ready for the first feature commit. The opinionated defaults (Python 3.11+, src/ layout, ruff + pyright basic, pytest, pre-commit, 95% coverage) are designed to be a sensible baseline you rarely need to touch.

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

- **CI**: ruff + pyright (basic) + pytest + deprecation-strict pass + coverage gate (95%) across Python 3.11–3.14.
- **Pre-commit hooks**: ruff (lint + autofix), trailing whitespace, EOF newline, YAML/TOML validity, merge-conflict markers.
- **Pinning tests** (`tests/test_rules.py`): no `print()` debug, no secrets in tree, public functions have type hints, no mutable default args, import-contract placeholder.
- **Documentation scaffolds**: `README.md`, `DESIGN.md`, `GUIDELINES.md`, `CHANGELOG.md` (Keep-a-Changelog), `docs/concepts.md` (glossary), `docs/enforcement-model.md` (4-tier rule architecture), `docs/adr/` ledger with a worked-example ADR-0000.
- **Hello-world example**: `src/<your-package>/example.py` + `tests/test_example.py` paired demonstration. Delete both when you write your first real module.
- **Dependabot** for `pip` + `github-actions` (weekly, grouped minor/patch).
- **OSS hygiene**: LICENSE (MIT default), SECURITY.md, CONTRIBUTING.md, issue + PR templates.

## Claude Code users (optional)

If you use [Claude Code](https://claude.com/claude-code), install the `/new-project` skill to get a 4-question UX with automatic GitHub repo creation and branch protection on top of the scaffold's own bootstrap:

```bash
# Install latest release (bundles SKILL.md + helper scripts)
gh release download --latest -R YuZh98/python-project-scaffold \
  --pattern "new-project.skill" -D /tmp
unzip -o /tmp/new-project.skill -d ~/.claude/skills/
```

To pin to a specific version, replace `--latest` with `--tag v1.7.6`.

Then invoke `/new-project` in any Claude Code session. The skill calls `scripts/init-project.py` under the hood — same engine as Options A and B.

The skill is **opt-in**. The scaffold works identically without it.

Source: [`tooling/claude-code/`](tooling/claude-code/). The `.skill` file is attached to every [GitHub Release](https://github.com/YuZh98/python-project-scaffold/releases) automatically by CI.

## Claude Code plugin

This repo also ships a Claude Code plugin that wraps the scaffold (and ships sibling skills for releases, changelog normalization, and pre-PR audits).

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
