#!/usr/bin/env bash
# Finalize a freshly scaffolded project: create the GitHub repo, push, and
# enable branch protection on main.
#
# Usage:
#   finalize.sh PROJECT_NAME VISIBILITY DESCRIPTION
#
# Why this is a separate script: networked operations (gh repo create, push,
# protection API) are independently fail-able from local scaffolding. Keeping
# them in their own file lets the user re-run just this phase if bootstrap
# succeeded but push failed.
#
# Side effects: creates a GitHub repo under the active gh login, sets origin,
# pushes main, attempts to enable branch protection (non-fatal on failure).

set -euo pipefail

die() {
  echo "finalize: $*" >&2
  exit 1
}

if [[ $# -lt 3 ]]; then
  die "usage: finalize.sh PROJECT_NAME VISIBILITY DESCRIPTION"
fi

NAME="$1"
VISIBILITY="$2"
DESC="$3"
TARGET="$(pwd)/$NAME"
GH_LOGIN="$(gh api user --jq .login)"

if [[ ! -d "$TARGET/.git" ]]; then
  die "expected git repo at $TARGET — did bootstrap.sh run?"
fi

# Create the GitHub repo with --source so it picks up the local main branch.
# We intentionally use HTTPS for origin; SSH users can rewrite afterwards.
cd "$TARGET"
gh repo create "$GH_LOGIN/$NAME" \
  --"$VISIBILITY" \
  --source=. \
  --remote=origin \
  --description "$DESC" \
  || die "gh repo create failed. Local repo is intact at $TARGET; re-run finalize after fixing."

git remote set-url origin "https://github.com/$GH_LOGIN/$NAME.git"

if ! git push -u origin main; then
  echo "finalize: remote repo created at https://github.com/$GH_LOGIN/$NAME but push failed." >&2
  echo "finalize: manual push:  cd $TARGET && git push -u origin main" >&2
  exit 1
fi

# Branch protection. Free-plan private repos can't take protection; treat
# that as informational, not a failure.
PROTECTION_BODY='{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false}'
if echo "$PROTECTION_BODY" | gh api "repos/${GH_LOGIN}/${NAME}/branches/main/protection" \
     --method PUT --silent --input - 2>/dev/null; then
  echo "finalize: branch protection enabled on main (no force-push, no deletion)." >&2
  echo "finalize: add required status checks after first CI run via Settings -> Branches." >&2
else
  echo "finalize: branch protection skipped (private repo on free plan, or transient API error)." >&2
fi

cat <<EOF >&2
finalize: scaffold complete.

  Local:   $TARGET
  Remote:  https://github.com/$GH_LOGIN/$NAME

  1. cd $TARGET && make test
     Runs ruff + pyright + pytest + coverage. Verify the green baseline
     before writing any code.

  2. Dependabot will open a few PRs shortly — this is expected. Grouped
     minor/patch updates: skim diff, confirm CI green, merge.

  3. New to this scaffold? Read docs/concepts.md for a tour of what shipped.
EOF
