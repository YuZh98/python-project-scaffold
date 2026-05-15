# ADR 0001: Decoupled scaffold and plugin versioning

**Status:** Accepted
**Date:** 2026-05-14

## Context

This repository hosts two products in a monorepo:
- the python-project-scaffold CLI (`scripts/init-project.py` + `template/`)
- the Claude Code plugin (`plugins/new-project/`)

The plugin consumes the scaffold (its `new-project` skill clones the scaffold at a pinned tag and runs `init-project.py`). Two options for versioning:

1. **Lockstep:** plugin version == scaffold version. Every scaffold release re-publishes the plugin; every plugin change forces a scaffold release.
2. **Decoupled:** plugin and scaffold version independently. Plugin pins which scaffold tag it was tested against.

## Decision

Use decoupled versioning. The plugin maintains its own `plugins/new-project/CHANGELOG.md` and its own `plugin.json` version (initial: `0.1.0`). The scaffold continues using its existing top-level `CHANGELOG.md` and tag scheme (`vX.Y.Z`). Plugin tags use a separate prefix: `plugin-vX.Y.Z`.

## Consequences

**Positive:**
- Plugin can ship skill prose fixes without forcing a scaffold release
- Scaffold can ship internal-only changes without re-publishing the plugin
- Independent release cadences match the products' actual change rates

**Negative:**
- Two CHANGELOGs in one repo — risk of routing confusion. Mitigated by the routing rule documented in `CONTRIBUTING.md`.
- Cross-cutting changes (plugin needs new scaffold flag) require entries in BOTH CHANGELOGs and a scaffold release before the plugin release.

## Alternatives considered

- **Lockstep:** rejected — forces scaffold bump for plugin-only changes
- **Single CHANGELOG with sub-sections:** rejected — readers expect one CHANGELOG per published artifact
