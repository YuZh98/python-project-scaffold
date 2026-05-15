---
name: new-project
description: >
  Invoke for /new-project or any request to create, start, scaffold, bootstrap, initialize,
  or spin up a new Python project or Python GitHub repository from scratch. Use this — not
  general coding — when the user wants a fresh Python repo that doesn't exist yet, with or
  without mentioning specific tooling. Automates GitHub repo creation, linting, testing,
  type checking, pre-commit hooks, and coverage in one step. Skip for: existing projects,
  non-Python languages, or questions about what templates contain.
---

# new-project

Thin orchestrator around the `python-project-scaffold` toolchain. Ask four questions, then
run the bundled scripts in order. Mechanics live in `scripts/`.

## Trigger examples

"create a new Python project" · "scaffold a python repo" · "bootstrap python library" ·
"start a fresh python project" · "spin up a new repo for a CLI tool" · `/new-project`

**Dry-run triggers:** `--dry-run`, "preview only", "show me what would happen", "simulate it".
Set `DRY_RUN=1` at invocation. Local scaffold tree still gets created (network clone runs);
license-amend and GitHub push are skipped. Print `[DRY-RUN] No remote actions taken.` at end.

## When NOT to trigger

Existing project (cwd already a git checkout) · non-Python language (Rust/Go/JS) ·
questions about what the scaffold ships.

## Drift policy

If the request diverges from the trigger examples — different language, in-place
modification, partial scaffold — **stop and ask before running any script**. Do not
extrapolate: a wrong scaffold writes to disk and may push to the wrong GitHub account.

## The four questions

Ask one at a time, re-prompt on invalid input. Store as `NAME`, `DESC`, `VISIBILITY`,
`LICENSE_ID`. Python floor (3.11) is a silent default.

1. **Project name** — lowercase letters/digits/hyphens, start+end alphanumeric.
2. **Description** — one-line summary.
3. **Visibility** — `private` (default) or `public`.
4. **License** — `MIT` (default), `Apache-2.0`, `BSD-3-Clause`, or `Unlicense`.

Before running anything, print a one-screen summary (name, target dir, github account,
license, visibility, author) and accept `y`/`Y`/`yes`/Enter to proceed.

## Execution order

```bash
# 1. Preflight checks (refuses if cwd is inside git, gh unauthenticated, deps missing).
bash scripts/preflight.sh

# 2. Clone scaffold at pinned tag, run init-project, make the initial commit.
bash scripts/bootstrap.sh "$NAME" "$DESC" "$LICENSE_ID"

# 3. Rewrite LICENSE for non-MIT and amend into the bootstrap commit.
#    Skipped under DRY_RUN.
if [[ -z "${DRY_RUN:-}" && "$LICENSE_ID" != "MIT" ]]; then
  TARGET="$(pwd)/$NAME"
  python3 scripts/write_license.py \
    "$LICENSE_ID" "$(date +%Y)" "$(git config --global user.name)" \
    > "$TARGET/LICENSE"
  git -C "$TARGET" add LICENSE && git -C "$TARGET" commit --amend --no-edit
fi

# 4. Create gh repo, push, enable branch protection. Skipped under DRY_RUN.
if [[ -z "${DRY_RUN:-}" ]]; then
  bash scripts/finalize.sh "$NAME" "$VISIBILITY" "$DESC"
else
  echo "[DRY-RUN] No remote actions taken. Local scaffold at $(pwd)/$NAME"
fi
```

Each script exits non-zero on failure; propagate and stop.

## IO examples

**Golden path** — *"scaffold audit-tools, MIT, public, 'Audit helpers for SOC2'"* →

```
✓ Preflight: gh authenticated as alice, cwd outside git.
✓ Bootstrap: /Users/alice/audit-tools created (init-project ran clean).
✓ Finalize: pushed to github.com/alice/audit-tools, branch protection enabled.

Next: cd audit-tools && make test   (your green baseline)
```

**Edge — inside a git repo**: cwd is a git checkout → preflight refuses with
`refusing to run inside an existing git repo. cd to a parent directory and re-invoke.`
No directory created, no remote calls made.

**Edge — gh not authenticated**: `gh auth status` fails → preflight refuses with
`gh is not authenticated. Run 'gh auth login' (needs 'repo' scope), then retry.`
No directory created, no remote calls made.

**Drift — non-Python request**: *"scaffold a new Rust crate"* → ask the user to confirm
before doing anything. This skill is Python-only; refuse cleanly or hand off.

## Concrete output examples

**Dry-run** (`DRY_RUN=1`) — no `Finalize` line, no push, no branch-protection call:

```
✓ Preflight: gh authenticated as alice, cwd outside git.
✓ Bootstrap: /Users/alice/audit-tools created (init-project ran clean).
[DRY-RUN] No remote actions taken. Local scaffold at /Users/alice/audit-tools
```

**Refusal** — printed on stderr, exit non-zero, no target directory created, no scaffold
cloned, no network calls made. Same shape for all preflight refusals (in-git, gh
unauthenticated, target exists, scaffold version unreachable):

```
new-project: refusing to run inside an existing git repo.
             cd to a parent directory and re-invoke.
```

## Do not

- Add `Co-Authored-By: Claude` to any commit.
- Re-implement validation; `init-project.py` owns it.
- Insert commits between bootstrap and finalize (license amend is the sole exception).

## On failure

- **Preflight** → message on stderr, exit. No state changed.
- **Bootstrap** → leave partial `$TARGET` for inspection, exit.
- **License amend** → user runs `git add LICENSE && git commit --amend --no-edit` after fixing `$TARGET/LICENSE`.
- **Finalize** → local repo intact; print `gh repo create` + `git push` recovery commands.
