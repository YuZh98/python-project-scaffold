# Tooling

Editor- and AI-assistant-specific convenience artifacts. **Opt-in.** The scaffold's bootstrap engine (`scripts/init-project.py`, `scripts/scaffold.sh`, `scripts/substitute.py`) is framework-neutral and does not require anything from this directory.

Use these only if you already use the tool they target.

## Available integrations

| Subdirectory | Tool | What it adds |
|---|---|---|
| [`claude-code/`](claude-code/) | [Claude Code](https://claude.com/claude-code) | `/new-project` skill — 3-prompt UX, auto GitHub repo creation, branch protection on top of the scaffold's own `init-project.py` flow |

## Install

Each integration documents its own install command in the parent README's "Quick start" section under the relevant option. The canonical files in this directory are the source of truth; copy them to the tool's expected location and update as new scaffold releases land (see scaffold `CHANGELOG.md`).

## Versioning

Files in this directory ship with each scaffold release. Pin your local copy to a specific scaffold tag (e.g. `v1.6.0`); never base it on `main`. When the scaffold releases a new version, re-copy the relevant file to pick up any improvements.

## Adding a new integration

Open a PR adding a new subdirectory at this level (e.g. `tooling/vscode/`). Each new integration must (a) be opt-in, (b) document its install command in the scaffold README, (c) work without modifying any file in `template/` or `scripts/`.
