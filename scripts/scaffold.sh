#!/usr/bin/env bash
# scaffold.sh — Orchestrate a new Python project from the python-project-scaffold template.
#
# Usage (positional):
#   scripts/scaffold.sh <target-dir> <values-json>
#
# Usage (env vars, e.g. from a Claude Code skill):
#   TARGET=<dir> VALUES=<json-path> scripts/scaffold.sh
#
# Exit codes:
#   0  — success
#   10 — target is an existing, non-empty git repo
#   11 — pre-flight tool missing (gh or python3)
#   20 — pytest failed inside the new project

set -euo pipefail

# ---------------------------------------------------------------------------
# Locate repo root (the directory containing this script's parent)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SCAFFOLD_REPO_ROOT="${REPO_ROOT}"

# ---------------------------------------------------------------------------
# Cleanup partial scaffold on signal (SIGINT, SIGTERM).
# Only fires if scaffold did not complete successfully — last step unsets the trap.
# ---------------------------------------------------------------------------
cleanup_on_signal() {
    local exit_code=$?
    if [ -n "${TARGET:-}" ] && [ -d "${TARGET}" ]; then
        # Only cleanup if the scaffolded repo has no commits yet — otherwise the user
        # has work to preserve.
        if ! git -C "${TARGET}" rev-parse HEAD >/dev/null 2>&1; then
            echo "" >&2
            echo "✗ Scaffold interrupted — removing partial directory ${TARGET}" >&2
            rm -rf "${TARGET}"
        else
            echo "" >&2
            echo "✗ Scaffold interrupted but ${TARGET} has commits — leaving in place" >&2
        fi
    fi
    exit $exit_code
}
trap cleanup_on_signal INT TERM

# ---------------------------------------------------------------------------
# Step 0 — Parse args / env vars
# ---------------------------------------------------------------------------
echo "✓ [0/11] Parsing arguments…"

TARGET="${1:-${TARGET:-}}"
VALUES="${2:-${VALUES:-}}"

if [[ -z "${TARGET}" || -z "${VALUES}" ]]; then
  echo "✗ Usage: scaffold.sh <target-dir> <values-json>" >&2
  echo "  Or set TARGET and VALUES environment variables." >&2
  exit 1
fi

TARGET="$(cd "$(dirname "${TARGET}")" 2>/dev/null && pwd)/$(basename "${TARGET}")" \
  || TARGET="$(pwd)/$(basename "${TARGET}")"
VALUES="$(realpath "${VALUES}")"

echo "  TARGET : ${TARGET}"
echo "  VALUES : ${VALUES}"

# ---------------------------------------------------------------------------
# Step 1 — Idempotency check
# ---------------------------------------------------------------------------
echo "✓ [1/11] Idempotency check…"

if [[ -d "${TARGET}" && -n "$(ls -A "${TARGET}" 2>/dev/null)" && -d "${TARGET}/.git" ]]; then
  echo "✗ [1/11] ${TARGET} is an existing, non-empty git repo. Refusing to overwrite." >&2
  exit 10
fi

# ---------------------------------------------------------------------------
# Step 2 — Pre-flight checks
# ---------------------------------------------------------------------------
echo "✓ [2/11] Pre-flight checks…"

if ! command -v python3 &>/dev/null; then
  echo "✗ [2/11] python3 not found in PATH. Install Python 3.11+ and retry." >&2
  exit 11
fi

if ! command -v gh &>/dev/null; then
  echo "✗ [2/11] gh (GitHub CLI) not found in PATH. Install from https://cli.github.com/ and retry." >&2
  exit 11
fi

echo "  python3 : $(python3 --version)"
echo "  gh      : $(gh --version | head -1)"

# ---------------------------------------------------------------------------
# Step 3 — Copy template tree
# ---------------------------------------------------------------------------
echo "✓ [3/11] Copying template tree to ${TARGET}…"

mkdir -p "${TARGET}"
# Use template/. (not template/*) to preserve dotfiles like .gitignore
cp -R "${REPO_ROOT}/template/." "${TARGET}/"
echo "  Template files copied."

# ---------------------------------------------------------------------------
# Step 4 — Run substitution engine
# ---------------------------------------------------------------------------
echo "✓ [4/11] Running placeholder substitution…"

python3 "${REPO_ROOT}/scripts/substitute.py" \
  --target "${TARGET}" \
  --values "${VALUES}"

# substitute.py exits non-zero on any error; set -e propagates that.

# ---------------------------------------------------------------------------
# Step 5 — Init git
# ---------------------------------------------------------------------------
echo "✓ [5/11] Initialising git repository…"

git -C "${TARGET}" init --initial-branch=main
echo "  git init complete."

# ---------------------------------------------------------------------------
# Step 5.5a — Write scaffold-version provenance file
# Read version from the scaffold repo's manifest.
# ---------------------------------------------------------------------------
MANIFEST_VERSION=$(python3 -c "import json; print(json.load(open('${SCAFFOLD_REPO_ROOT}/template.manifest.json'))['version'])")
SCAFFOLD_SHA=$(git -C "${SCAFFOLD_REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo "unknown")
cat > "${TARGET}/.scaffold-version" <<EOF
# Provenance — DO NOT EDIT by hand.
# This file records which scaffold version produced this project.
# Future migration tooling reads it to identify pre-v(N) projects.
manifest_version: ${MANIFEST_VERSION}
scaffold_sha:     ${SCAFFOLD_SHA}
scaffolded_at:    $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
echo "  Wrote .scaffold-version (manifest_version=${MANIFEST_VERSION})"

# ---------------------------------------------------------------------------
# Step 5.5b — Assert python3 meets the floor
# ---------------------------------------------------------------------------
FLOOR="${PYTHON_FLOOR:-3.11}"
python3 - "$FLOOR" <<'PY'
import sys
floor = sys.argv[1]
major, minor = (int(x) for x in floor.split("."))
if sys.version_info < (major, minor):
    print(f"[scaffold] ERROR: python3 is {sys.version.split()[0]}, need >={floor}", file=sys.stderr)
    sys.exit(1)
print(f"[scaffold] ✓ python3 {sys.version.split()[0]} meets floor {floor}")
PY

# ---------------------------------------------------------------------------
# Step 6 — Create venv
# ---------------------------------------------------------------------------
echo "✓ [6/11] Creating Python virtual environment…"

python3 -m venv "${TARGET}/.venv"
echo "  .venv created."

# ---------------------------------------------------------------------------
# Step 7 — Install dependencies
# ---------------------------------------------------------------------------
echo "✓ [7/11] Installing dependencies…"

"${TARGET}/.venv/bin/pip" install --upgrade pip --quiet

if [[ -f "${TARGET}/requirements.txt" ]]; then
  "${TARGET}/.venv/bin/pip" install -r "${TARGET}/requirements.txt" --quiet
fi

if [[ -f "${TARGET}/requirements-dev.txt" ]]; then
  "${TARGET}/.venv/bin/pip" install -r "${TARGET}/requirements-dev.txt" --quiet
fi

echo "  Dependencies installed."

# ---------------------------------------------------------------------------
# Step 8 — Install pre-commit hooks
# ---------------------------------------------------------------------------
echo "✓ [8/11] Installing pre-commit hooks…"

( cd "${TARGET}" && "./.venv/bin/pre-commit" install )
echo "  pre-commit hooks installed."

# ---------------------------------------------------------------------------
# Step 9 — Run tests
# ---------------------------------------------------------------------------
echo "✓ [9/11] Running tests inside scaffolded project…"

set +e
"${TARGET}/.venv/bin/pytest" "${TARGET}/tests/" -q 2>&1
PYTEST_EXIT=$?
set -e

if [[ "${PYTEST_EXIT}" -ne 0 ]]; then
  echo "✗ [9/11] Tests failed (exit ${PYTEST_EXIT}). Aborting — no commit on red." >&2
  exit 20
fi

echo "  All tests passed."

# ---------------------------------------------------------------------------
# Step 10 — Initial commit
# ---------------------------------------------------------------------------
echo "✓ [10/11] Creating initial commit…"

git -C "${TARGET}" add . "${TARGET}/.scaffold-version"
git -C "${TARGET}" commit -m "feat: initial scaffold from python-project-scaffold (manifest v${MANIFEST_VERSION})"
echo "  Initial commit created."

# ---------------------------------------------------------------------------
# Step 11 — Done
# ---------------------------------------------------------------------------
echo "✓ [11/11] Scaffold complete!"
echo ""
echo "  ✅ Scaffold complete: ${TARGET}"
echo "  Relative path       : $(realpath --relative-to="$(pwd)" "${TARGET}" 2>/dev/null || echo "${TARGET}")"
echo ""
echo "  Next: write \`docs/adr/ADR-0001-import-contract.md\`."

trap - INT TERM EXIT
