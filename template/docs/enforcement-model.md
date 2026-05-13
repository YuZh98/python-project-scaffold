# Enforcement Model

The scaffold ships rules at four enforcement tiers. Strong tiers cannot be bypassed; weak tiers can drift. When a rule can move down one tier, move it.

> **Rule of thumb on commit rejection**: when a hook or CI fails, identify which tier surfaced it. The fix lives at that tier or below — not above.

---

## Tier 1 — CI / tests / linters (mechanical, blocking)

| Mechanism | What it catches | Where to fix |
|-----------|-----------------|--------------|
| `pytest tests/test_rules.py` (pinning tests) | no `print()` in production, type hints on public functions, no mutable default args, no secrets in repo | Production code |
| `pytest tests/` (regular tests) | functional regressions | Code or test |
| `pyright .` | type-hint correctness, missing annotations | Code (add hints) |
| `ruff check .` | lint rules (unused imports, line length, dead code) | Code (run `ruff --fix` for autofixable subset) |
| `pytest --cov` 95% gate | coverage drop below threshold | Add tests |

Rules at this tier are non-negotiable: a red CI run blocks merge.

## Tier 2 — Pre-commit + Claude Code hooks (gates an action)

| Mechanism | What it catches | Where to fix |
|-----------|-----------------|--------------|
| `pre-commit` hooks | trailing whitespace, missing EOF newline, malformed YAML/TOML, merge-conflict markers, ruff auto-fixable issues | Re-run `git add` after the hook auto-fixes; commit again |
| `~/.claude/hooks/rule-check-bash.sh` (Claude Code only) | AI-attribution trailers in commit messages, status literals in production code, `print()` in new code | Edit the staged content; remove the violating pattern |

Pre-commit hooks fire on `git commit`; the Claude Code hook fires on every Bash tool invocation in a Claude session. The Claude Code hook is only active when committing through Claude — `git commit` from a plain terminal does NOT trigger it. For terminal-agnostic enforcement, the rule must live at Tier 1.

## Tier 3 — Prose conventions (this file, CLAUDE.md, GUIDELINES.md)

| Source | What it covers | Where to fix |
|--------|----------------|--------------|
| `GUIDELINES.md` | Naming, error handling, testing patterns, CHANGELOG discipline | Update both code and GUIDELINES.md if the convention is changing |
| `CLAUDE.md` (project) | Stack pins, project-specific patterns, gotchas registry pointer | Same — update prose, then code, then add pinning test |
| `~/.claude/CLAUDE.md` (universal) | Cross-project rules: WHAT-not-HOW commits, audit-before-merge, etc. | Discuss with maintainer before changing |

Prose conventions are judgment calls — a reader applies them. They drift faster than Tier 1 enforcement, so the scaffold's meta-rule says: every convention added here SHOULD be paired with a pinning test (or an `xfail` bridge with a follow-on issue).

## Tier 4 — Memory / preferences

Per-session preferences live in Claude's project memory at `~/.claude/projects/<this-project>/memory/`. This is the weakest tier — relying on a memory file to enforce a load-bearing invariant is a known anti-pattern. Use Tier 4 only for preferences and history, never for rules.

---

## Worked example: "my commit was rejected — which tier?"

| Symptom | Tier | Fix |
|---------|------|-----|
| `ruff` autofixed a file → hook exit non-zero | Tier 2 (pre-commit) | `git add` the fixed file; commit again |
| `pytest tests/test_rules.py::TestNoPrintDebugInProductionCode` red | Tier 1 (pinning test) | Remove `print()` from production; use logging or return value |
| `pytest --cov` says 91% < 95% | Tier 1 (coverage gate) | Add tests until coverage reaches 95% |
| Reviewer comment: "use snake_case here" | Tier 3 (GUIDELINES.md) | Rename the symbol; reply with the GUIDELINES section |
| `pyright .` says `Argument of type "str" cannot be assigned...` | Tier 1 (type checker) | Add or fix the type hint |

If a rule lives in prose but you find yourself breaking it repeatedly, that's the signal it should move down to Tier 1 or Tier 2.
