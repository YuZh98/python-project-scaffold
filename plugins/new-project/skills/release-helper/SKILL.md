---
name: release-helper
description: >
  Invoke for /release, "cut a release", "ship vX.Y.Z", "tag and push a release",
  "publish version X.Y.Z", or any request to perform the release sequence on an
  existing Python project that follows Keep-a-Changelog. Rotates [Unreleased] →
  versioned section, commits, annotated-tags, pushes, then bumps pyproject metadata
  to the next dev cycle. Use this — not ad-hoc git commands — whenever the user
  wants to release, even if they don't say "skill". For existing projects being
  released, not /new-project scaffolding. Skip for: non-Python projects without
  pyproject.toml, projects without a Keep-a-Changelog CHANGELOG.md, or pre-release
  / RC / alpha / beta tags (this skill handles final vX.Y.Z releases only).
---

# release-helper

Orchestrator for the release sequence defined in `~/.claude/CLAUDE.md` §9. Mechanics
live in `scripts/release.sh`; this file describes WHEN to invoke, WHY each step matters,
the ORDER of operations, and what to do on failure.

Why one skill (not three): the tag, the changelog rotation, and the push must land
atomically from the reader's POV. Splitting them across separate invocations invites
drift — a tag pointing at a commit whose changelog still says `[Unreleased]`, or a
changelog rotated locally but never pushed. The script enforces the order; this skill
enforces the gate before the script runs.

## Trigger examples

"release v1.2.0" · "cut release 1.2.0" · "ship version 1.2.0" · "do the release for v1.2.0" ·
"tag and push v1.2.0" · "publish 1.2.0" · `/release v1.2.0` · `/release-helper 1.2.0`

## When NOT to trigger

- The user is editing the CHANGELOG without releasing → use `changelog-normalizer` instead.
- Pre-release / RC / alpha / beta versions (`1.2.0rc1`, `1.2.0-beta`) — this skill is for
  final releases. Reject with a one-line message.
- No `pyproject.toml` at the repo root.
- No `CHANGELOG.md` with a `## [Unreleased]` heading.

## Drift policy

If the request diverges from the trigger examples — non-Python project, non-Keep-a-Changelog
format, pre-release version, in-place rewrite without tag/push — **stop and ask the user
to confirm before running the script**. The script makes pushed-to-origin changes; a wrong
release is harder to undo than a wrong scaffold. Specifically:

- **Non-standard branch** (anything outside `main`, `master`, `release/*`): ask before
  passing `--allow-branch`. Standard release branches are the default for a reason.
- **Already-tagged version**: refuse hard. Do not offer to delete the tag — the user must
  do that explicitly and re-invoke.
- **Empty `[Unreleased]`**: refuse with the message below. Do not invent entries.

The cost of a false refusal is one re-invoke; the cost of a wrong release is a force-push
debate on a shared branch.

## Composition: changelog-normalizer (pre-step)

Before rotating `[Unreleased]`, invoke the `changelog-normalizer` skill (same plugin,
sibling directory) on `CHANGELOG.md` as a pre-step. The normalizer enforces the project's
Keep-a-Changelog style (bullet voice, subheading order, PR-number suffix). Releasing
without normalizing bakes drift into the historical record.

The invocation is in prose intentionally — the exact runtime form varies by harness, so
this skill describes WHAT to compose rather than HOW. Hand control to whatever mechanism
the current runtime uses to load a sibling skill, then return here.

If `changelog-normalizer` is not installed (plugin partial install, peer skill not yet
released), warn the user and offer to proceed without normalization. Do not silently
skip — the user should know the artifact may not match house style. Suggested phrasing:

> "`changelog-normalizer` skill not found. The release will still work, but
> `[Unreleased]` entries won't be style-checked first. Proceed anyway? (y/N)"

## Inputs

Three inputs, one required:

1. **Version string** (required) — `vX.Y.Z` or `X.Y.Z`. Validated against the regex
   `^v?[0-9]+\.[0-9]+\.[0-9]+$`. The script normalizes both forms internally so you
   can pass whichever the user typed.
2. **`--dry-run`** (optional) — print proposed diff and the commands that *would* run,
   change nothing. Use this on the first invoke if the user seems uncertain, or if the
   version string is ambiguous.
3. **`--allow-branch`** (optional, escape hatch) — bypass the main/master/release/*
   branch check. Use only after explicit user confirmation.

If the user omits the version, ask: *"What version are you cutting? (e.g. `v1.2.0`)"*.
Do not guess from the changelog or git tags — that's how off-by-one releases happen.

## Execution order

```bash
bash scripts/release.sh --check "$VERSION"       # 1. preflight (no writes)
# 2. invoke the changelog-normalizer skill on CHANGELOG.md (see composition section)
bash scripts/release.sh --dry-run "$VERSION"     # 3. show proposed rotation diff
# 4. ASK CONFIRMATION — proceed only on y/Y/yes/Enter
bash scripts/release.sh "$VERSION"               # 5. execute
```

Pass `--allow-branch` only after the user explicitly confirms a non-standard branch.

Push is the explicit ask of this skill — the universal "don't push unless asked" rule
does not apply here. The user invoked the release skill; that is the ask.

No `--no-verify`, no GPG override. The script inherits the user's `commit.gpgsign` /
`tag.gpgsign` config; it never overrides git config. Do not add `Co-Authored-By: Claude`
to the release or version-bump commits — release commits are public artifacts.

## IO examples

**1. Golden path** — clean repo on `main`, `[Unreleased]` has 3 entries, version not tagged:

```
> release v1.2.0

Preflight checks: ok
  - branch: main
  - tree: clean
  - tag v1.2.0: does not exist
  - CHANGELOG.md: 3 entries under [Unreleased]

Running changelog-normalizer on CHANGELOG.md... ok (no changes needed)

Proposed rotation:
  - ## [Unreleased]               →  ## [1.2.0] - 2026-05-14
  + (fresh ## [Unreleased] with 6 empty subheadings above the new versioned section)

Commands that will run:
  git add CHANGELOG.md
  git commit -m "chore: release v1.2.0"
  git tag -a v1.2.0 -m "Release v1.2.0"
  git push && git push --tags
  # (then version bump)
  python: pyproject.toml version 1.2.0 → 1.2.1.dev0
  git add pyproject.toml
  git commit -m "chore: bump version to 1.2.1.dev0"
  git push

Proceed? (y/N): y

Released v1.2.0 (commit a1b2c3d, tag v1.2.0 pushed).
Follow-up bump: commit e4f5g6h pushed.
```

**2. Edge — empty `[Unreleased]`**: heading exists, only HTML comments and bare subheadings
below it (`### Added` with no bullets):

```
> release v1.2.0

release: nothing to release. [Unreleased] in CHANGELOG.md has no entries.
        Add bullets under one of: Added, Changed, Fixed, Removed, Deprecated, Security.
        Then re-invoke.

(no changes made)
```

**3. Edge — dirty working tree**:

```
> release v1.2.0

release: working tree dirty. Commit or stash before releasing.
         (run `git status` to see what.)

(no changes made)
```

**4. Edge — dry-run, version with v-prefix**:

```
> release v1.2.0 --dry-run

[dry-run] would rotate ## [Unreleased] → ## [1.2.0] - 2026-05-14
[dry-run] would commit:  chore: release v1.2.0
[dry-run] would tag:     v1.2.0 (annotated, message "Release v1.2.0")
[dry-run] would push:    git push && git push --tags
[dry-run] would bump:    pyproject.toml 1.2.0 → 1.2.1.dev0
[dry-run] would commit:  chore: bump version to 1.2.1.dev0
[dry-run] would push:    git push

(no changes made)
```

**5. Drift — non-standard branch**: user is on `feature/auth-refactor` and asks to release.
Ask explicitly: *"You're on `feature/auth-refactor`, not a release branch (`main`,
`master`, `release/*`). Releasing from feature branches is unusual. Proceed with
`--allow-branch`? (y/N)"* — do not pass `--allow-branch` without an explicit yes.

**6. Drift — pre-release version**: `release v1.2.0rc1` → refuse. *"This skill is for
final releases (vX.Y.Z). Pre-release tagging is out of scope; use `git tag` directly."*

## Concrete output examples

Golden-path final output (verbatim excerpt from IO example 1 above):

```
Released v1.2.0 (commit a1b2c3d, tag v1.2.0 pushed).
Follow-up bump: commit e4f5g6h pushed.
```

Dry-run output is a sequence of `[dry-run]` lines describing each proposed mutation,
terminated by `(no changes made)` — see IO example 4. Refusals print the failure reason
on stderr followed by `(no changes made)` (IO examples 2-3); no commit, tag, or push is
ever produced on a refusal path. Pass refusal messages through verbatim — they are the
script's contract with the user.

## Refuse conditions

The script refuses (exit non-zero, no state changed) on any of: dirty working tree,
detached HEAD, non-release branch without `--allow-branch`, malformed version
(`^v?[0-9]+\.[0-9]+\.[0-9]+$`), tag already exists locally or on origin, missing
`CHANGELOG.md` or `## [Unreleased]` heading, zero bullet entries under `[Unreleased]`,
missing `pyproject.toml`, or `pyproject.toml` version mismatch at the bump step.

Each refusal prints the failure reason and the recovery action; IO examples 2-3 and 5-6
show the exact wording for the four most common paths.

## On failure

- **Preflight fails** → message on stderr, exit. No state changed. Address and re-invoke.
- **Normalizer fails / is absent** → warn the user; offer to proceed (release still works,
  it just won't enforce changelog style).
- **Rotation succeeds but commit fails** (pre-commit hook rejects, etc.) → `CHANGELOG.md`
  is modified on disk but not committed. The script leaves it. Do not run `git checkout`
  automatically — the user may want to inspect the rotation. Print the recovery command:
  *"To abandon the rotation: `git checkout CHANGELOG.md`. To retry: fix the issue and
  re-invoke release-helper."*
- **Tag succeeds but push fails** (network, auth, branch protection) → commit and tag
  exist locally. Print: *"Local commit and tag created. Push failed: <reason>. To retry:
  `git push && git push --tags` once resolved."* Do not auto-retry — auth or branch
  protection issues need a human.
- **Version bump fails** → primary release is already pushed and is the irreversible
  part; the dev-cycle bump can be done by hand. Print: *"Release v1.2.0 is live. The
  follow-up version bump failed: <reason>. To retry by hand: edit `pyproject.toml`
  version to `1.2.1.dev0`, then `git commit -am 'chore: bump version to 1.2.1.dev0' &&
  git push`."*

## Do not

- Auto-delete a pre-existing tag to "make room" for the release. Destructive; the user
  must do it explicitly and re-invoke.
- Push amended commits over a published tag.
- Invent `[Unreleased]` entries to make an empty-changelog release work. Refuse instead.

(The `--no-verify`, GPG-override, and `Co-Authored-By: Claude` prohibitions are stated
once under Execution order — they are not repeated here.)
