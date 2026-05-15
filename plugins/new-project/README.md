# python-project-scaffold (Claude Code plugin)

Renamed from `new-project` in plugin v0.2.0; the slash command `/new-project` remains unchanged.

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

## Migration from `new-project@python-project-scaffold`

If you have the plugin installed under its previous name:

```bash
claude plugin uninstall new-project@python-project-scaffold
claude plugin install python-project-scaffold@python-project-scaffold
```

Skill triggers, bundled scripts, and behaviour are otherwise unchanged.

## Usage

Each skill auto-triggers on natural language. See each `skills/<name>/SKILL.md` for trigger phrases and IO examples.

## Requirements

- `git` (the `new-project` skill clones the scaffold at a pinned tag)
- `gh` CLI with authentication (`gh auth login`)
- Python 3.11+
- `make`

## Version

See `CHANGELOG.md`.
