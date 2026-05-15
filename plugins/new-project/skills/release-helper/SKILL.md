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

Orchestrates one atomic release: rotate `[Unreleased]` → `[X.Y.Z]`, commit, annotated-tag,
push, then bump `pyproject.toml` to the next dev cycle. Mechanics live in
`scripts/release.sh`; this file covers WHEN to invoke, ORDER of operations, composition
with `changelog-normalizer`, and recovery on failure.

The tag, the changelog rotation, and the push must land together — a tag pointing at a
commit whose changelog still says `[Unreleased]` is the failure mode this skill prevents.

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
format, pre-release version, in-place rewrite without tag/push — stop and ask before
running the script. Specifically:

- **Non-standard branch** (anything outside `main`, `master`, `release/*`): ask before passing `--allow-branch`.
- **Already-tagged version**: refuse hard; do not offer to delete the tag.
- **Empty `[Unreleased]`**: refuse with the message below; do not invent entries.

Default for any other ambiguity is refuse + ask, not guess.

## Composition: changelog-normalizer (pre-step)

Before rotating `[Unreleased]`, invoke the sibling `changelog-normalizer` skill on
`CHANGELOG.md`. It enforces Keep-a-Changelog structure (subheading order, refs on every
entry, no process narrative); see its SKILL.md for the rules.

Hand control to the runtime's sibling-skill loader, then return here.

If `changelog-normalizer` is not installed, warn the user and offer to proceed without
normalization — do not silently skip. Suggested phrasing:

> "`changelog-normalizer` skill not found. The release will still work, but
> `[Unreleased]` entries won't be style-checked first. Proceed anyway? (y/N)"

## Inputs

1. **Version string** (required) — `vX.Y.Z` or `X.Y.Z`; matched against `^v?[0-9]+\.[0-9]+\.[0-9]+$`. The script normalizes both forms.
2. **`--dry-run`** (optional) — print proposed diff and would-run commands; change nothing.
3. **`--allow-branch`** (optional) — bypass the main/master/release/* branch check; pass only after explicit user confirmation.

If the user omits the version, ask: *"What version are you cutting? (e.g. `v1.2.0`)"*. Do not guess from the changelog or git tags.

## Execution order

```bash
bash scripts/release.sh --check "$VERSION"       # 1. preflight (no writes)
# 2. invoke the changelog-normalizer skill on CHANGELOG.md (see composition section)
bash scripts/release.sh --dry-run "$VERSION"     # 3. show proposed rotation diff
# 4. ASK CONFIRMATION — proceed only on y/Y/yes/Enter
bash scripts/release.sh "$VERSION"               # 5. execute
```

Pass `--allow-branch` only after explicit user confirmation of a non-standard branch.

Push is in scope here; do not gate it behind a separate "are you sure you want to push" prompt.

No `--no-verify`, no GPG override, no `Co-Authored-By: Claude` on release or version-bump commits.

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

Golden-path success (two lines, stdout):

```
Released v<VERSION> (commit <SHA>, tag v<VERSION> pushed).
Follow-up bump: commit <SHA> pushed.
```

Dry-run: a sequence of `[dry-run]` lines (one per proposed mutation) terminated by `(no changes made)`.

Refusal: failure reason on stderr, then `(no changes made)`; no commit, tag, or push is ever produced. Pass refusal messages through verbatim.

## Refuse conditions

The script is the authoritative list of refuse conditions; it exits non-zero with no state changed and prints the failure reason plus the recovery action. IO examples 2-3 and 5-6 show the wording for the four most common paths.

## On failure

- **Preflight fails** → message on stderr, exit; no state changed; address and re-invoke.
- **Normalizer fails / is absent** → warn the user and offer to proceed without it.
- **Rotation succeeds but commit fails** (pre-commit hook, etc.) → `CHANGELOG.md` is modified on disk but not committed; do not auto-`git checkout`. Print: *"To abandon the rotation: `git checkout CHANGELOG.md`. To retry: fix the issue and re-invoke release-helper."*
- **Tag succeeds but push fails** (network, auth, branch protection) → commit and tag exist locally; do not auto-retry. Print: *"Local commit and tag created. Push failed: <reason>. To retry: `git push && git push --tags` once resolved."*
- **Version bump fails** → release is already pushed and irreversible; the dev-cycle bump can be done by hand. Print: *"Release v1.2.0 is live. The follow-up version bump failed: <reason>. To retry by hand: edit `pyproject.toml` version to `1.2.1.dev0`, then `git commit -am 'chore: bump version to 1.2.1.dev0' && git push`."*

## Do not

- Auto-delete a pre-existing tag to "make room" for the release; the user must do it explicitly and re-invoke.
- Push amended commits over a published tag.
- Invent `[Unreleased]` entries to make an empty-changelog release work; refuse instead.
