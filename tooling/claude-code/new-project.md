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

# New-Project Skill

Goal: bootstrap a new Python project from `python-project-scaffold` and create a GitHub repo for it. The skill is a Claude Code-specific wrapper around the scaffold's own bootstrap engine (`scripts/init-project.py`) — it adds GitHub repo creation, branch protection, and Claude-style 3-question UX.

The scaffold itself is Claude-independent; if you want to bootstrap without this skill, see https://github.com/YuZh98/python-project-scaffold for the manual `python3 scripts/init-project.py` flow.

## When to invoke

Trigger this skill when the user wants to start a NEW project AND wants a GitHub repo created automatically. The user types `/new-project`, "scaffold new project", "bootstrap new repo", or "start a new python project".

REFUSE if the user is already inside an existing git repo (the skill creates a new directory below cwd).

For manual scaffold-only bootstrap without GitHub repo creation, point the user at the scaffold's `scripts/init-project.py` (see scaffold README) instead.

## Workflow

### Step 1 — Pre-flight

Run, in order:

```bash
gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first (needs 'repo' scope for repo creation and branch protection). If you have multiple accounts, switch with 'gh auth switch'."; exit 1; }
ACTIVE_GH_LOGIN=$(gh api user --jq .login)
[[ -n "$(git config --global user.name 2>/dev/null)" ]] || { echo "Configure git first: git config --global user.name '<name>' && git config --global user.email '<email>'"; exit 1; }
[[ -n "$(git config --global user.email 2>/dev/null)" ]] || { echo "Configure git first: git config --global user.email '<email>'"; exit 1; }
python3 --version >/dev/null 2>&1 || { echo "python3 is required but not found. Install Python 3.11+ and retry."; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && { echo "Refusing to run inside an existing git repo. cd to a parent directory and re-invoke."; exit 1; } || true
```

If any pre-flight fails, abort with the actionable message and do nothing.

### Step 2 — Ask the user 3 questions

Use `AskUserQuestion` if available; otherwise prompt sequentially. The 3 questions:

1. **Project name** — lowercase letters / digits / hyphens; start+end with a letter or digit. Example: `my-cool-tool`. On invalid input, re-prompt with: "Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit. Got: '<value>'. Try: my-cool-tool".
2. **One-line description**. Example: "Tool for managing X."
3. **Visibility**: `public` (default) or `private`.

DO NOT ask for license or Python floor here — the skill uses silent defaults (MIT license, Python 3.11 floor) and passes them directly to `init-project.py` in Step 5. The skill deliberately keeps its prompts to 3.

### Step 3 — Show derived-values summary BEFORE clone

Compute these derived values (without calling init-project.py — these are the bits the skill needs for the GitHub URL):

```bash
SCAFFOLD_VERSION="v1.7.1"
PACKAGE_NAME=$(echo "$NAME" | tr '-' '_')                       # snake_case
PROJECT_TITLE=$(echo "$NAME" | tr '-' ' ' | python3 -c "import sys; print(sys.stdin.read().strip().title())")
TARGET="$(pwd)/$NAME"
```

Then print a summary table:

```
─────────────────────────────────────────────
Pre-clone summary — please review

  Project name      $NAME
  Project title     $PROJECT_TITLE
  Package name      $PACKAGE_NAME
  Description       $DESC
  Visibility        $VISIBILITY
  Target dir        $TARGET
  GitHub repo       github.com/$ACTIVE_GH_LOGIN/$NAME
  Active gh account $ACTIVE_GH_LOGIN
  Author            $(git config --global user.name)
  Email             $(git config --global user.email)
  Scaffold version  $SCAFFOLD_VERSION
  License           MIT (default; edit LICENSE + pyproject.toml to change)
  Python floor      3.11 (default; edit pyproject.toml to change)
  Ruff target       py311 (derived from Python floor; edit pyproject.toml to change)

─────────────────────────────────────────────

Proceed? [Y/n]
```

If user types anything except `y`/`Y`/`yes`/`Yes`/`YES`/Enter, abort cleanly without writing anything.

### Step 4 — Clone scaffold to a tmpdir (pinned)

```bash
SCAFFOLD_TMP=$(mktemp -d)
trap 'rm -rf "${SCAFFOLD_TMP:?}"' EXIT
git clone --depth 1 --branch "$SCAFFOLD_VERSION" \
  https://github.com/YuZh98/python-project-scaffold.git "$SCAFFOLD_TMP"
```

Bump `SCAFFOLD_VERSION` in Step 3 (and anywhere it appears) when adopting a new scaffold release; review the scaffold's `CHANGELOG.md` before bumping.

### Step 5 — Build values.json and delegate to init-project.py

```bash
VALUES=$(mktemp -d)/values.json
python3 - "$NAME" "$PROJECT_TITLE" "$PACKAGE_NAME" "$DESC" "$ACTIVE_GH_LOGIN" <<'PY' > "$VALUES"
import json, subprocess, sys
from datetime import date

name, title, pkg, desc, gh_login = sys.argv[1:6]

def _git(key):
    out = subprocess.run(["git", "config", "--global", key], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""

values = {
  "<<PROJECT_NAME>>":    name,
  "<<PROJECT_TITLE>>":   title,
  "<<PACKAGE_NAME>>":    pkg,
  "<<DESCRIPTION>>":     desc,
  "<<AUTHOR_NAME>>":     _git("user.name"),
  "<<AUTHOR_EMAIL>>":    _git("user.email"),
  "<<YEAR>>":            str(date.today().year),
  "<<LICENSE_ID>>":      "MIT",       # silent default; users wanting a different license can use init-project.py --in-place
  "<<PYTHON_FLOOR>>":    "3.11",      # silent default
  "<<GITHUB_USERNAME>>": gh_login,
}
print(json.dumps(values))
PY

python3 "$SCAFFOLD_TMP/scripts/init-project.py" \
  --target "$TARGET" \
  --values "$VALUES" \
  --yes \
  ${DRY_RUN:+--dry-run}

rm -rf "$(dirname "$VALUES")"
```

`init-project.py --target --values` skips interactive prompts entirely; the script:
- Uses the pre-built values.json (all required fields supplied, including silent defaults for license=MIT and Python floor=3.11).
- All 10 required placeholders (author, email, year, GitHub username, etc.) are pre-filled by the skill in Step 5; `substitute.py` auto-derives `<<RUFF_TARGET>>` from `<<PYTHON_FLOOR>>` during substitution.
- Shows its own confirmation summary and gate (the `--yes` flag bypasses it because the skill already confirmed in Step 3).
- Delegates to `scaffold.sh`, which: copies the template, substitutes placeholders, inits git, creates venv, installs deps, installs pre-commit hooks (incl. commit-msg hook for Conventional Commits), runs pytest gate, and makes the first commit.

If `init-project.py` exits non-zero, abort the skill and print its stderr. The local repo at `$TARGET` may be partially set up — see the rollback story in `init-project.py`.

To recover: fix the root cause, then delete `$TARGET` and re-invoke the skill. (If `scaffold.sh` completed but a later step failed, inspect `$TARGET` manually before re-running.)

### Step 6 — Create GitHub repo + push

```bash
cd "$TARGET"
gh repo create "$ACTIVE_GH_LOGIN/$NAME" \
  --"$VISIBILITY" \
  --source=. \
  --remote=origin \
  --description "$DESC"
git remote set-url origin "https://github.com/$ACTIVE_GH_LOGIN/$NAME.git"
# HTTPS push is intentional — users who prefer SSH can run:
#   git remote set-url origin git@github.com:$ACTIVE_GH_LOGIN/$NAME.git
git push -u origin main || {
  echo "Remote repo created at https://github.com/$ACTIVE_GH_LOGIN/$NAME but push failed."
  echo "To push manually: cd $TARGET && git push -u origin main"
  exit 1
}
```

If `gh repo create` fails (name collision, permission), KEEP the local repo intact and print:

```
Local scaffold ready at $TARGET — manual push:
  cd $TARGET
  gh repo create $ACTIVE_GH_LOGIN/$NAME --$VISIBILITY --description "$DESC"
  git remote add origin "https://github.com/$ACTIVE_GH_LOGIN/$NAME.git"
  git push -u origin main
```

Then exit cleanly.

### Step 7 — Branch protection + cleanup + report

```bash
PROTECTION_BODY='{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}'
if echo "$PROTECTION_BODY" | gh api "repos/${ACTIVE_GH_LOGIN}/${NAME}/branches/main/protection" \
     --method PUT --silent --input - 2>/dev/null; then
  echo "✓ Branch protection enabled (no force-push, no deletion)."
  echo "  Add required status checks after first CI run: Settings → Branches → Edit main."
  echo "  See: $TARGET/docs/setup-branch-protection.md for the full guide."
else
  echo "ℹ Branch protection skipped (private repo on free plan, or transient API error)."
fi

# SCAFFOLD_TMP is cleaned up by the trap set in Step 4.

echo ""
echo "✓ Scaffold complete"
echo ""
echo "  Local path:  $TARGET"
echo "  Remote URL:  https://github.com/$ACTIVE_GH_LOGIN/$NAME"
echo "  Next step:   cd $TARGET && make test"
echo ""
```

## Error handling

- Step 1 pre-flight failure → abort with the actionable message; create nothing.
- Step 3 user declines → abort cleanly; no clone, no files.
- Step 4 git clone failure → abort with the network error; create nothing.
- Step 5 init-project.py failure → keep `$TARGET` as-is for user inspection; print init-project.py's stderr.
- Step 6 gh repo create failure → keep local repo intact; print manual push command (uses `git remote add`, not `git remote set-url`, since origin has not been set yet).
- Step 6 git push failure → repo was created on GitHub; print targeted recovery: `cd $TARGET && git push -u origin main`.
- Step 7 branch protection failure → not fatal; print info message and continue (the local + remote repo are usable).
- All abort paths: clean up `$SCAFFOLD_TMP` if it exists.

## What NOT to do

- Do not auto-open the project in `$EDITOR` (machine-specific).
- Do not auto-open a PR (commit-to-main is fine for a scaffold).
- Do not push secrets or `.env` files (covered by the template `.gitignore`).
- Do not add `Co-Authored-By: Claude` to any commit (the scaffold's first commit message is set by `init-project.py`; the skill never overrides it).
- Do not re-implement license hints, project-name validation, or package-name derivation — `init-project.py` owns those. The skill intentionally builds a partial values.json in Step 5 to supply known values upfront (name, title, package, description, silent license/floor defaults); this is an integration shim, not a reimplementation of the engine.
- Do not skip pre-flight checks even if the user appears to be re-invoking after a previous failure.
- Do not add commits to `$TARGET` between Steps 5 and 7. The first commit is made by `scaffold.sh`; extra commits before the first push break the clean-history invariant.
- Do not re-run `make install` after Step 5. `scaffold.sh` already ran the full setup phase (venv, deps, pre-commit, pytest, first commit).
- Do not modify files in `$SCAFFOLD_TMP`. Treat it as read-only; it is cleaned up by the trap at exit.

## --dry-run

If the user invokes the skill with the equivalent of `--dry-run` (e.g. "/new-project --dry-run" or "preview only"), or natural variants like "just show me what would happen", "simulate it", "preview only":

1. Set `DRY_RUN=1` before Step 5 so `${DRY_RUN:+--dry-run}` is passed to `init-project.py --target`. As of v1.7.2, `init-project.py` correctly handles `--dry-run` in `--target` mode: it prints the values and phases without writing any files or making any git commits.
2. Skip Steps 6 and 7 (no GitHub repo creation, no branch protection).
3. Note: Step 4 (clone scaffold) still runs even in dry-run mode — network access is required.
4. Surface `init-project.py`'s dry-run phase output prominently to the user — this is the primary informational value of dry-run.

Print at the end:
```
[DRY-RUN] No files written, no GitHub repo created.
```

## Updates and drift

- This skill pins to scaffold release tag `v1.7.1` via `SCAFFOLD_VERSION`. To adopt a new scaffold release, bump the tag in Step 3 (where `SCAFFOLD_VERSION` is defined) and review the scaffold's `CHANGELOG.md` between versions.
- The scaffold's interactive prompts and validators are the source of truth — the skill must not re-implement them. If `init-project.py` changes its prompt set, this skill's Step 5 description should be updated to match (but no behavioral change needed in the skill itself).
- Compatibility contract: this skill expects `init-project.py --target` to be a stable interface. Breaking changes to that interface trigger a scaffold-major-version bump and require a skill update.
