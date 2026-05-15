#!/usr/bin/env bash
# Bootstrap a new Python project tree by delegating to the scaffold's
# `init-project` entry point.
#
# Usage:
#   bootstrap.sh PROJECT_NAME DESCRIPTION LICENSE_ID
#
# Why this is a separate script: SKILL.md should not contain pipx invocation
# details or values-JSON construction. Those are mechanics, and changing
# scaffold versions or argument formats should not require re-reading the
# whole orchestrator.
#
# Side effects: creates "$(pwd)/$PROJECT_NAME". Makes the scaffold's single
# initial commit inside it. Does NOT touch GitHub — that's finalize.sh.

set -euo pipefail

# ---------------------------------------------------------------------------
# Scaffold version pin.
# Pinned to the latest stable scaffold tag. Plugin release flow re-pins
# this to whichever scaffold tag the plugin release was tested against.
# ---------------------------------------------------------------------------
SCAFFOLD_VERSION="v1.8.0"
SCAFFOLD_REPO_URL="https://github.com/YuZh98/python-project-scaffold.git"

die() {
  echo "bootstrap: $*" >&2
  exit 1
}

if [[ $# -lt 3 ]]; then
  die "usage: bootstrap.sh PROJECT_NAME DESCRIPTION LICENSE_ID"
fi

NAME="$1"
DESC="$2"
LICENSE_ID="$3"

# Derive remaining values. init-project.py also validates these, but the
# orchestrator needs TARGET ahead of time and PACKAGE_NAME/TITLE for the
# values JSON.
PACKAGE_NAME="${NAME//-/_}"
PROJECT_TITLE="$(echo "$NAME" | tr '-' ' ' | python3 -c 'import sys; print(sys.stdin.read().strip().title())')"
TARGET="$(pwd)/$NAME"
GH_LOGIN="$(gh api user --jq .login)"
AUTHOR_NAME="$(git config --global user.name)"
AUTHOR_EMAIL="$(git config --global user.email)"
YEAR="$(date +%Y)"
PYTHON_FLOOR="3.11"

# Refuse to clobber an existing directory. init-project.py also checks, but
# failing early avoids a confusing partial pipx download.
if [[ -d "$TARGET" ]]; then
  die "target directory already exists: $TARGET"
fi

# Single trap with append-friendly cleanup array. Subsequent temp dirs push
# onto CLEANUP; trap iterates and removes on EXIT regardless of exit path.
CLEANUP=()
trap 'for d in ${CLEANUP[@]+"${CLEANUP[@]}"}; do [[ -n "$d" ]] && rm -rf "$d"; done' EXIT

VALUES_DIR="$(mktemp -d)"
CLEANUP+=("$VALUES_DIR")
VALUES="$VALUES_DIR/values.json"

python3 - \
  "$NAME" "$PROJECT_TITLE" "$PACKAGE_NAME" "$DESC" \
  "$AUTHOR_NAME" "$AUTHOR_EMAIL" "$YEAR" "$LICENSE_ID" \
  "$PYTHON_FLOOR" "$GH_LOGIN" <<'PY' > "$VALUES"
import json, sys
keys = [
    "<<PROJECT_NAME>>", "<<PROJECT_TITLE>>", "<<PACKAGE_NAME>>", "<<DESCRIPTION>>",
    "<<AUTHOR_NAME>>", "<<AUTHOR_EMAIL>>", "<<YEAR>>", "<<LICENSE_ID>>",
    "<<PYTHON_FLOOR>>", "<<GITHUB_USERNAME>>",
]
print(json.dumps(dict(zip(keys, sys.argv[1:1 + len(keys)]))))
PY

# Fetch scaffold at pinned tag into temp dir and invoke init-project.py
# directly. The scaffold has no pyproject.toml/console_script entry, so
# pipx is not an option — we run the script by path.
SCAFFOLD_TMP="$(mktemp -d)"
CLEANUP+=("$SCAFFOLD_TMP")

git clone --depth 1 --branch "$SCAFFOLD_VERSION" \
  "$SCAFFOLD_REPO_URL" "$SCAFFOLD_TMP" >&2

python3 "$SCAFFOLD_TMP/scripts/init-project.py" \
  --target "$TARGET" \
  --values "$VALUES" \
  --yes

echo "bootstrap: scaffold complete at $TARGET" >&2
