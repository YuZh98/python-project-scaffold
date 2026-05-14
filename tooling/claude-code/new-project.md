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

Wrapper around `python-project-scaffold` that adds GitHub repo creation, branch protection,
and a 4-question UX. See https://github.com/YuZh98/python-project-scaffold for the manual flow.

Refuse if already inside a git repo — the skill creates a new directory below cwd.

## Workflow

### Step 1 — Pre-flight

```bash
gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first (needs 'repo' scope for repo creation and branch protection). If you have multiple accounts, switch with 'gh auth switch'."; exit 1; }
ACTIVE_GH_LOGIN=$(gh api user --jq .login)
[[ -n "$(git config --global user.name 2>/dev/null)" ]] || { echo "Configure git first: git config --global user.name '<name>' && git config --global user.email '<email>'"; exit 1; }
[[ -n "$(git config --global user.email 2>/dev/null)" ]] || { echo "Configure git first: git config --global user.email '<email>'"; exit 1; }
python3 --version >/dev/null 2>&1 || { echo "python3 is required but not found. Install Python 3.11+ and retry."; exit 1; }
make --version >/dev/null 2>&1 || { echo "make is required but not found. macOS: xcode-select --install  Linux: sudo apt install build-essential"; exit 1; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && { echo "Refusing to run inside an existing git repo. cd to a parent directory and re-invoke."; exit 1; } || true
```

### Step 2 — Ask 4 questions

Use `AskUserQuestion` if available, otherwise prompt sequentially:

1. **Name** — `lowercase-letters-digits-hyphens`, start+end alphanumeric. Re-prompt: "Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit. Got: '<value>'. Try: my-cool-tool"
2. **Description** — one line. Example: "Tool for managing X."
3. **Visibility** — `private` (default) or `public`. Re-prompt: "Visibility must be 'private' or 'public'. Got: '<value>'."
4. **License** — `MIT` (default), `Apache-2.0`, `BSD-3-Clause`, or `Unlicense`. Re-prompt: "License must be one of: MIT, Apache-2.0, BSD-3-Clause, Unlicense. Got: '<value>'."

Store answers as `NAME`, `DESC`, `VISIBILITY`, `LICENSE_ID`. Python floor is a silent default (3.11).

### Step 3 — Summary + confirm

```bash
SCAFFOLD_VERSION="v1.7.8"
PACKAGE_NAME=$(echo "$NAME" | tr '-' '_')
PROJECT_TITLE=$(echo "$NAME" | tr '-' ' ' | python3 -c "import sys; print(sys.stdin.read().strip().title())")
TARGET="$(pwd)/$NAME"
[[ -d "$TARGET" ]] && { echo "Directory $TARGET already exists. Choose a different name or remove it first."; exit 1; }
```

Print and confirm before writing anything:

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
  License           $LICENSE_ID
  Python floor      3.11 (fixed default)
  Ruff target       py311

─────────────────────────────────────────────

Proceed? [Y/n]
```

Accept `y`/`Y`/`yes`/`Yes`/`YES`/Enter. Anything else → abort cleanly, write nothing.

### Step 4 — Clone scaffold

```bash
SCAFFOLD_TMP=$(mktemp -d)
trap 'rm -rf "${SCAFFOLD_TMP:?}"' EXIT
git clone --depth 1 --branch "$SCAFFOLD_VERSION" \
  https://github.com/YuZh98/python-project-scaffold.git "$SCAFFOLD_TMP"
```

To adopt a new scaffold release: bump `SCAFFOLD_VERSION` here and review the scaffold's `CHANGELOG.md`.

### Step 5 — Bootstrap

```bash
VALUES=$(mktemp -d)/values.json
python3 - "$NAME" "$PROJECT_TITLE" "$PACKAGE_NAME" "$DESC" "$ACTIVE_GH_LOGIN" "$LICENSE_ID" <<'PY' > "$VALUES"
import json, subprocess, sys
from datetime import date

name, title, pkg, desc, gh_login, license_id = sys.argv[1:7]

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
  "<<LICENSE_ID>>":      license_id,
  "<<PYTHON_FLOOR>>":    "3.11",
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

if [[ -n "${DRY_RUN:-}" ]]; then
  echo "[DRY-RUN] No files written, no GitHub repo created."
  exit 0
fi

# Scaffold template has MIT text; overwrite and amend first commit for non-MIT choices.
if [[ "$LICENSE_ID" != "MIT" ]]; then
  WRITE_LICENSE="$HOME/.claude/skills/new-project/scripts/write_license.py"
  [[ -f "$WRITE_LICENSE" ]] || WRITE_LICENSE="$SCAFFOLD_TMP/tooling/claude-code/scripts/write_license.py"
  python3 "$WRITE_LICENSE" \
    "$LICENSE_ID" "$(date +%Y)" "$(git config --global user.name)" \
    > "$TARGET/LICENSE"
  git -C "$TARGET" add LICENSE && git -C "$TARGET" commit --amend --no-edit
  echo "✓ LICENSE rewritten to $LICENSE_ID text (first commit amended)."
fi
```

On failure: print stderr, delete `$TARGET`, re-invoke. (If only the license amend failed, run `git add LICENSE && git commit --amend --no-edit` manually after fixing `$TARGET/LICENSE`.)

### Step 6 — Create GitHub repo + push

```bash
cd "$TARGET"
gh repo create "$ACTIVE_GH_LOGIN/$NAME" \
  --"$VISIBILITY" \
  --source=. \
  --remote=origin \
  --description "$DESC"
git remote set-url origin "https://github.com/$ACTIVE_GH_LOGIN/$NAME.git"
# HTTPS is intentional; SSH users: git remote set-url origin git@github.com:$ACTIVE_GH_LOGIN/$NAME.git
git push -u origin main || {
  echo "Remote repo created at https://github.com/$ACTIVE_GH_LOGIN/$NAME but push failed."
  echo "To push manually: cd $TARGET && git push -u origin main"
  exit 1
}
```

On `gh repo create` failure, keep local repo and print:
```
Local scaffold ready at $TARGET — manual push:
  cd $TARGET
  gh repo create $ACTIVE_GH_LOGIN/$NAME --$VISIBILITY --description "$DESC"
  git remote add origin "https://github.com/$ACTIVE_GH_LOGIN/$NAME.git"
  git push -u origin main
```

### Step 7 — Branch protection + report

```bash
PROTECTION_BODY='{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}'
if echo "$PROTECTION_BODY" | gh api "repos/${ACTIVE_GH_LOGIN}/${NAME}/branches/main/protection" \
     --method PUT --silent --input - 2>/dev/null; then
  echo "✓ Branch protection enabled (no force-push, no deletion)."
  echo "  Add required status checks after first CI run: Settings → Branches → Edit main."
else
  echo "ℹ Branch protection skipped (private repo on free plan, or transient API error)."
fi

echo ""
echo "✓ Scaffold complete"
echo ""
echo "  Local:   $TARGET"
echo "  Remote:  https://github.com/$ACTIVE_GH_LOGIN/$NAME"
echo ""
echo "  1. cd $TARGET && make test"
echo "     Runs ruff + pyright + pytest + coverage. All should pass."
echo "     This is your green baseline — verify it before writing any code."
echo ""
echo "  2. Dependabot will open a few PRs shortly — this is expected."
echo "     Grouped minor/patch updates: skim the diff, confirm CI green, merge."
echo ""
echo "  3. New to this scaffold? Read docs/concepts.md for a tour of what shipped."
echo ""
```

Branch protection failure is not fatal — the repo is usable.

## Do not

- Open `$EDITOR`, auto-open a PR, or add `Co-Authored-By: Claude` to any commit.
- Re-implement validation or derivation — `init-project.py` owns that; this skill is an integration shim.
- Add commits between Steps 5–7. `init-project.py --target` makes the only pre-push commit; the license amend in Step 5 is the sole exception.
- Re-run `make install` — `init-project.py --target` already ran the full setup phase.
- Modify `$SCAFFOLD_TMP`; it is read-only and trap-cleaned at exit.

## --dry-run

Trigger phrases: `/new-project --dry-run`, "preview only", "show me what would happen", "simulate it".

Recognise the trigger phrase at invocation. Set `DRY_RUN=1` immediately, then proceed through Steps 1–5 normally. The explicit shell gate at the end of Step 5 exits before Steps 6–7. Step 4 clone still runs (network required). Surface the phase output to the user.

Print at end: `[DRY-RUN] No files written, no GitHub repo created.`

## Examples

### Name validation

User provides `My_Project` (invalid: uppercase, underscore) → skill re-prompts:
```
Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit.
Got: 'My_Project'. Try: my-project
```
User provides `my-project` → valid, continues to question 2.

### License re-prompt

User enters `GPL-3.0` at license question → skill re-prompts:
```
License must be one of: MIT, Apache-2.0, BSD-3-Clause, Unlicense. Got: 'GPL-3.0'.
```
User enters `Apache-2.0` → valid.

### Happy-path Step 3 summary

Inputs: name=`data-pipeline`, desc=`ETL framework for time-series data`, visibility=`private`, license=`MIT`:
```
─────────────────────────────────────────────
Pre-clone summary — please review

  Project name      data-pipeline
  Project title     Data Pipeline
  Package name      data_pipeline
  Description       ETL framework for time-series data
  Visibility        private
  Target dir        /Users/alice/projects/data-pipeline
  GitHub repo       github.com/alice/data-pipeline
  Active gh account alice
  Author            Alice Smith
  Email             alice@example.com
  Scaffold version  v1.7.6
  License           MIT
  Python floor      3.11 (fixed default)
  Ruff target       py311

─────────────────────────────────────────────

Proceed? [Y/n]
```

### Step 7 completion output

```
✓ Branch protection enabled (no force-push, no deletion).
  Add required status checks after first CI run: Settings → Branches → Edit main.

✓ Scaffold complete

  Local:   /Users/alice/projects/data-pipeline
  Remote:  https://github.com/alice/data-pipeline

  1. cd /Users/alice/projects/data-pipeline && make test
     Runs ruff + pyright + pytest + coverage. All should pass.
     This is your green baseline — verify it before writing any code.

  2. Dependabot will open a few PRs shortly — this is expected.
     Grouped minor/patch updates: skim the diff, confirm CI green, merge.

  3. New to this scaffold? Read docs/concepts.md for a tour of what shipped.
```
