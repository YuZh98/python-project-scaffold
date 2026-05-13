#!/usr/bin/env bash
# Build new-project.skill from tooling/claude-code/ sources.
# Usage: package.sh [output-dir]
# Output: <output-dir>/new-project.skill
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${1:-$(pwd)}"
OUTPUT="$OUTPUT_DIR/new-project.skill"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/new-project/scripts"
cp "$SKILL_ROOT/new-project.md"          "$TMP/new-project/SKILL.md"
cp "$SKILL_ROOT/scripts/write_license.py" "$TMP/new-project/scripts/"

python3 - "$TMP" "$OUTPUT" <<'PY'
import sys, zipfile, pathlib
root, out = pathlib.Path(sys.argv[1]), sys.argv[2]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(root.rglob("*")):
        if f.is_file():
            z.write(f, f.relative_to(root))
PY

echo "✓ Built: $OUTPUT  ($(wc -c < "$OUTPUT" | tr -d ' ') bytes)"
