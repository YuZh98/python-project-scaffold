# Claude Code Project Rules

> **Optional file.** Loaded by Claude Code if you use it as your editor. Safe to delete otherwise — no other tool reads this file.

_Project-specific rules. Universal rules inherit from `~/.claude/CLAUDE.md`._

## Layer model (inherited from universal)

Four enforcement layers, in order of strength (top = strongest):

1. **CI / tests / linters** — mechanical enforcement; ruff, pyright, pytest, `tests/test_rules.py` pinning tests, coverage gate.
2. **Pre-commit + Claude Code hooks** — pre-action gates; format-fix, EOF, YAML/TOML validity, merge-conflict markers, and the user's global `rule-check-bash.sh` (Claude Code-specific).
3. **This file + `GUIDELINES.md`** — judgment + style rules. Read at session start.
4. **Per-session memory** — preferences, dynamic state.

When a rule can move down (toward layer 1), move it. Memory is the weakest place for load-bearing rules.

See `~/.claude/CLAUDE.md` for the full universal rule set.

---

## Stack
- Python <<PYTHON_FLOOR>>+
- (add: framework, database, deployment target as decided)

## Architectural decisions
- See `docs/adr/` — write ADR-0001 for the import contract before adding any production code.

## Project-specific rules
- (add rules here as they're discovered — load-bearing patterns, gotchas, etc.)

## Stack-specific gotchas
- (use the capture-pin-comment workflow per universal rules — `docs/dev-notes/` is the registry)
