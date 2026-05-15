---
name: audit-runner
description: >
  Invoke for /audit-diff, "audit this PR", "audit the diff", "pre-merge audit", "second
  opinion on this change", or any pre-PR independent review of a Python diff against the
  project's GUIDELINES.md / CLAUDE.md / DESIGN.md. Scaffold-aware delta from the
  harness-level audit-diff skill: knows this plugin's project-brief paths and ships the
  11-dimension framework (with two-axis mode flags, primary-dim rule, drift sweeps,
  meta-principles) as a static spec plus per-dimension checklists, a surface-detection
  script, a coordinator brief, and a report template. The skill itself does NOT spawn
  agents; the model or user reading this skill drives orchestration using whatever
  dispatch mechanism the runtime provides. Required (per global rules §3) before merging
  any PR that touches business logic, schema, or production behavior; skip only for
  docs-only / dependabot grouped-minor / single-file typo PRs. Distinct from general code
  review: this is the structural pre-merge gate, not freeform feedback. Do NOT trigger on
  changelog edits ("normalize CHANGELOG" → changelog-normalizer), scaffolding requests
  ("new repo" / "spin up project" → new-project), or release-flow phrasings ("cut a
  release" / "ship vX.Y.Z" / "tag and push" → release-helper).
---

# audit-runner

Pre-PR independent audit framework. Eleven dimensions, two orthogonal mode axes,
primary-dim rule, drift sweeps, meta-principles. The implementing agent **cannot** satisfy
this gate alone (confirmation bias is structural); the audit must be performed with fresh
context against the project's declared rubric.

Mechanics live in `scripts/` and `dimensions/`. This file describes WHEN, WHY, the
framework shape, the IO contract, and the recommended invocation pattern.

---

## What this skill DOES and DOES NOT do

**DOES ship:**

- The 11-dimension audit framework as a written specification (this file).
- Per-dimension checklists (`dimensions/*.md`) — usable directly by a human reviewer or by
  a model applying the framework.
- A surface-detection helper (`scripts/surface_detect.py`) that scans a unified diff and
  emits a JSON list of which context-aware dimensions have triggers in the diff.
- A reusable coordinator brief (`scripts/coordinator_brief.md`) — operational handbook
  for whoever (model or human) is performing the audit.
- A report template (`scripts/report_template.md`) defining the required output shape.

**DOES NOT do:**

- Spawn sub-agents. The skill is a static spec + scripts; it has no executable
  substrate that dispatches agents.
- Run tests, lint, or any project gates. The audit is **static**: it reads the diff and
  the project brief, and produces a report. Runtime evidence is escalated as an open
  question, not fabricated.
- Decide on its own which agents (if any) to dispatch. That decision belongs to the
  caller — model, human, or a higher-level orchestrator — and depends on what the
  current runtime supports.

Composition is **prose-driven**: the skill describes WHAT to compose; the runtime
decides HOW.

---

## Trigger examples

- "audit this PR"
- "audit the diff"
- "pre-merge audit"
- "second opinion on this change"
- "review before merge"
- "/audit-diff"
- "audit for correctness and security only"   *(subset — scope=dims=...)*
- "deep audit, all dimensions"                *(depth=all)*
- "fresh-context review of the staged changes"

## When NOT to trigger

- Freeform code review with no merge gate ("what do you think of this function?") — use
  general review, not the audit framework.
- Docs-only / dependabot grouped-minor-or-patch / single-file typo PRs (audit-exempt per
  global rules §3). State the exemption and stop.
- Diffs that do not yet exist (no staged changes, no PR open). Ask which diff to audit.
- **Adjacent sibling-skill territory** — route to the appropriate sibling, not here:
  - "Normalize / fix / lint the CHANGELOG" → `changelog-normalizer`.
  - "Scaffold / spin up / start a new Python project" → `new-project`.
  - "Cut a release / ship vX.Y.Z / tag and push" → `release-helper`.

  These three skills compose with audit-runner (release-helper calls changelog-normalizer
  as a pre-step; audit-runner is the merge gate that runs against any of their PRs), but
  the user's request word-shape decides which entry point wins. "Audit" / "review" /
  "pre-merge" wins here.

## Drift policy

If the user request diverges from the examples — unrecognised dimension name, audit of
something other than a Python diff, audit without a project brief on disk — **stop and
ask for confirmation** before any audit work begins. Specifically:

- **Suspiciously small diff** (<5 LOC after excluding whitespace): ask whether the user
  wants the full 11-dim framework or just a blocker-only sanity check. The framework has
  fixed overhead; trivial diffs do not justify it.
- **Unrecognised scope dim**: list the 11 valid dim slugs (see *Dimension catalogue*
  below) and ask which the user meant.
- **No GUIDELINES.md / CLAUDE.md in repo**: warn that the audit will fall back to global
  rules only, then ask whether to proceed.
- **Diff spans multiple unrelated concerns**: surface this before any audit work begins
  and ask whether to audit the union or split into separate audit runs.

A wrong refusal is recoverable; a misframed audit produces a confident report against
the wrong rubric and wastes the reviewer's trust.

---

## Mode flags (two orthogonal axes)

```
scope:  all                              (default)
        dims=correctness,security,...    (restrict to listed dims; comma-sep slugs)
        files=src/foo.py,src/bar.py      (limit diff context to listed paths)

depth:  blocker-only                     (single-pass, no extra dispatch)
        major+                           (default; deeper context-aware passes when triggers fire)
        all                              (every applicable context-aware dim, parallel if dispatcher allows)
```

**Default for behaviour-changing PR**: `scope=all depth=major+`. The two axes do not
interact: `scope=dims=...` controls *which* dimensions are evaluated; `depth=...`
controls *how thoroughly* each dim is dug into and *whether additional fresh-context
passes are recommended* per dim.

Pass on the invocation line, e.g.:

```
/audit-diff scope=dims=correctness,tests depth=all
/audit-diff scope=files=src/auth/*.py depth=major+
```

---

## Dimension catalogue

Eleven dimensions, split into two tiers. Each has a checklist file under `dimensions/`.

### CORE (always evaluated, six dims)

| Slug | Name | One-line scope |
|------|------|----------------|
| `correctness` | Correctness | Logic bugs, edge cases, **silent-breakage sweep** (removed guard / changed default / narrowed precondition / widened postcondition). |
| `design` | Design quality | Architecture, layer boundaries, single responsibility, file size, abstraction fit, intent-revealing names (judgment-tier). |
| `conventions` | Conventions | **Lint-tier mechanical, not judgment.** snake_case, type hints on public, no `print()`, no magic numbers, formatter clean, GUIDELINES.md rule violations. |
| `tests` | Test quality | (a) **Discipline**: TDD followed? failing-then-passing? coverage gate met? (b) **Code quality**: mock abuse, brittleness, isolation, intent-revealing names, gaps in critical path. |
| `docs` | Docs & comments | CHANGELOG `[Unreleased]` entry presence and verb/diff agreement (format checks live in `changelog-normalizer`), ADR for hard-to-reverse decisions, docstrings on public API, comment quality, README example accuracy, deprecation notices, user-facing error clarity. **DESIGN.md / GUIDELINES.md drift sweeps**: *history-as-guidance* (rationale that no longer holds) and *WHAT-vs-HOW/WHY overspec* (implementation recipes / file-path enumerations / pinned-version specifics that will rot). |
| `ci` | CI & rule enforcement | GHA YAML validity, pre-commit hooks updated if rule changed, **§7 enforcement: new rule has pinning test in same PR OR explicit `xfail(strict=False)` with reason linking follow-up PR**, coverage gate, CI matrix covers `requires-python`. |

### CONTEXT-AWARE (evaluate OR emit explicit "N/A because <reason>", five dims)

Never silent skip — context-aware dims always appear in the report, either with findings
or with a justified N/A line.

| Slug | Name | Surface triggers |
|------|------|------------------|
| `security` | Security | Auth path / `subprocess.` / `eval`/`exec` / `os.environ` write / network call / deserialization (`pickle`, `yaml.load`) / path-from-user-input / SQL touched. |
| `performance` | Performance | Hot path change / new DB query in loop / sync-in-async / removed index / new external call. |
| `observability` | Observability | New failure path / swallowed exception / log level wrong / structured-log key change / metric drift. |
| `interface` | Interface contracts | Public symbol removed/renamed / default kwarg semantics changed / new exception class / `__all__` drift. (Return-type narrowing requires diff-paired context, so the line scanner does not surface it; the dimension checklist still covers it once the dim is evaluated.) |
| `dependency` | Dependency hygiene | New dep added or version bumped (license, pinning, supply-chain, duplicate, install bloat). |

The diff scanner `scripts/surface_detect.py` produces the trigger list. The auditor reads
it to decide which context-aware dims need a focused pass.

---

## Recommended invocation pattern (prose-driven composition)

The framework is realised by reading this file and applying the procedure below. The
exact dispatch mechanism — single-pass model, parallel sub-agents, human reviewer — is
runtime-specific; the skill describes WHAT to compose, not HOW.

```
   /audit-diff
       │
       ▼
 ┌─────────────────┐
 │ surface_detect  │  scans diff, emits JSON trigger list (dim → file:line)
 └────────┬────────┘
          │
          ▼
 ┌─────────────────────────────────────────┐
 │ Audit pass (FRESH CONTEXT)              │  load coordinator_brief.md +
 │   - load project brief                  │    GUIDELINES.md + CLAUDE.md + DESIGN.md +
 │   - walk 6 CORE dims                    │    diff + surface_detect output
 │   - for each context-aware dim with a   │
 │     trigger (or all of them at depth=all),
 │     apply its checklist with focused    │
 │     attention — runtime decides whether │
 │     this is a fresh sub-agent dispatch, │
 │     a focused single-pass pass, or a    │
 │     human-driven review                 │
 │   - dedupe via primary-dim rule         │
 │   - assemble report from template       │
 └────────┬────────────────────────────────┘
          │
          ▼
   final report (markdown, shape per scripts/report_template.md)
```

**Composition is prose-driven, not executable.** The runtime decides whether to
dispatch fresh-context sub-agents per context-aware dim or simulate the discipline by
re-reading the brief between dims in a single pass. The framework's correctness —
primary-dim rule, drift sweeps, mandatory N/A, meta-principles — is identical either way.

If `surface_detect.py` is not runnable (no Python, no diff on disk), say so and either
ask for the trigger list or evaluate every context-aware dim conservatively.

### Mode → recommended-shape mapping

| `depth=` | Pass count | Per-dim shape |
|----------|------------|---------------|
| `blocker-only` | One pass | Walk the 6 CORE dims; emit blockers only. Skip context-aware dim deep dives. |
| `major+` *(default)* | One pass + per-trigger focused passes | Walk CORE dims; for each triggered context-aware dim, do a focused pass (fresh sub-agent dispatch if the runtime supports it). |
| `all` | One pass + per-applicable-dim focused passes | Walk CORE dims; do a focused pass per applicable context-aware dim regardless of triggers (parallel where the dispatcher allows). |

| `scope=` | Effect |
|----------|--------|
| `all` *(default)* | All eligible dims evaluated |
| `dims=<list>` | Only listed dims evaluated; others marked `N/A (scope excluded)` |
| `files=<list>` | Diff context limited to listed paths before any audit work begins |

---

## Good-audit meta-principles (the auditor must follow)

These are not decorative. Pre-PR audits drift toward useless "looks good" reports without
them. The coordinator brief enforces each.

- **Fresh context per pass.** No implementer history bleeds in. *Why:* confirmation bias
  is the failure mode the audit exists to defeat.
- **Project brief loaded.** GUIDELINES.md + CLAUDE.md + DESIGN.md (if present) are
  read before walking dims. *Why:* the audit measures the diff against the project's
  declared rubric, not the auditor's priors.
- **Severity tiered.** `blocker` / `major` / `minor` / `nit`. Each dim file ships a
  severity guide. *Why:* a flat list of issues is unactionable; the reader needs to know
  what blocks merge.
- **File:line citations on every finding.** No "somewhere in the auth module."
- **Suggested fix inline.** A finding without a fix path is half a finding.
- **One finding = one fact.** No bundled rows. *Why:* bundled findings hide which part
  the author should address; granularity is what makes the table actionable.
- **"What I did NOT check and why" is mandatory.** Surfaces blind spots so the reader
  can compensate. *Why:* unstated omissions look like coverage and create false
  confidence.
- **"What's done well" capped at one line, citing a specific decision.** No filler. *Why:*
  performative praise dilutes the rest of the report.
- **Time budget per dim.** Coordinator brief sets a soft cap; the auditor stops digging
  past it and notes what was deferred.
- **No new requirements.** Audit against the project's declared rubric, not invented
  acceptance criteria. *Why:* mid-review goalpost-moving is the fastest way to lose the
  implementer's trust.
- **No diff recap.** The reader has the diff. Describe deltas from expectations, not the
  diff itself.
- **Blocking-for-merge vs preference distinguished.** Every finding states which.
- **Context-aware dim with no surface → explicit "N/A because <reason>", never silent
  skip.** *Why:* silence reads as coverage; explicit N/A is the only honest signal.

---

## Drift = cross-cutting sweep within each dim (not its own dim)

Drift findings — CHANGELOG vs `pyproject.toml`, comment vs code, ADR status vs reality —
are caught by each dim's own drift-sweep prompt and primary-dim'd to where the fix lives
(usually `docs`). There is **no separate "Drift" dimension**; that would double-report.

Cross-cutting *observations* (multi-dim patterns, not single facts) go in the
report's `## Cross-cutting observations` section, separate from the findings table.

---

## Primary-dim rule

Each finding has exactly ONE primary dim — the dim where the **fix lives**. If a missing
guard in `subprocess.run` is both a Correctness issue (silent breakage) and a Security
issue (command injection surface), the primary dim is whichever owns the fix:

- "Add `shell=False` and validate input" → `security` primary.
- "Restore the `if not user_input:` guard removed in this diff" → `correctness` primary.

This is the auditor's call during dedupe. Cross-cutting patterns get one row in the
cross-cutting section instead of N rows in the table.

---

## IO examples

### Example 1 — Golden path (behaviour-changing PR with security surface)

**Input.** User has staged a PR adding a new shell-out for git tag rollback. The diff
introduces `subprocess.run([...], shell=True)` and removes a guard on user-supplied
input. User invokes `/audit-diff` (defaults: `scope=all depth=major+`).

**What happens.**
1. `scripts/surface_detect.py` scans the diff and emits:
   ```json
   [
     {"dim": "security", "trigger": "subprocess.", "file": "src/release/rollback.py", "line": 42},
     {"dim": "correctness", "trigger": "removed_guard", "file": "src/release/rollback.py", "line": 38}
   ]
   ```
2. The auditor (fresh ctx) loads `coordinator_brief.md`, GUIDELINES.md, CLAUDE.md, and
   walks the 6 CORE dims. Silent-breakage sweep in `correctness` catches the removed
   guard.
3. Because the `security` trigger fired, the auditor performs a focused security pass
   (the runtime decides whether this is a separate fresh-context sub-agent dispatch or a
   single-pass focused walk; either preserves the framework).
4. The focused security pass flags `shell=True` + unsanitised input as a blocker. The
   auditor merges findings, applies primary-dim rule: removed-guard finding gets
   `correctness` primary, `shell=True` gets `security` primary.
5. Final report includes both findings, plus N/A justifications for `performance`,
   `observability`, `interface`, `dependency` (no surface in diff).

**Output.** Markdown report following `scripts/report_template.md`. Verdict: **Request
changes** (one blocker).

### Example 2 — Edge: targeted subset

**Input.** `/audit-diff scope=dims=tests depth=all`. User wants a deep test-quality
review only.

**What happens.**
1. `surface_detect.py` runs but its output is filtered to listed dims (or ignored — only
   `tests` matters).
2. The auditor walks only the `tests` dim, deep mode. No extra context-aware passes (Test
   quality is CORE; per-trigger context-aware passes do not apply).
3. Other 10 dims marked `N/A (scope excluded)` in the report. Findings table contains
   only test-quality findings.

**Output.** Report shape preserved. `## Per-dimension N/A justifications` lists the 10
excluded dims with `scope excluded` as the reason. `## What I did NOT check and why`
explicitly names the trade-off.

### Example 3 — Edge: no surface (pure docs PR)

**Input.** PR updates `README.md` and `docs/adr/0007-cache-strategy.md`. No code
changes. User invokes `/audit-diff`.

**What happens.**
1. `surface_detect.py` returns `[]` — no triggers fire.
2. The auditor walks 6 CORE dims, but most pass trivially. `docs` dim does the real
   work: ADR status field correct? CHANGELOG entry? cross-references valid?
3. No context-aware focused passes triggered. All five context-aware dims marked `N/A
   because no surface in diff`, with trigger lists noted.
4. The audit finishes fast.

**Output.** Report with verdict likely **Approve** or **Approve with nits**. Findings
table possibly empty; N/A section lists all five context-aware dims with their
considered-and-rejected trigger lists.

---

## Concrete output shape

The auditor writes to `scripts/report_template.md`'s structure. The template
has two modes (COMPACT for ≤2 findings with no blockers; FULL otherwise); see
the template comments for the split. The stub below is the **FULL** form
(two blockers present):

```markdown
## Verdict
Request changes

## Executive summary
Two blockers: an unvalidated shell-out and a removed input guard. One major nit on
CHANGELOG format. Behaviour-changing PR; this gate must pass before merge.

## Findings table
| ID | Primary dim | Severity | File:Line                       | Finding                                                       | Suggested fix                                              |
|----|-------------|----------|---------------------------------|---------------------------------------------------------------|------------------------------------------------------------|
| F1 | security    | blocker  | src/release/rollback.py:42      | `subprocess.run(..., shell=True)` with user-supplied tag name | Set `shell=False`, pass argv list, validate tag via regex. |
| F2 | correctness | blocker  | src/release/rollback.py:38      | Removed guard against empty tag name (silent breakage).       | Restore `if not tag: raise ValueError(...)`.               |
| F3 | docs        | major    | CHANGELOG.md:8                  | `[Unreleased]` entry verb says "Added", but the diff is a bug fix in rollback. | Move entry to `Fixed` and rewrite to describe the fix.     |

## Cross-cutting observations
- The rollback path lacks any tests for the new shell-out branch; this would have caught
  F1 and F2 together. Primary fix lives under `tests`, but the gap is visible from
  `correctness` and `security` simultaneously.

## Per-dimension N/A justifications
- performance: N/A because no surface in diff (no hot-path change, no DB query, no
  sync-in-async, no removed index, no new external call).
- observability: N/A because no surface in diff (no failure-path change, no log-level
  change, no metric drift).
- interface: N/A because no surface in diff (no public symbol removed/renamed, no
  default kwarg semantics change).
- dependency: N/A because no surface in diff (`pyproject.toml` untouched).

## What I did NOT check and why
- Did not run the test suite (audit is static).
- Did not evaluate the upstream `git` CLI version contract — assumed stable.
- Did not check for race conditions across concurrent rollbacks — out of single-file
  diff scope; flagged for follow-up.

## What's done well
- The `RollbackContext` dataclass cleanly separates rollback state from the CLI entry
  point — good single-responsibility boundary.

## Open questions
- Is the empty-tag path supposed to no-op or raise? The removed guard suggests intent
  changed; please clarify before fixing F2.
```

---

## Files in this skill

```
audit-runner/
├── SKILL.md                       # this file — when/why/framework spec
├── scripts/
│   ├── coordinator_brief.md       # operational handbook for whoever runs the audit
│   ├── surface_detect.py          # diff scanner → JSON trigger list
│   └── report_template.md         # output structure the auditor fills in
└── dimensions/                    # per-dim checklists (loaded as needed)
    ├── correctness.md
    ├── design.md
    ├── conventions.md
    ├── tests.md
    ├── docs.md
    ├── ci.md
    ├── security.md
    ├── performance.md
    ├── observability.md
    ├── interface.md
    └── dependency.md
```

## Recommended workflow when invoked manually or by the model

The runtime handbook (step-by-step procedure) lives in `scripts/coordinator_brief.md`.
The shell pattern that produces the trigger list, then loads everything the auditor
needs:

```bash
# Produce the trigger list from the staged diff (or a passed --diff-file):
git diff --staged | python3 scripts/surface_detect.py > /tmp/audit_triggers.json

# Then load into the audit pass (fresh context):
#   scripts/coordinator_brief.md, the diff, /tmp/audit_triggers.json,
#   the project brief (GUIDELINES.md / CLAUDE.md / DESIGN.md), and mode flags.
```

This file is the *contract* — framework, modes, output shape, meta-principles.
`scripts/coordinator_brief.md` is the operational handbook the auditor loads at
the start of a pass.
