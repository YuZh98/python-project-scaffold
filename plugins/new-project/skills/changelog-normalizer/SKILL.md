---
name: changelog-normalizer
description: >
  Invoke for any request to normalize, clean up, reformat, lint, fix, or check the style
  of a CHANGELOG.md file. Trigger on "normalize changelog", "fix changelog format", "clean
  up CHANGELOG entries", "check changelog style", "make the changelog consistent", "lint
  CHANGELOG.md", or `/changelog-normalize`. Use this — not freeform editing — whenever a
  CHANGELOG already exists and needs to conform to Keep-a-Changelog structure: canonical
  subheadings in spec order, commit/PR refs on every entry, no process narrative. Voice
  (imperative vs descriptive) is the author's choice — the skill validates structure and
  process-narrative content, not voice. Single responsibility: reformat existing entries.
  Does NOT invent, add, or remove changelog content. Skip for: writing release notes from
  scratch, summarizing commits into a new changelog, cutting a release / tagging a
  version / "release vX.Y.Z" / "ship X.Y.Z" (use `release-helper`, which composes this
  skill as its pre-step), or non-CHANGELOG markdown.
---

# changelog-normalizer

Reformats `CHANGELOG.md` to a single canonical Keep-a-Changelog 1.1.0 structure
(canonical subheadings in spec order, refs on every entry, no process narrative). Voice
in entries (imperative or descriptive) is the author's choice — the skill validates
structure and process-narrative content, not voice. The work is **format conformance**,
not content authoring. The skill never invents entries, never invents commit hashes or
PR numbers, and never silently picks a subheading for an ambiguous entry.

The bundled script (`scripts/normalize_changelog.py`) does the mechanical work; this file
exists to (a) tell the model when to use it, (b) make the style rules unmissable via
concrete BEFORE/AFTER examples, and (c) define the drift policy for ambiguous cases.

## Trigger examples

"normalize the changelog" · "fix changelog format" · "clean up CHANGELOG entries" ·
"check changelog style" · "make the changelog consistent" · "lint CHANGELOG.md" ·
"the changelog has drifted from Keep-a-Changelog" · `/changelog-normalize`

## When NOT to trigger

- Writing a new CHANGELOG.md from scratch — that's authoring, not normalizing.
- Generating release notes from commit history — different skill.
- Editing arbitrary markdown (README, ADRs, docs).
- Cutting a release, tagging a version, rotating `[Unreleased]` to `[X.Y.Z]` — that's
  `release-helper`, which **composes this skill** as its pre-step. If the user says
  "release vX.Y.Z" or "ship X.Y.Z", they want release-helper, not this skill.

## Drift policy (READ BEFORE EDITING)

The whole point of this skill is that the user has been burned by Claude silently picking
subheadings or fabricating refs across sessions. **The default for ambiguity is to ask,
not to guess.** Three concrete triggers stop the skill and surface a question:

1. **Ambiguous entry placement (`Fixed` vs `Changed`, or `Added` vs `Changed`).** "Make
   timeout configurable" could be a bug fix (the old timeout was broken) or an
   enhancement (it always worked but was inflexible). The script flags any `Changed`
   entry starting with an ambiguous verb (`make`, `expose`, `support`, `allow`, `enable`)
   as `ambiguous-subheading`. Ask the user; do not pick silently.
2. **Verb–section mismatch.** An entry starting `Fix X` under `### Changed`, or `Add X`
   under `### Fixed`, almost certainly belongs in the section its verb names. The script
   flags this as `verb-section-mismatch` but **does not auto-move** — the verb might be
   wrong instead of the section. Ask the user which way to fix it.
3. **Missing ref — NEVER fabricate.** If an entry has no `(#42)` or `(abc1234)` suffix,
   the script flags it as `missing-ref`. Ask the user for the PR or commit; if they say
   "no ref available", leave an inline `<!-- TODO: ref -->` (the script preserves these
   on subsequent runs). Inventing a plausible-looking ref poisons the changelog forever.

Same principle for unclear content: surface the original line verbatim and ask. Do not
paraphrase an ambiguous entry into something that *sounds* right.

If the user's overall request diverges from the trigger examples — e.g. they ask to
*generate* a changelog rather than normalize one — stop and confirm. A wrong refusal is
recoverable; a fabricated PR ref is not.

## Structural rules (script-enforced)

The script applies these mechanically — the examples below show each in context.

1. **Format**: Keep-a-Changelog, `## [Unreleased]` always at the top.
2. **Subheadings, in this exact order, only those present**:
   `### Added` · `### Changed` · `### Deprecated` · `### Removed` · `### Fixed` · `### Security`.
   Empty subheadings are dropped from released versions; `[Unreleased]` keeps them as
   workspace scaffolding for contributors.
3. **Entry format**: `- {Verb} {object}. ({commit-hash})` or `(#PR-number)`.
   The period comes before the ref — the ref is a parenthetical citation, not part of
   the sentence. Sentence-case capitalization; bullet symbol is `-` only (the script
   replaces `*`, `+`, `•`). Voice is your choice (imperative or descriptive) — the
   script does not rewrite verbs.
4. **Version header**: `## [X.Y.Z] - YYYY-MM-DD` for released, `## [Unreleased]` for
   pending. Versions sort descending (newest first), with `[Unreleased]` always on top.
5. **Link references** at the bottom of the file (`[Unreleased]: https://...`) are
   preserved verbatim. The script does not rewrite or invent them.
6. **Process narrative auto-strip** — phrases like `per audit pass`, `re-audit`,
   `review iteration`, `per agent feedback`, `per AI review`, and any `Co-Authored-By:`
   line referencing an AI assistant are removed silently. This is the privacy/hygiene
   rule the script enforces non-negotiably; do not ask.
7. **Candidate duplicates** within a section are flagged for human merge (keep the
   more specific phrasing; if neither is more specific, ask). Never auto-merge.

## Content rules (judgment — model-enforced)

- **WHAT changes and WHY it matters, not HOW.** Skip file paths, step numbers,
  implementation details.
  - Poor: `Step 5: replaced cd with git -C in the license-amend block.`
  - Good: `Fix license rewrite silently failing when shell cwd doesn't persist.`
- Group related changes into one bullet at the user-impact level.
- Each version section opens with a **one-sentence summary** of what the release is
  about, before any `###` subheading. Recommended by Keep-a-Changelog convention
  (this rule was previously pinned by `template/tests/test_cohesion.py` but was
  demoted to a recommendation in v1.8.0 — see CHANGELOG and the template's own
  `CHANGELOG.md` HTML comment).
- Do not overuse bolding (`**text**`) — reserve it for genuine emphasis (e.g.
  `**BREAKING**:` prefix on breaking-change entries).

## Release-time rotation (called by release-helper)

When `release-helper` invokes this skill as its pre-step, the workflow is:

1. Normalize entries under `[Unreleased]` (this skill's normal mode).
2. `release-helper` then rotates the `[Unreleased]` block to `## [vX.Y.Z] - YYYY-MM-DD`,
   re-adds an empty `[Unreleased]` above it with the six standard subheadings, and drops
   any subheadings that ended up empty in the just-released block.

The rotation itself lives in `release-helper`, not here — this skill's contract is
format conformance only. If invoked directly by the user (no release in progress),
leave the empty `[Unreleased]` scaffolding intact; contributors add bullets under it as
work lands.

## How to run the script

Default: in-place rewrite with a `.bak` backup next to the file.

```bash
python3 scripts/normalize_changelog.py CHANGELOG.md           # rewrite + .bak
python3 scripts/normalize_changelog.py CHANGELOG.md --check   # CI mode: exit 1 on issues
python3 scripts/normalize_changelog.py CHANGELOG.md --diff    # show proposed diff, no write
```

The script writes ambiguous-case warnings to stderr with line numbers and exits non-zero
in `--check` mode if any rule is violated. In default mode it applies the unambiguous
fixes, then prints the warnings — the model surfaces those warnings to the user and
collects answers before re-running.

## Workflow

The default for a clean CHANGELOG is to exit quickly without ceremony. Most invocations
land on a CHANGELOG that's already conformant — running the full ask-loop on every one
of those is the difference between this skill feeling like a 5-second sanity check and
feeling like a 2-minute ordeal.

1. **Run `--check` first.** This is cheap (<100 ms on real CHANGELOGs).
2. **Fast-path: clean CHANGELOG → stop.** If `--check` returns exit code 0 (no
   warnings, no content changes needed) AND a model-judgment scan of the file shows
   no Content-rule violations from the section above (multi-sentence bullets,
   file-path leaks in entries, marketing-tone summary, glued-distinct-changes), report
   "CHANGELOG is clean — no normalization needed" and stop. **Do not narrate the
   workflow steps you did not take.**
3. **Issues found → enumerate, then ask in one batch.** If `--check` surfaces
   ambiguous cases and missing refs, ask the user about all of them together
   (one `AskUserQuestion` call with multiple questions, or a single message
   listing them numbered). Surface each original line verbatim; never paraphrase
   ambiguous text into something that "sounds right".
4. **Missing-ref policy.** If the user says "no ref available" for any entry, leave
   it unreferenced with an inline `<!-- TODO: ref -->` comment — the script
   preserves these on subsequent runs. **Never fabricate a plausible-looking ref.**
5. **Apply.** Edit the file with the user's answers, then run the script in default
   mode to apply mechanical fixes. Show the resulting diff and the `.bak` location
   in one message, not three.

## Concrete output examples

These verbatim excerpts from production CHANGELOGs anchor "what good output looks like."

### Example A — before/after revision (scaffold v1.8.0)

The drift patterns this skill exists to catch are easiest to see side by side. Both blocks below are real: the BEFORE shipped in `python-project-scaffold` commit `68fdfdc` (the initial v1.8.0 release commit) and was flagged by the author as drifted; the AFTER shipped in commit `ec6c0bb` (`docs: revise v1.8.0 CHANGELOG entries to match canonical style`).

**BEFORE** — drifted:

```markdown
## [v1.8.0] - 2026-05-15

The scaffold ships a Claude Code plugin (`plugins/new-project/`) bundling the new-project skill plus three sibling skills (release-helper, changelog-normalizer, audit-runner) via a self-hosted marketplace. Scaffold-level defaults rebalance toward universality: coverage threshold drops from 95% to 80%, imperative-mood and ADR-for-decisions rules demoted from required to recommended, and the cohesion test no longer enforces summary-paragraph style.

### Added
- Claude Code plugin (`plugins/new-project/`) packaging the scaffold's existing skill plus three sibling skills (release-helper, changelog-normalizer, audit-runner). Distributed via self-hosted marketplace at `.claude-plugin/marketplace.json`. See ADR 0001 for the decoupled-versioning rationale. (64e6db5)

### Changed
- Template default coverage threshold lowered from 95% to 80%. Projects bootstrapped from the scaffold now inherit the conservative default with a comment suggesting they raise it as the project stabilizes. Existing bootstrapped projects are unaffected. (#22)
- Template `tests/test_cohesion.py` no longer pins summary-paragraph-before-bullets in CHANGELOG versioned sections. Demoted to a recommendation in the template's `CHANGELOG.md` HTML comment. (#22)
- Template docs no longer prescribe imperative mood in commit messages or changelog entries. Conventional-commits prefix list demoted from "must use these types" to "common examples". (#22)
- ADR-for-hard-to-reverse-decisions wording changed from "required" to "strongly recommended" across template docs. (#22)

### Security
- Internal-process docs (`docs/superpowers/`, `docs/dev-notes/`, session logs) added to `.gitignore` for both scaffold and template. Closes a violation of CLAUDE.md §8 ("Internal-process docs are gitignored and never committed") that v0.1.0 inadvertently shipped. (#21)
```

**AFTER** — canonical:

```markdown
## [v1.8.0] - 2026-05-15

Scaffold now ships as a Claude Code plugin bundling the new-project skill alongside release-helper, changelog-normalizer, and audit-runner. Template-side defaults also relax: coverage threshold drops from 95% to 80%, and the imperative-mood, ADR-for-decisions, and summary-paragraph rules are demoted from required to recommended.

### Added
- Claude Code plugin (`plugins/new-project/`) bundling the new-project skill alongside release-helper, changelog-normalizer, and audit-runner; distributed via a self-hosted marketplace. (64e6db5)

### Changed
- Template default coverage threshold lowered from 95% to 80% — conservative starting point with a comment suggesting projects raise it as they stabilize. (#22)
- Summary-paragraph-before-bullets rule in template CHANGELOG sections demoted from pinning test to recommendation in the comment block. (#22)
- Imperative-mood requirement on commit messages and changelog entries dropped as taste-pinning. (#22)
- Conventional Commits prefix list demoted from "must use these types" to "common examples". (#22)
- ADR-for-hard-to-reverse-decisions wording softened from "required" to "strongly recommended" across template docs. (#22)

### Security
- Internal-process docs (`docs/superpowers/`, `docs/dev-notes/`, session logs) added to `.gitignore` for both scaffold and template, closing a CLAUDE.md §8 violation that v0.1.0 inadvertently shipped. (#21)
```

**Drift patterns fixed (study these — they recur):**

1. **Multi-sentence bullets compressed to one sentence.** Every BEFORE bullet under `### Added` and `### Changed` ran two or three sentences; AFTER bullets are one sentence each with the period right before the ref. Join clauses with `—`, `;`, or `,` instead of starting a new sentence.
2. **Implementation paths stripped from bullets.** BEFORE leaked HOW: `.claude-plugin/marketplace.json`, `tests/test_cohesion.py`, "Conventional-commits prefix list demoted from ... to ...". AFTER keeps the user-visible artifact (`plugins/new-project/`) but drops file paths that read as code spelunking.
3. **Meta-pointers dropped.** "See ADR 0001 for the decoupled-versioning rationale" is a reference for someone who already cares about the architecture; not changelog material. AFTER removes it.
4. **Self-justification framing dropped.** BEFORE's "Closes a violation of CLAUDE.md §8 ('Internal-process docs are gitignored and never committed') that v0.1.0 inadvertently shipped" is process narrative. AFTER says the same thing as a clause: "closing a CLAUDE.md §8 violation that v0.1.0 inadvertently shipped" — no scare quotes around the rule text.
5. **Distinct changes split into separate bullets.** BEFORE glued "imperative-mood demotion" + "Conventional Commits prefix-list demotion" into one bullet because they happened in the same commit. AFTER splits them — they're independent user-facing changes.
6. **Marketing-tone summary rewritten as declarative.** BEFORE: "Scaffold-level defaults rebalance toward universality" (corporate voice). AFTER: "Template-side defaults also relax" (plain). The summary states what shipped; it doesn't editorialize about the design philosophy.

### Example B — small release with Added + Changed

From `python-project-scaffold/CHANGELOG.md` v1.7.6:

```markdown
## [v1.7.6] - 2026-05-13

The skill can now be installed with a single command. CI automatically builds a `.skill` zip file and attaches it to every GitHub Release on tag push — no manual packaging step needed.

### Added
- CI workflow that builds and uploads `new-project.skill` to GitHub Releases on every version tag. (#15)

### Changed
- README install instructions updated to use `gh release download --latest`. (#15)
```

### Example C — concise refactor entry

From `python-project-scaffold/CHANGELOG.md` v1.7.5:

```markdown
## [v1.7.5] - 2026-05-13

Skill cut from 452 to 212 lines. License texts moved to a bundled helper script that loads only when needed; several redundant sections removed.

### Changed
- Skill condensed 53%; license texts extracted to `scripts/write_license.py`. (#14)
```

### What these examples illustrate

- One-sentence summary leads each version, explaining what the release is *about* in user-impact terms
- Entries say WHAT changed and WHY it matters; HOW (file paths, step numbers) is omitted
- Each entry ends with `(#PR)` or `(commit-hash)` in parens
- No process narrative, no AI-attribution `Co-Authored-By:` lines, no bolding overuse
- Voice (imperative or descriptive) is the author's choice — the examples here use a mix and both are fine

### Reference link (additional canonical examples)

- `https://github.com/YuZh98/python-project-scaffold/blob/main/CHANGELOG.md?plain=1`
- `https://github.com/YuZh98/latex2arxiv/blob/main/CHANGELOG.md?plain=1`

These stay current as the linked CHANGELOGs evolve. For patterns not covered by Examples A-C, point the user at the relevant section of these files.

## IO examples

**Golden path** — *"normalize the changelog at ./CHANGELOG.md"*:

1. Run `python3 scripts/normalize_changelog.py CHANGELOG.md --check`.
2. Script prints to stderr: `4 mechanical fixes available · 2 ambiguous · 3 missing refs`.
3. Model surfaces the 2 ambiguous cases and 3 missing-ref cases to user, one at a time.
4. User answers; model edits the file with answers.
5. Model runs the script in default mode → `CHANGELOG.md.bak` created, mechanical fixes applied.
6. Model shows the user the resulting diff.

**Edge — `--check` mode for CI** — *"add a CI step that fails on changelog drift"*:

Run `python3 scripts/normalize_changelog.py CHANGELOG.md --check`. Exit 0 means clean,
exit 1 means at least one issue. CI fails fast; no file is modified.

**Edge — process narrative auto-strip** — entry contains "per Claude audit pass": the
script strips the phrase automatically (it's unambiguous — the rule says no AI mentions,
period). The model does NOT ask. The before/after of the stripped phrase is shown in the
diff so the user can verify.

**Drift — user asks to generate a changelog from commits** — *"build me a changelog from
the last 50 commits"*. This is authoring, not normalizing. Stop and confirm: "This skill
only reformats existing CHANGELOG entries. Generating new entries from commit history is
out of scope. Do you want to (a) write a draft yourself and have me normalize it, or
(b) handle this without the skill?"

## Do not

- Fabricate commit hashes or PR numbers under any circumstances.
- Silently pick between subheadings for ambiguous entries.
- Rewrite link references at the bottom of the file.
- Touch any markdown file other than the changelog the user named.
- Add `Co-Authored-By: Claude` to any commit that comes out of this work.
- Bundle "while you're at it" changes (version bumps, release-cut steps) — single
  responsibility is the whole point.

## On failure

- **Script exits non-zero in default mode** → the `.bak` was written before any edit; the
  original is recoverable as `CHANGELOG.md.bak`. Read the stderr message and ask the user.
- **Ambiguous case the user can't resolve** → leave an inline HTML comment
  `<!-- TODO: classify this entry -->` and continue. The script preserves these on
  subsequent runs.
- **Script reports a parse error** (e.g. a version header it can't recognize) → do NOT
  attempt manual surgery. Surface the line to the user and ask whether the file's
  structure should be migrated (separate concern) before normalization continues.
