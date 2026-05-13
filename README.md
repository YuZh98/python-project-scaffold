# python-project-scaffold

A Python project scaffold with mature rule-guarding wired from commit 1.

[GitHub template repo](https://github.com/YuZh98/python-project-scaffold).

## What you get

A new project bootstrapped from this scaffold ships with, on day 0:

- **CI**: ruff + pyright (basic) + pytest + deprecation-strict pass + coverage gate (95%) across Python 3.11–3.14
- **Pre-commit hooks**: ruff (lint + autofix), trailing whitespace, EOF newline, YAML/TOML validity, merge-conflict markers
- **Pinning tests** (`tests/test_rules.py`): no `print()` debug, no secrets in tree, public functions have type hints, no mutable default args, import-contract placeholder
- **Documentation scaffolds**: `DESIGN.md`, `GUIDELINES.md`, `CLAUDE.md`, `CHANGELOG.md` (Keep-a-Changelog), `docs/adr/` ledger with a worked-example ADR-0000
- **Dependabot** for `pip` + `github-actions` (weekly, grouped minor/patch)
- **Layer model** inherited from `~/.claude/CLAUDE.md` (4-tier rule enforcement)

## Quick start (manual)

```bash
git clone --depth 1 --branch v1.0.0 https://github.com/YuZh98/python-project-scaffold.git /tmp/scaffold
cp -R /tmp/scaffold/template/. /path/to/new-project/
cd /path/to/new-project
# Create a values.json with the 10 placeholders (see template.manifest.json for the list)
python3 /tmp/scaffold/scripts/substitute.py --target . --values values.json
git init && git add . && git commit -m "feat: initial scaffold"
```

## Quick start (Claude Code skill)

If you have the `/new-project` skill installed:

```
/new-project
```

The skill prompts for project name, description, license, visibility, then clones, substitutes, initializes git, runs tests, makes the first commit, and pushes to GitHub. See [the skill](https://github.com/YuZh98/python-project-scaffold/blob/main/docs/skill-usage.md) for details.

## Placeholders

10 placeholders, listed in `template.manifest.json`. Required: project name, title, package name, description, author name + email, year, license id, GitHub username, Python floor. Auto-derived: ruff target (from Python floor).

## Versioning

The scaffold uses release tags (`v1.0.0`, `v1.1.0`, ...). Pin your `/new-project` skill or manual clone to a specific tag — never clone latest `main`. See [CHANGELOG.md](CHANGELOG.md) for what each release changed.

## Maintenance

| Concern | Approach |
|---------|----------|
| Python version coverage | CI matrix hardcoded `3.11`–`3.14`. When 3.15+ ships, manually add to matrix + bump scaffold version. Manifest regex is open-ended; the matrix is the only hardcoded list. |
| Action SHA pins | Dependabot tracks `github-actions` weekly. |
| Pre-commit hook versions | Manual `pre-commit autoupdate` quarterly. |
| Pinning test rules | New universal rules land in this repo, then propagate to new projects only. Existing scaffolded projects sync manually. |

## License

MIT.

## See also

- [`template.manifest.json`](template.manifest.json) — placeholder registry
- [`scripts/scaffold.sh`](scripts/scaffold.sh) — orchestrator
- [`scripts/substitute.py`](scripts/substitute.py) — substitution engine
- [`tests/test_scaffold.py`](tests/test_scaffold.py) — end-to-end smoke test
- [`tests/test_skill_flow.py`](tests/test_skill_flow.py) — SKILL.md ↔ manifest drift guard
