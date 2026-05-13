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

Goal: bootstrap a new Python project from `python-project-scaffold` and create a GitHub repo for it. The skill is a Claude Code-specific wrapper around the scaffold's own bootstrap engine (`scripts/init-project.py`) — it adds GitHub repo creation, branch protection, and Claude-style 4-question UX.

The scaffold itself is Claude-independent; if you want to bootstrap without this skill, see https://github.com/YuZh98/python-project-scaffold for the manual `python3 scripts/init-project.py` flow.

## When to invoke

Trigger this skill when the user wants to create a NEW project AND wants a GitHub repo created automatically. User phrases that trigger this skill: `/new-project`, "create a new python project", "initialize a new project", "start a new python project", "scaffold new project", "bootstrap new repo", "spin up a fresh python project", or any request to create/start/initialize/scaffold/bootstrap a new Python repo or project from scratch.

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

### Step 2 — Ask the user 4 questions

Use `AskUserQuestion` if available; otherwise prompt sequentially. The 4 questions:

1. **Project name** — lowercase letters / digits / hyphens; start+end with a letter or digit. Example: `my-cool-tool`. On invalid input, re-prompt with: "Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit. Got: '<value>'. Try: my-cool-tool".
2. **One-line description**. Example: "Tool for managing X."
3. **Visibility**: `private` (default) or `public`.
4. **License**: `MIT` (default), `Apache-2.0`, `BSD-3-Clause`, or `Unlicense`. On invalid input, re-prompt with: "License must be one of: MIT, Apache-2.0, BSD-3-Clause, Unlicense. Got: '<value>'."

Store the license answer as `LICENSE_ID`. DO NOT ask for Python floor — the skill uses a silent default (Python 3.11 floor) and passes it directly to `init-project.py` in Step 5.

### Step 3 — Show derived-values summary BEFORE clone

Compute these derived values (without calling init-project.py — these are the bits the skill needs for the GitHub URL):

```bash
SCAFFOLD_VERSION="v1.7.3"
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
  License           $LICENSE_ID
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
  "<<LICENSE_ID>>":      license_id,  # set by Step 2 question 4
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

# If the user chose a non-MIT license, the scaffold template's LICENSE file contains
# MIT text. Overwrite it with the correct SPDX text and amend the first commit.
if [[ "$LICENSE_ID" != "MIT" ]]; then
  YEAR=$(date +%Y)
  AUTHOR=$(git config --global user.name)
  python3 - "$LICENSE_ID" "$YEAR" "$AUTHOR" > "$TARGET/LICENSE" <<'PY'
import sys
lid, year, author = sys.argv[1], sys.argv[2], sys.argv[3]

texts = {
  "Apache-2.0": f"""Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.
   "License" shall mean the terms and conditions for use, reproduction, and
   distribution as defined by Sections 1 through 9 of this document.
   "Licensor" shall mean the copyright owner or entity authorized by the
   copyright owner that is granting the License.
   "Legal Entity" shall mean the union of the acting entity and all other
   entities that control, are controlled by, or are under common control with
   that entity.
   "You" (or "Your") shall mean an individual or Legal Entity exercising
   permissions granted by this License.
   "Source" form shall mean the preferred form for making modifications.
   "Object" form shall mean any form resulting from mechanical transformation
   or translation of a Source form.
   "Work" shall mean the work of authorship made available under the License.
   "Derivative Works" shall mean any work that is based on the Work.
   "Contribution" shall mean any work of authorship submitted to the Licensor.
   "Contributor" shall mean Licensor and any Legal Entity on behalf of whom a
   Contribution has been received by the Licensor.

2. Grant of Copyright License. Subject to the terms and conditions of this
   License, each Contributor hereby grants to You a perpetual, worldwide,
   non-exclusive, no-charge, royalty-free, irrevocable copyright license to
   reproduce, prepare Derivative Works of, publicly display, publicly perform,
   sublicense, and distribute the Work and such Derivative Works.

3. Grant of Patent License. Subject to the terms and conditions of this
   License, each Contributor hereby grants to You a perpetual, worldwide,
   non-exclusive, no-charge, royalty-free, irrevocable patent license to make,
   use, sell, offer for sale, import, and otherwise transfer the Work.

4. Redistribution. You may reproduce and distribute copies of the Work or
   Derivative Works thereof in any medium, with or without modifications,
   provided that You meet the following conditions:
   (a) You must give any other recipients a copy of this License; and
   (b) You must cause any modified files to carry prominent notices stating
       that You changed the files; and
   (c) You must retain all copyright, patent, trademark, and attribution
       notices from the Source form of the Work; and
   (d) If the Work includes a "NOTICE" file, you must include a readable copy
       of the attribution notices contained within that NOTICE file.

5. Submission of Contributions. Unless You explicitly state otherwise, any
   Contribution submitted for inclusion in the Work shall be under the terms
   of this License, without any additional terms or conditions.

6. Trademarks. This License does not grant permission to use trade names,
   trademarks, service marks, or product names of the Licensor.

7. Disclaimer of Warranty. THE WORK IS PROVIDED "AS IS" WITHOUT WARRANTIES
   OR CONDITIONS OF ANY KIND.

8. Limitation of Liability. IN NO EVENT SHALL ANY CONTRIBUTOR BE LIABLE FOR
   ANY DAMAGES ARISING FROM THE WORK.

9. Accepting Warranty or Additional Liability. While redistributing the Work,
   You may offer acceptance of warranty or liability obligations. However,
   when accepting such obligations, You may act only on Your own behalf.

END OF TERMS AND CONDITIONS

Copyright {year} {author}

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy of
the License at http://www.apache.org/licenses/LICENSE-2.0
""",
  "BSD-3-Clause": f"""BSD 3-Clause License

Copyright (c) {year}, {author}
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""",
  "Unlicense": """This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute
this software, either in source code form or as compiled binaries, for any
purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>
""",
}
print(texts[lid], end="")
PY
  cd "$TARGET" && git add LICENSE && git commit --amend --no-edit
fi
```

`init-project.py --target --values` skips interactive prompts entirely; the script:
- Uses the pre-built values.json (all required fields supplied; license is set from Step 2 question 4; Python floor defaults to 3.11).
- All 10 required placeholders (author, email, year, GitHub username, etc.) are pre-filled by the skill in Step 5; `substitute.py` auto-derives `<<RUFF_TARGET>>` from `<<PYTHON_FLOOR>>` during substitution.
- Shows its own confirmation summary and gate (the `--yes` flag bypasses it because the skill already confirmed in Step 3).
- Delegates to `scaffold.sh`, which: copies the template, substitutes placeholders, inits git, creates venv, installs deps, installs pre-commit hooks (incl. commit-msg hook for Conventional Commits), runs pytest gate, and makes the first commit.

If `init-project.py` exits non-zero, abort the skill and print its stderr. The local repo at `$TARGET` may be partially set up — see the rollback story in `init-project.py`.

To recover: fix the root cause, then delete `$TARGET` and re-invoke the skill. (If `scaffold.sh` completed but the license-file amend failed, inspect `$TARGET` manually — run `git add LICENSE && git commit --amend --no-edit` after fixing the LICENSE file.)

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
- Step 5 license-file rewrite failure (non-MIT only) → `$TARGET/LICENSE` may still contain MIT text; print error; user should `git add LICENSE && git commit --amend --no-edit` after fixing.
- Step 6 gh repo create failure → keep local repo intact; print manual push command (uses `git remote add`, not `git remote set-url`, since origin has not been set yet).
- Step 6 git push failure → repo was created on GitHub; print targeted recovery: `cd $TARGET && git push -u origin main`.
- Step 7 branch protection failure → not fatal; print info message and continue (the local + remote repo are usable).
- All abort paths: clean up `$SCAFFOLD_TMP` if it exists.

## What NOT to do

- Do not auto-open the project in `$EDITOR` (machine-specific).
- Do not auto-open a PR (commit-to-main is fine for a scaffold).
- Do not push secrets or `.env` files (covered by the template `.gitignore`).
- Do not add `Co-Authored-By: Claude` to any commit (the scaffold's first commit message is set by `init-project.py`; the skill never overrides it).
- Do not re-implement project-name validation, package-name derivation, or placeholder substitution — `init-project.py` owns those. The skill builds a values.json in Step 5 to supply known values (name, title, package, description, license, silent floor default); this is an integration shim, not a reimplementation.
- Do not skip pre-flight checks even if the user appears to be re-invoking after a previous failure.
- Do not add commits to `$TARGET` between Steps 5 and 7. The first commit is made by `scaffold.sh`; extra commits before the first push break the clean-history invariant.
- Do not re-run `make install` after Step 5. `scaffold.sh` already ran the full setup phase (venv, deps, pre-commit, pytest, first commit).
- Do not modify files in `$SCAFFOLD_TMP`. Treat it as read-only; it is cleaned up by the trap at exit.

## Examples

### Happy path

**User:** "create a new private python project called invoice-parser for extracting data from PDF invoices, Apache license"

**Step 2 answers collected:**
- Name: `invoice-parser`
- Description: `Tool for extracting structured data from PDF invoices.`
- Visibility: `private`
- License: `Apache-2.0`

**Step 3 summary printed:**
```
─────────────────────────────────────────────
Pre-clone summary — please review

  Project name      invoice-parser
  Project title     Invoice Parser
  Package name      invoice_parser
  Description       Tool for extracting structured data from PDF invoices.
  Visibility        private
  Target dir        /Users/alice/invoice-parser
  GitHub repo       github.com/alice/invoice-parser
  Active gh account alice
  Author            Alice Smith
  Email             alice@example.com
  Scaffold version  v1.7.3
  License           Apache-2.0
  Python floor      3.11 (default; edit pyproject.toml to change)
  Ruff target       py311 (derived from Python floor; edit pyproject.toml to change)

─────────────────────────────────────────────

Proceed? [Y/n]
```

**Step 7 final output:**
```
✓ Branch protection enabled (no force-push, no deletion).
  Add required status checks after first CI run: Settings → Branches → Edit main.

✓ Scaffold complete

  Local path:  /Users/alice/invoice-parser
  Remote URL:  https://github.com/alice/invoice-parser
  Next step:   cd /Users/alice/invoice-parser && make test
```

---

### Name validation re-prompt

**User provides:** `My_Project` (invalid: uppercase letters and underscore)

**Skill re-prompts:**
```
Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit.
Got: 'My_Project'. Try: my-project
```

**User provides:** `my-project` → valid, skill continues to question 2.

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

- This skill pins to scaffold release tag `v1.7.3` via `SCAFFOLD_VERSION`. To adopt a new scaffold release, bump the tag in Step 3 (where `SCAFFOLD_VERSION` is defined) and review the scaffold's `CHANGELOG.md` between versions.
- The scaffold's interactive prompts and validators are the source of truth — the skill must not re-implement them. If `init-project.py` changes its prompt set, this skill's Step 5 description should be updated to match (but no behavioral change needed in the skill itself).
- Compatibility contract: this skill expects `init-project.py --target` to be a stable interface. Breaking changes to that interface trigger a scaffold-major-version bump and require a skill update.
