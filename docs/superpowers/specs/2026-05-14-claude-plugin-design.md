# Claude Code Plugin Design

**Date:** 2026-05-14
**Status:** Approved (in implementation)
**Repo:** python-project-scaffold (monorepo: scaffold + plugin)

## 1. Background & Goals

Scaffold ships as a standalone Python CLI (`scripts/init-project.py` + `template/`) — independent of Claude. A hand-written Claude Code skill (`tooling/claude-code/`) wraps it for natural-language scaffolding. Currently installed manually at `~/.claude/skills/new-project/` — no versioning, no update channel.

Goal: package scaffold-aware tooling as a Claude Code plugin with self-hosted marketplace for versioned distribution. Secondary goal: public showcase / portfolio piece.

## 2. Architecture (Approach B — Conventional Plugin Layout)

```
python-project-scaffold/
├── .claude-plugin/marketplace.json       # repo = marketplace
├── plugins/new-project/
│   ├── plugin.json
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── LICENSE
│   ├── SKILL_AUTHORING.md                # universal convention doc
│   └── skills/
│       ├── new-project/
│       │   ├── SKILL.md                  # thin orchestrator
│       │   └── scripts/{preflight,bootstrap,write_license.py,finalize}
│       ├── release-helper/
│       │   ├── SKILL.md
│       │   └── scripts/release.sh
│       ├── changelog-normalizer/
│       │   ├── SKILL.md                  # rich BEFORE/AFTER examples
│       │   └── scripts/normalize_changelog.py
│       └── audit-runner/
│           ├── SKILL.md                  # framework + meta-principles
│           ├── scripts/{coordinator_brief.md, surface_detect.py, report_template.md}
│           └── dimensions/*.md           # 11 dim checklists
├── scripts/                              # scaffold (unchanged)
├── template/
│   └── ...                               # unchanged
├── docs/
│   ├── adr/000X-decoupled-plugin-versioning.md
│   └── superpowers/specs/<this file>
├── tooling/                              # deprecated, delete after migration
├── CHANGELOG.md                          # scaffold
└── CONTRIBUTING.md                       # add dual-changelog routing rule
```

**Separation:** scaffold + plugin are two products in one repo. Scaffold = standalone CLI. Plugin = consumer. Plugin has own version + own CHANGELOG (decoupled cadence).

## 3. v0.1 Scope

### Skills (4)

1. **new-project** (migrated + refactored from `tooling/claude-code/`)
2. **release-helper** (new)
3. **changelog-normalizer** (new, retained over agent's "premature abstraction" objection because user has empirical drift pain across sessions)
4. **audit-runner** (new, scaffold-aware delta from generic `audit-diff` skill)

### Out of scope for v0.1
- Slash command `/new-project` (skill auto-triggers on natural language; explicit command = redundant)
- ADR-writer skill (defer)
- Multiple plugin support (this repo hosts one plugin)

### Distribution
- v0.1: self-host marketplace at `.claude-plugin/marketplace.json`; users invoke `/plugin marketplace add YuZh98/python-project-scaffold`
- v1.0+: submit to community marketplace for discoverability

## 4. Universal SKILL.md Convention

Captured in `plugins/new-project/SKILL_AUTHORING.md`. Every SKILL.md MUST include:

1. **Trigger examples** — natural-language phrasings that should activate skill
2. **IO examples** — golden path + ≥2 edge cases with concrete input/output pairs
3. **Drift policy** — explicit rule: if user request diverges substantively from examples, **ask confirmation before producing output**
4. **Concrete output examples** — what skill produces (especially `changelog-normalizer`'s BEFORE/AFTER pairs)

Drift confirmation prevents silent extrapolation from anchored examples.

## 5. Per-Skill Specifications

### 5.1 new-project (refactor)

**Purpose:** scaffold fresh Python repo via scaffold's `init-project.py`.

**Refactor:** existing ~300-line SKILL.md → thin orchestrator (~80-110 lines) + `scripts/*.sh`. Token-efficiency win.

**Inputs:** 4-question UX (name, description, visibility, license).

**Flow:**
1. `scripts/preflight.sh` — refuse if inside git, check `gh auth`, probe scaffold availability
2. `scripts/bootstrap.sh NAME DESC LICENSE_ID` — git clone scaffold at pinned tag, invoke `python3 $SCAFFOLD_TMP/scripts/init-project.py --target --values --yes` (pipx path NOT used because scaffold has no `pyproject.toml`/console_script)
3. `scripts/write_license.py LICENSE_ID YEAR AUTHOR` — only for non-MIT (scaffold ships MIT by default)
4. `scripts/finalize.sh NAME VISIBILITY DESC` — `gh repo create`, push, branch protection

**SCAFFOLD_VERSION:** pinned to `v1.7.9` (latest tag) for v0.1. Plugin release flow re-pins to current scaffold tag.

**Dry-run:** ported from canonical skill — `/new-project --dry-run` shows preview without executing.

### 5.2 release-helper

**Purpose:** automate user's CLAUDE.md §9 release sequence.

**Composes:** `changelog-normalizer` as pre-step.

**Flow:**
1. Validate clean repo, non-detached branch, `[Unreleased]` non-empty
2. Invoke `changelog-normalizer` skill
3. Show proposed rotation diff; ask confirmation
4. `scripts/release.sh vX.Y.Z`: rotate `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`, commit `chore: release vX.Y.Z`, annotated tag, push (commit + tags atomic)
5. Follow-up: bump `pyproject.toml` version to `X.Y.(Z+1).dev0`, commit `chore: bump version`

**Refuses:**
- Non-standard branch (unless `--allow-branch`)
- Dirty working tree
- Empty `[Unreleased]`
- Version already tagged
- Missing/malformed `CHANGELOG.md`

**Honors:** GPG signing if `commit.gpgsign=true` (no override). Never `--no-verify`.

### 5.3 changelog-normalizer

**Purpose:** normalize `CHANGELOG.md` to a consistent Keep-a-Changelog style. Single responsibility: format conformance. Does NOT add or remove entries or invent content.

#### Structural rules

- Keep-a-Changelog format with `[Unreleased]` at top
- Six legal subheadings, in this exact order (Keep-a-Changelog 1.1.0 spec) — omit any that are empty before releasing: **Added · Changed · Deprecated · Removed · Fixed · Security**
- Version header: `## [X.Y.Z] - YYYY-MM-DD` (released) or `## [Unreleased]`
- Versions ordered descending (newest first)
- Link references at bottom (per Keep-a-Changelog spec)
- Empty subheadings removed at release time
- Bullet symbol = `-` only (no `*`, `+`, `•`)
- Sentence-case capitalization; period only when entry is multi-sentence
- Each version section opens with a **one-sentence summary** of what the release is about, before any `###` subheading. Enforced by `template/tests/test_cohesion.py::TestChangelogFormat`.

#### Content rules

- **WHAT changes and WHY it matters, not HOW.** Skip file paths, step numbers, implementation details.
- Group related changes into ONE bullet at user-impact level (imperative mood).
  - Poor: `Step 5: replaced cd with git -C in the license-amend block.`
  - Good: `Fix license rewrite silently failing when shell cwd doesn't persist.`
- End each entry with PR# or commit hash in parens — e.g. `(#42)` or `(abc1234)`
- Strip process narrative: any mention of `Claude`, `agent`, `audit pass`, `AI`, `re-audit`, review iterations
- Do not overuse bolding (`**text**`) — sparingly, for genuine emphasis only

#### Release-time rotation (called by release-helper)

- Rotate `[Unreleased]` block to `## [vX.Y.Z] - YYYY-MM-DD`
- Re-add empty `[Unreleased]` section above with the six standard subheadings ready
- Empty subheadings in the just-released block are dropped

#### Concrete output examples (REQUIRED in SKILL.md)

These verbatim excerpts from production CHANGELOGs anchor "what good output looks like" for the skill. Embed them in `SKILL.md` so the skill's intended output is reproducible without external lookups.

**Example A — single-sentence summary + multi-entry Fixed section (`python-project-scaffold/CHANGELOG.md` v1.7.7):**

```markdown
## [v1.7.7] - 2026-05-14

Correctness fixes found by independent multi-agent audit. The most impactful: non-MIT license files were being generated with incorrect text (a condensed paraphrase of Apache-2.0 instead of the full SPDX text), and several shell-level guards that the skill described in prose weren't actually enforced.

### Fixed
- Apache-2.0 license text was a condensed paraphrase; replaced with the full canonical SPDX verbatim. (#18)
- Non-MIT license rewrite used `cd` to change directories, which doesn't persist across tool calls; now uses `git -C` to operate without changing cwd. (#18)
- Dry-run relied on Claude reading instructions to skip GitHub steps; now an explicit shell gate exits before any network operation. (#18)
- Bootstrapping into an existing directory produced undefined behaviour; skill now aborts with a clear message if the target path already exists. (#18)
- License script was sourced from a hardcoded install path, breaking for users who copied only SKILL.md; now tries the bundled path first and falls back to the cloned scaffold. (#18)
```

**Example B — small release with Added + Changed (`python-project-scaffold/CHANGELOG.md` v1.7.6):**

```markdown
## [v1.7.6] - 2026-05-13

The skill can now be installed with a single command. CI automatically builds a `.skill` zip file and attaches it to every GitHub Release on tag push — no manual packaging step needed.

### Added
- CI workflow that builds and uploads `new-project.skill` to GitHub Releases on every version tag. (#15)

### Changed
- README install instructions updated to use `gh release download --latest`. (#15)
```

**Example C — concise refactor entry (`python-project-scaffold/CHANGELOG.md` v1.7.5):**

```markdown
## [v1.7.5] - 2026-05-13

Skill cut from 452 to 212 lines. License texts moved to a bundled helper script that loads only when needed; several redundant sections removed.

### Changed
- Skill condensed 53%; license texts extracted to `scripts/write_license.py`. (#14)
```

**What these examples illustrate:**
- One-sentence summary leads each version, explaining what the release is *about* in user-impact terms
- Entries say WHAT changed and WHY it matters; HOW (file paths, step numbers) is omitted
- Imperative mood: "Apache-2.0 license text was…" describes the bug, then "replaced with…" describes the fix
- Each entry ends with `(#PR)` or `(commit-hash)` in parens
- No process narrative, no `Co-Authored-By: Claude`, no bolding overuse

**Reference link (additional canonical examples):**
- `https://github.com/YuZh98/python-project-scaffold/blob/main/CHANGELOG.md?plain=1`
- `https://github.com/YuZh98/latex2arxiv/blob/main/CHANGELOG.md?plain=1`

These stay current automatically as the linked CHANGELOGs evolve. When the skill must demonstrate a pattern not covered by Examples A-C, point the user at the relevant section of the linked files.

#### Modes

- Default: in-place write with `.bak` backup
- `--check`: report violations on stderr, exit non-zero, no write (CI mode)
- `--diff`: preview without writing

#### Drift policy (critical)

- Ambiguous entry placement (could be `Fixed` or `Changed`?) → ask the user, never pick silently
- Verb-section mismatch (e.g. `Fix X` under `### Changed`) → flag for human review, do not auto-move
- **Never fabricate** commit hashes or PR numbers. If a ref is missing, ask the user or get explicit "no ref available" confirmation.

### 5.4 audit-runner

**Purpose:** pre-PR independent audit. Scaffold-aware delta from generic `audit-diff` skill: knows GUIDELINES.md/DESIGN.md/CLAUDE.md paths, applies 11-dim framework, supports mode flags, dispatches sub-agents on context-aware triggers.

#### 11 Dimensions

**CORE (6, always evaluated):**

1. **Correctness** — logic, races, error paths, edge cases, off-by-one, nullable. **+ Silent-breakage sweep:** removed guard / changed default / narrowed precondition / widened postcondition.
2. **Design quality** — architecture, boundaries, single-resp, file size, abstraction fit. **Nomenclature** (intent-revealing names) lives here.
3. **Conventions** — lint-tier mechanical: snake_case, type hints on public, no `print()`, no magic numbers, formatter clean, GUIDELINES.md rule violations. Explicit "lint-tier, not judgment" label.
4. **Test quality** — TWO sub-questions: (a) Discipline — TDD followed? failing-then-passing test? coverage gate? (b) Test code quality — mock abuse? brittle? isolated? names clear? critical-path gap?
5. **Docs & comments** — covers all written artifacts: CHANGELOG, ADRs, `DESIGN.md`, `GUIDELINES.md`, docstrings, comments, README, error messages. Specifically:
   - **CHANGELOG**: `[Unreleased]` exists, correct format, entries end with PR#/hash, one-sentence summary leads each version
   - **ADR**: if change is architectural (introduces new pattern, alters dependency direction, defines new public boundary) and no ADR present, flag it (per §6)
   - **DESIGN.md / GUIDELINES.md drift sweeps:**
     - *History-as-guidance*: are past decisions stated as binding when current context has shifted? Flag rules whose stated rationale no longer holds, decisions that read as "we did X for reason Y" when reason Y is gone, or "current practice is Z" statements that the diff contradicts. The fix is usually a one-line status update or supersession marker, not a rewrite.
     - *WHAT-vs-HOW/WHY overspec*: is the doc writing HOW or WHY when stating WHAT suffices? Implementation steps belong in code; only decisions and surviving rationale belong in DESIGN/GUIDELINES. Flag step-by-step recipes, file-path enumerations, or "currently we use library X version Y.Z" specifics that will rot.
   - **Comment quality**: WHY not WHAT (only when WHY is genuinely non-obvious — most code needs no comment), no rotted references, no TODO without ticket
   - **Public API**: docstrings + type hints present
   - **README**: code examples in README still execute against current code
   - **Deprecation/migration notices**: present when removing or renaming public surface
   - **User-facing error messages**: actionable, no internal jargon leakage
6. **CI & rule enforcement** — workflow YAML validity, pre-commit hooks updated if new rule, **§7 enforcement: new rule has pinning test in same PR OR explicit xfail(strict=False) with reason linking follow-up**, coverage gate, CI matrix covers `requires-python` versions.

**CONTEXT-AWARE (5, emit explicit `N/A because <reason>` if no surface, never silent skip):**

7. **Security** — triggers: auth / subprocess / eval / exec / `os.environ` write / network / deserialization / path-from-user-input / SQL touched.
8. **Performance** — triggers: hot path change / new DB query in loop / sync-in-async / removed index / new external call.
9. **Observability** — triggers: new failure path / swallowed exception / log level wrong / structured-log key change / metric drift.
10. **Interface contracts** — triggers: public symbol removed/renamed / default kwarg semantics changed / return type narrowed / exception type changed.
11. **Dependency hygiene** — triggers: new dep added or version bumped (license, pinning, supply-chain, duplicate, install bloat).

#### Drift = cross-cutting sweep

Each dim's checklist ends with: "what in this dim's scope drifted from another source?" — eliminates double-reporting. Drift is NOT its own dim.

#### Primary-dim rule

Each finding has ONE primary dim = where the fix lives. Cross-cutting observations get separate section. No double-reporting in findings table.

#### Mode flags (two orthogonal axes)

```
scope:  all | dims=correctness,security | files=src/foo.py
depth:  blocker-only | major+ | all
```

Default: `scope=all depth=major+`.

#### Orchestration (hybrid coordinator + on-demand subs)

- Coordinator agent (fresh ctx) loads project brief (GUIDELINES.md + CLAUDE.md + DESIGN.md + diff)
- Walks 6 CORE dims sequentially
- `scripts/surface_detect.py` scans diff → JSON list of triggered context-aware dims
- Coordinator spawns sub-agent per triggered dim (fresh ctx, single-dim focus)
- Coordinator dedupes via primary-dim rule, assembles report

| Mode | Coordinator | Sub-agents |
|---|---|---|
| `depth=blocker-only` | 6 core, fast | None |
| `depth=major+` (default) | 6 core, deep | On trigger |
| `depth=all` | 6 core, deep | All applicable, parallel |
| `scope=dims=<list>` | Only listed | Only listed |
| `scope=files=<list>` | Diff context limited | Same orchestration |

Cost: typical ~1-2 sonnet runs (~30-60s); deep audit ~3-5 parallel agents (~2-3 min, ~5×).

#### Good-audit meta-principles

- Fresh context per agent (no implementer history)
- Project brief loaded
- Severity tiered: blocker / major / minor / nit
- File:line citations
- Suggested fix inline
- One finding = one fact (no bundled rows)
- "What I did NOT check and why" mandatory
- "What's done well" capped 1 line, cite specific decision
- Time budget per dim
- No new requirements (don't invent acceptance criteria)
- No diff recap (describe deltas from expectations)
- Blocking-for-merge vs preference distinguished
- Context-aware dim: explicit N/A with reason, never silent skip

#### Report shape

```
## Verdict
Approve / Approve with nits / Request changes

## Executive summary (2-3 sentences)

## Findings table
| ID | Primary dim | Severity | File:Line | Finding | Suggested fix |

## Cross-cutting observations
(Multi-dim patterns; not per-finding)

## Per-dimension N/A justifications
(Context-aware dims with no surface — explicit reason)

## What I did NOT check and why

## What's done well
(1 line, specific decision)

## Open questions
```

## 6. Scaffold ↔ Plugin Contract

**Coupling:** plugin's `bootstrap.sh` shells out to scaffold's `scripts/init-project.py`.

**Resolution:** `git clone --depth 1 --branch $SCAFFOLD_VERSION` (pinned tag) into temp dir, invoke `python3 $TMP/scripts/init-project.py`. NOT pipx (scaffold has no pyproject.toml).

**Pinning:** `SCAFFOLD_VERSION` shell variable in `bootstrap.sh`. Plugin release flow re-pins to current scaffold tag.

**Contract test (CI):** new workflow runs `python3 scripts/init-project.py --help`, asserts flag surface plugin depends on (`--target`, `--values`, `--yes`). Breaks plugin builds if scaffold renames flags.

## 7. CI Gates

- Existing scaffold CI (lint, type check, test, coverage) unchanged
- NEW: scaffold ↔ plugin contract test (`init-project.py --help` surface)
- NEW: plugin smoke test — install plugin in sandbox `~/.claude/plugins/`, invoke `audit-runner` skill with toy diff, assert exit-0
- NEW: changelog-normalizer `--check` gate on plugin's own CHANGELOG

## 8. Versioning & Changelog Routing

**Decoupled versions:** scaffold version (current: v1.7.9) and plugin version (initial: v0.1.0) evolve independently.

**Why:** plugin can iterate on skill prose without forcing scaffold release; scaffold can ship bugfixes without re-publishing plugin.

**ADR:** `docs/adr/000X-decoupled-plugin-versioning.md` records this decision (per CLAUDE.md §6).

**Routing rule in CONTRIBUTING.md:**
- Scaffold-only change → scaffold `CHANGELOG.md`
- Plugin-only change → plugin `CHANGELOG.md`
- Cross-cutting (e.g. plugin adds flag requiring scaffold support) → entry in BOTH, link to each other

## 9. Release Path

- **v0.1 (now):** self-hosted marketplace in same repo. Users: `/plugin marketplace add YuZh98/python-project-scaffold` then `/plugin install new-project@python-project-scaffold`.
- **v1.0+:** submit to community marketplace (e.g. `wshobson/agents`) for discoverability.

## 10. Migration Plan

1. Create `plugins/new-project/` structure (in progress via parallel skill-creator agents)
2. Refactor existing `tooling/claude-code/new-project.md` → thin orchestrator + scripts
3. Add `.claude-plugin/marketplace.json` + `plugin.json`
4. Add ADR for decoupled versioning
5. Add CONTRIBUTING.md routing rule
6. Add CI contract test + smoke test
7. Verify plugin install + invoke locally
8. Delete `tooling/claude-code/` (deprecated)
9. Tag plugin v0.1.0
10. Update user's manual install: `rm -rf ~/.claude/skills/new-project/` then `/plugin install`

## 11. Open Implementation Notes

- Plugin `bootstrap.sh` MUST use `git clone` not pipx (scaffold has no console_script)
- `--dry-run` flag from canonical skill must be preserved in new orchestrator
- `SCAFFOLD_VERSION` pinned to `v1.7.9` for v0.1
- Universal SKILL.md convention applied to all 4 skills present + future
- `audit-runner` does NOT replace harness's generic `audit-diff` — it adds scaffold-aware orchestration

## Appendix A — Rejected Options

- **Lockstep versioning** (plugin version tracks scaffold) — rejected: forces scaffold bump for skill typo
- **Slash command `/new-project`** — rejected: skill auto-triggers, command duplicates trigger phrases for no UX gain
- **Drift as own dim** — rejected: doubles checking burden, becomes a property cross-cut within each dim
- **Single-agent audit only** — rejected: bias bleeds across dims, no parallel speedup for deep audits
- **Multi-agent fan-out always (11 agents)** — rejected: 11× token cost for marginal independence on small diffs
- **Replace audit-runner with docs/auditing.md** — initially chosen, then reverted: framework too complex for docs-only; encapsulation in skill prevents application drift
- **changelog-normalizer folded into release-helper** — initially recommended, then reverted: user has empirical pain from cross-session changelog drift; standalone skill warranted
- **First-time invocation Q&A (`mention_coauthor` + `prose_style` preferences)** — deferred to v0.2 once the corresponding behaviors are implemented. Shipping the prompt without the behavior would be UX theater: the answers would be cached but never read by `parse`/`normalize`/`render`/`main`. Rewire when the rendering paths actually consume the preferences.
