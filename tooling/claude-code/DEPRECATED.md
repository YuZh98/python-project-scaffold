# DEPRECATED

This directory is the previous home of the hand-written `new-project` Claude Code skill. As of plugin v0.1.0 (2026-05-14), the skill lives at `plugins/new-project/skills/new-project/` and is distributed via the marketplace at `.claude-plugin/marketplace.json`.

## Migration for existing users

If you previously installed the skill manually at `~/.claude/skills/new-project/`:

```bash
rm -rf ~/.claude/skills/new-project/
# Then in Claude Code:
/plugin marketplace add YuZh98/python-project-scaffold
/plugin install new-project@python-project-scaffold
```

## Scheduled removal

This directory will be removed in plugin v0.2.0 or scaffold v1.8.0, whichever ships first.
