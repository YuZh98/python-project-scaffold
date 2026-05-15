# Claude Plugin v0.2 Roadmap

**Date:** 2026-05-14
**Source:** independent `plugin-dev` evaluation against Claude Code's official plugin spec (84/100; "marketplace-ready with caveats")

Tracks work deferred from v0.1.0. Each item is sized for one focused PR.

## Major (3)

### M1 — Trim `audit-runner/SKILL.md` via progressive disclosure

**Why:** SKILL.md is 3,288 words — 64% over the spec's 2,000-word recommendation. Token cost paid every invocation.

**What:**
- Move 11-dim catalogue + mode-flag tables + report shape + meta-principles → `audit-runner/references/framework.md`
- Move IO examples → `audit-runner/references/examples.md`
- Trim SKILL.md to ~1,200 words: trigger contract + invocation pattern + pointers to references/

### M2 — Move `changelog-normalizer` canonical examples to `references/`

**Why:** SKILL.md is 2,064 words; the three BEFORE/AFTER excerpts (Examples A/B/C from production CHANGELOGs) are progressive-disclosure violations.

**What:**
- Create `changelog-normalizer/references/canonical-examples.md` with the three excerpts + "What these illustrate" section
- SKILL.md keeps a one-line pointer + the structural-rules table

### M3 — Ship 4 passthrough slash commands

**Why:** SKILL.md descriptions advertise `/new-project`, `/release`, `/changelog-normalize`, `/audit-diff`. Users typing those today get "no command" — discoverability failure.

**What:** create `plugins/new-project/commands/{new-project,release,changelog-normalize,audit-diff}.md`. Each ~5 lines: frontmatter + delegation to the named skill. Optional: pre-set flags (e.g. `/new-project --dry-run`).

## Minor (6)

### m4 — Add `repository` field to `plugin.json`

`{"repository": "https://github.com/YuZh98/python-project-scaffold"}`.

### m5 — Add `version` to marketplace `plugins[]` entry

Pin `0.1.0` (or current) at the marketplace level for explicit version contract.

### m6 — Move `SKILL_AUTHORING.md` out of plugin root

Auto-discovery doesn't load it. Move to `docs/skill-authoring.md` and reference from plugin README.

### m7 — Convert `dimensions/` → `references/dimensions/`

Spec convention is `references/` for "loaded as needed" docs. Update all `dimensions/*.md` cross-refs in `audit-runner/SKILL.md` and `coordinator_brief.md` after the move.

### m8 — Replace `/Users/alice/...` placeholder paths in IO examples

Use `~/audit-tools` or `<workdir>/audit-tools` instead.

### m9 — Move `coordinator_brief.md` from `scripts/` to `references/`

It's documentation, not executable code. Spec convention.

### m10 — Strip `~/.claude/CLAUDE.md` user-side reference from release-helper SKILL.md

Inline the rule (release sequence) instead of citing the user's private global file.

## Privacy enforcement (deferred from v0.1 Wave 10)

Original Wave 10 Agent A crashed mid-flight. Re-dispatch in v0.2:

- `scripts/check-privacy.py` — pattern-scan staged commit message + tracked files (AI/agent/process narrative + personal paths)
- Pre-commit hook integration (`.pre-commit-config.yaml`)
- CI workflow `.github/workflows/privacy.yml`
- Pinning test `tests/test_privacy.py`
- Allowlist file `.privacy-allow.txt`
- Promote rule to `template/GUIDELINES.md` so every bootstrapped project inherits the gate
- Apply to scaffold + template + plugin (eat own dogfood)

## v0.1 deferrals (other)

- **F6 scaffold CHANGELOG missing refs** — 5 v1.0.0 entries lack PR/commit refs. Backfill + add scaffold-CHANGELOG `--check` step to ci.yml.
- **`Preferences` cache rewire** — `mention_coauthor` + `prose_style` removed from v0.1 because answers were dead. Re-introduce when normalize logic actually consumes them.
- **`new-project` package-layout question** — current default is `src/`. Add a 5th question or accept feedback that this should remain a silent default.
- **`new-project` Python-floor question** — silent default `3.11`. Some users will care; consider adding to the question UX.
- **Plugin name collision** — plugin is `new-project`, contains skill `new-project`. Consider rename to `python-lifecycle` or `scaffold-toolkit` for clarity (breaking change → defer to v0.2 deliberately).
- **`bump-version` standalone skill** — split out of release-helper for users who want to bump without releasing.
- **`ADR-writer` skill** — global rules §6 requires ADRs for architectural decisions; no skill helps yet.
- **README transcript-style walkthrough** per skill — current 30-line README + per-SKILL.md examples are dense for new users.
- **`finalize.sh` VISIBILITY whitelist + `bootstrap.sh` NAME pre-validation** — defensive upstream guards (currently caught by `init-project.py` but only after wasted work).
- **`release.sh` pyproject bump scope to `[project]`** — current `count=1` works for well-formed pyproject; tomllib refactor for stricter scoping.

## Anti-roadmap (explicitly NOT planned)

- **audit-runner reimplemented as self-spawning** — rejected; harness binding is runtime-specific. Keep prose-driven composition.
- **changelog-normalizer with multiple style profiles** — rejected; one canonical KaC 1.1.0 style. Override via fork.
- **Plugin split into 4 separate plugins** — considered, deferred. Bundle stays for v0.2; revisit if user demand emerges.
