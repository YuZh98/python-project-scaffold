# new-project (Claude Code plugin)

Scaffold-aware Claude Code skills for Python project lifecycle:

- **new-project** — scaffold fresh Python repos via `python-project-scaffold`
- **release-helper** — automate the release sequence (rotate CHANGELOG, tag, push)
- **changelog-normalizer** — normalize CHANGELOGs to consistent Keep-a-Changelog style
- **audit-runner** — pre-PR independent audit using an 11-dimension framework

## Install

```bash
/plugin marketplace add YuZh98/python-project-scaffold
/plugin install new-project@python-project-scaffold
```

## Usage

Each skill auto-triggers on natural language. See each `skills/<name>/SKILL.md` for trigger phrases and IO examples.

## Requirements

- `git` (the `new-project` skill clones the scaffold at a pinned tag)
- `gh` CLI with authentication (`gh auth login`)
- Python 3.11+
- `make`

## Version

See `CHANGELOG.md`.
