#!/usr/bin/env bash
# release.sh — execute the release sequence for a Python project that follows
# Keep-a-Changelog. Implements the steps from ~/.claude/CLAUDE.md §9.
#
# Usage:
#   release.sh [--check | --dry-run] [--allow-branch] VERSION
#
# Modes:
#   --check     run preflight only (no writes, no commits, no push)
#   --dry-run   print the rotation diff and the commands that would run
#   (default)   execute the full release: rotate, commit, tag, push, bump, push
#
# VERSION accepts either `vX.Y.Z` or `X.Y.Z`; both are normalized internally.
# Pre-release suffixes (rc1, beta, alpha, .dev0 on input) are rejected — this
# script handles final releases only.
#
# Why bash for orchestration, Python for file edits: shell glue is good at
# running git and capturing exit codes; CHANGELOG rewriting and TOML version
# bumping want real parsing. The python heredocs are kept small and stateless.
#
# Refuse-first policy: every precondition is checked before any state changes.
# A run that would have failed at step 4 never gets to step 1.

set -euo pipefail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

die() {
  echo "release: $*" >&2
  exit 1
}

note() {
  echo "release: $*" >&2
}

usage() {
  cat >&2 <<'USAGE'
usage: release.sh [--check | --dry-run] [--allow-branch] VERSION
  VERSION       semver, vX.Y.Z or X.Y.Z (no pre-release suffixes)
  --check       preflight only; no writes
  --dry-run     print proposed diff and commands; no writes
  --allow-branch  bypass the main/master/release/* branch check
USAGE
  exit 2
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

MODE="execute"           # execute | check | dry-run
ALLOW_BRANCH="false"
VERSION_RAW=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)         MODE="check"; shift ;;
    --dry-run)       MODE="dry-run"; shift ;;
    --allow-branch)  ALLOW_BRANCH="true"; shift ;;
    -h|--help)       usage ;;
    -*)              die "unknown flag: $1" ;;
    *)
      if [[ -n "$VERSION_RAW" ]]; then
        die "unexpected extra argument: $1 (already have version: $VERSION_RAW)"
      fi
      VERSION_RAW="$1"
      shift
      ;;
  esac
done

[[ -n "$VERSION_RAW" ]] || usage

# ---------------------------------------------------------------------------
# Normalize version. Accept both `1.2.0` and `v1.2.0`. The brief uses three
# forms in three places (tag/commit message want `v`; CHANGELOG heading and
# pyproject metadata don't). Normalize once, refer to the right form by name.
# ---------------------------------------------------------------------------

if [[ ! "$VERSION_RAW" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  die "invalid version: '$VERSION_RAW'. Expected vX.Y.Z or X.Y.Z (no pre-release suffixes)."
fi

VER_NO_V="${VERSION_RAW#v}"
VER_WITH_V="v${VER_NO_V}"

# Derive the next dev-cycle version: bump patch by 1, append .dev0.
# 1.2.0 -> 1.2.1.dev0 ; 0.9.4 -> 0.9.5.dev0
IFS='.' read -r MAJOR MINOR PATCH <<<"$VER_NO_V"
NEXT_DEV="${MAJOR}.${MINOR}.$((PATCH + 1)).dev0"

TODAY="$(date +%Y-%m-%d)"

# ---------------------------------------------------------------------------
# Preflight — every check before any state change
# ---------------------------------------------------------------------------

# Must be inside a git repo.
git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || die "not inside a git repository."

# Run from repo root regardless of cwd. Keeps relative paths predictable.
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Branch check. Detached HEAD is always refused; non-release branches are
# refused unless --allow-branch is set.
CURRENT_BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  die "HEAD is detached. Check out a release branch (main/master/release/*) and retry."
fi
case "$CURRENT_BRANCH" in
  main|master|release/*)
    : # ok
    ;;
  *)
    if [[ "$ALLOW_BRANCH" != "true" ]]; then
      die "current branch '$CURRENT_BRANCH' is not a release branch.
       Standard release branches: main, master, release/*.
       Pass --allow-branch to override (rarely correct)."
    fi
    note "branch override: releasing from '$CURRENT_BRANCH' via --allow-branch."
    ;;
esac

# Clean working tree. --porcelain returns one line per dirty path.
if [[ -n "$(git status --porcelain)" ]]; then
  die "working tree dirty. Commit or stash before releasing.
       (run 'git status' to see what.)"
fi

# CHANGELOG must exist and contain [Unreleased].
CHANGELOG="CHANGELOG.md"
[[ -f "$CHANGELOG" ]] || die "$CHANGELOG missing at repo root."

if ! grep -qE '^## \[Unreleased\]' "$CHANGELOG"; then
  die "$CHANGELOG has no '## [Unreleased]' heading. This skill requires Keep-a-Changelog format."
fi

# pyproject.toml must exist (we need it for the post-release bump).
[[ -f "pyproject.toml" ]] || die "pyproject.toml missing at repo root."

# Tag must not already exist (local OR remote).
if git rev-parse -q --verify "refs/tags/${VER_WITH_V}" >/dev/null; then
  die "tag ${VER_WITH_V} already exists locally. Refusing to re-release.
       (Delete with 'git tag -d ${VER_WITH_V}' only if you know it was never pushed.)"
fi
# Remote check is best-effort: don't fail the whole run if 'origin' isn't set.
if git remote get-url origin >/dev/null 2>&1; then
  if git ls-remote --tags origin "${VER_WITH_V}" 2>/dev/null | grep -q "refs/tags/${VER_WITH_V}"; then
    die "tag ${VER_WITH_V} already exists on origin. Refusing to re-release."
  fi
fi

# [Unreleased] must have at least one bullet entry. HTML comments and bare
# subheadings (### Added with no bullets) don't count. We delegate to a real
# parse in Python because subheading detection has to be ordered relative to
# the next `## [` heading, and bash regex is unreliable for that.
#
# Why route through a tempfile instead of $(python3 - <<PY): bash 3.2 (macOS
# default) has known fragility with heredocs nested in command substitution.
# A tempfile-backed Python script is portable and equally cheap.
COUNT_PY="$(mktemp -t release_count.XXXXXX.py)"
cat > "$COUNT_PY" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()

# Find the [Unreleased] section: from its heading to the next ## [...] or EOF.
m = re.search(r'^## \[Unreleased\][^\n]*\n', text, flags=re.MULTILINE)
if not m:
    print(0); sys.exit(0)
start = m.end()
next_section = re.search(r'^## \[', text[start:], flags=re.MULTILINE)
end = start + next_section.start() if next_section else len(text)
block = text[start:end]

# Strip HTML comments so they don't accidentally match bullet regex.
block = re.sub(r'<!--.*?-->', '', block, flags=re.DOTALL)

# Count markdown bullets with at least one non-whitespace char of content.
bullets = re.findall(r'^\s*[-*]\s+\S', block, flags=re.MULTILINE)
print(len(bullets))
PY

UNRELEASED_BULLETS="$(python3 "$COUNT_PY" "$CHANGELOG")"
rm -f "$COUNT_PY"

if [[ "$UNRELEASED_BULLETS" -eq 0 ]]; then
  die "nothing to release. [Unreleased] in $CHANGELOG has no entries.
       Add bullets under one of: Added, Changed, Deprecated, Removed, Fixed, Security.
       Then re-invoke."
fi

note "preflight ok: branch=$CURRENT_BRANCH version=$VER_WITH_V unreleased_entries=$UNRELEASED_BULLETS"

if [[ "$MODE" == "check" ]]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Rotation — compute, and either print (dry-run) or write (execute).
# ---------------------------------------------------------------------------
#
# The rewrite:
#   1. Find `## [Unreleased]` heading.
#   2. Replace it with two headings:
#        ## [Unreleased]
#        (fresh empty body with all 6 Keep-a-Changelog subheadings as scaffolding)
#        ## [X.Y.Z] - YYYY-MM-DD
#   3. The existing entries (between the old [Unreleased] heading and the next
#      `## [` heading) stay attached to the new versioned heading.
#
# Pre-populating the 6 subheadings on the fresh [Unreleased] is a deliberate
# choice. The template comment says "omit empty ones before releasing" — that's
# a release-time scrub, not a never-include rule. Scaffolding the headings
# helps the next change pick the right bucket without re-reading the spec.

TMP_NEW="$(mktemp -t release.XXXXXX)"
trap 'rm -f "$TMP_NEW"' EXIT

python3 - "$CHANGELOG" "$VER_NO_V" "$TODAY" "$TMP_NEW" <<'PY'
import re, sys
src_path, version, today, out_path = sys.argv[1:5]
text = open(src_path, encoding="utf-8").read()

FRESH_UNRELEASED = (
    "## [Unreleased]\n"
    "\n"
    "### Added\n"
    "\n"
    "### Changed\n"
    "\n"
    "### Deprecated\n"
    "\n"
    "### Removed\n"
    "\n"
    "### Fixed\n"
    "\n"
    "### Security\n"
    "\n"
)
NEW_HEADING = f"## [{version}] - {today}\n"

# Locate the [Unreleased] section: the heading line plus everything up to
# the next `## [` heading (or EOF).
m = re.search(r'^## \[Unreleased\][^\n]*\n', text, flags=re.MULTILINE)
if not m:
    sys.stderr.write("release: lost the [Unreleased] heading between preflight and rotate. Aborting.\n")
    sys.exit(1)
section_start = m.start()
body_start = m.end()
next_section = re.search(r'^## \[', text[body_start:], flags=re.MULTILINE)
section_end = body_start + next_section.start() if next_section else len(text)

before = text[:section_start]
body = text[body_start:section_end]
after = text[section_end:]

# Scrub the body before it becomes the new versioned section:
#   - drop HTML comments (they're authoring guidance, not release notes)
#   - drop empty subheadings (### Foo with no content under them)
# This is the inverse of why we pre-populate subheadings on the fresh
# [Unreleased]: scaffolding belongs in the WIP block, not in the historical
# record. The Keep-a-Changelog convention is "omit empty subsections at
# release time" — we enforce that here so the user doesn't have to.
body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)

# Split into ### subsections and keep only the ones with at least one bullet.
parts = re.split(r'(^### [^\n]*\n)', body, flags=re.MULTILINE)
# parts looks like: [pre, header1, content1, header2, content2, ...]
# pre is anything before the first ### (we drop it: blank lines / stray text).
kept = []
for i in range(1, len(parts), 2):
    header = parts[i]
    content = parts[i + 1] if i + 1 < len(parts) else ""
    # Keep the subsection iff it has at least one bullet with content.
    if re.search(r'^\s*[-*]\s+\S', content, flags=re.MULTILINE):
        kept.append(header + content.rstrip() + "\n\n")

cleaned_body = "".join(kept)
if not cleaned_body:
    # Shouldn't happen — preflight already counted bullets — but guard anyway.
    sys.stderr.write("release: no non-empty subsections in [Unreleased] after scrub. Aborting.\n")
    sys.exit(1)

new_section = NEW_HEADING + "\n" + cleaned_body
new_text = before + FRESH_UNRELEASED + new_section + after

with open(out_path, "w", encoding="utf-8") as f:
    f.write(new_text)
PY

if [[ "$MODE" == "dry-run" ]]; then
  echo "[dry-run] would rotate ## [Unreleased] → ## [${VER_NO_V}] - ${TODAY}"
  echo "[dry-run] diff:"
  diff -u "$CHANGELOG" "$TMP_NEW" || true   # diff exits 1 when files differ
  echo "[dry-run] would commit:  chore: release ${VER_WITH_V}"
  echo "[dry-run] would tag:     ${VER_WITH_V} (annotated, message 'Release ${VER_WITH_V}')"
  echo "[dry-run] would push:    git push && git push --tags"
  echo "[dry-run] would bump:    pyproject.toml ${VER_NO_V} → ${NEXT_DEV}"
  echo "[dry-run] would commit:  chore: bump version to ${NEXT_DEV}"
  echo "[dry-run] would push:    git push"
  echo "[dry-run] (no changes made)"
  exit 0
fi

# ---------------------------------------------------------------------------
# Execute mode — write, commit, tag, push, bump, commit, push.
# ---------------------------------------------------------------------------

cp "$TMP_NEW" "$CHANGELOG"
note "rotated [Unreleased] → [${VER_NO_V}] - ${TODAY}"

# Stage and commit. Hooks run normally — never pass --no-verify.
# GPG signing is inherited from the user's git config (commit.gpgsign,
# tag.gpgsign); this script never overrides it.
git add "$CHANGELOG"
git commit -m "chore: release ${VER_WITH_V}"

# Always annotated. The brief is explicit: -a, not lightweight.
git tag -a "${VER_WITH_V}" -m "Release ${VER_WITH_V}"

# Per brief: `git push && git push --tags`. Functionally equivalent to
# `git push --follow-tags` here (annotated tag reachable from pushed commit),
# but the literal form is what's specified. `--follow-tags` is a one-line
# alternative if the user wants pushed-tag-set narrowing.
git push
git push --tags

RELEASE_SHA="$(git rev-parse --short HEAD)"
note "released ${VER_WITH_V} (commit ${RELEASE_SHA}, tag ${VER_WITH_V} pushed)"

# ---------------------------------------------------------------------------
# Post-release: bump pyproject.toml to the next dev cycle.
#
# This is a separate concern from the release itself. If the tag is later
# deleted (rare, but happens), the dev-cycle bump still stands and there's
# no metadata mismatch. Keeping them in separate commits makes the release
# commit itself a clean "this is what shipped at version X.Y.Z" record.
# ---------------------------------------------------------------------------

python3 - "pyproject.toml" "$VER_NO_V" "$NEXT_DEV" <<'PY'
import re, sys
path, old, new = sys.argv[1:4]
text = open(path, encoding="utf-8").read()

# Match `version = "X.Y.Z"` (TOML, double- or single-quoted) on a line.
# Only replace if the current value equals `old` exactly. This refuses to
# silently bump a project that's already on some other version — that's a
# signal the release flow got out of sync, and the user should investigate.
#
# Scope note: this is a regex pass, not a TOML-table-aware parse. If multiple
# `[tool.X]` sections coincidentally carry `version = "<old>"`, all of them
# would be rewritten. `count=1` on sub() caps the rewrite at the FIRST match
# (which is `[project].version` in any well-formed pyproject.toml). For
# stricter scoping to `[project]`, switch to tomllib + tomli_w in a future
# version — out of scope for v0.1.
pattern = re.compile(
    r'^(?P<lead>\s*version\s*=\s*)(?P<q>["\'])(?P<ver>[^"\']+)(?P=q)',
    flags=re.MULTILINE,
)

found = []
def repl(m):
    found.append(m.group("ver"))
    if m.group("ver") != old:
        return m.group(0)  # leave it; we'll error after
    return f'{m.group("lead")}{m.group("q")}{new}{m.group("q")}'

new_text = pattern.sub(repl, text, count=1)

if not found:
    sys.stderr.write(f"release: no 'version = \"...\"' line found in {path}.\n")
    sys.exit(1)
if old not in found:
    sys.stderr.write(
        f"release: pyproject.toml version is {found[0]!r}, expected {old!r}. "
        "Did the release commit modify pyproject.toml? Aborting bump.\n"
    )
    sys.exit(1)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_text)
PY

git add pyproject.toml
git commit -m "chore: bump version to ${NEXT_DEV}"
git push

BUMP_SHA="$(git rev-parse --short HEAD)"
note "bumped pyproject.toml ${VER_NO_V} → ${NEXT_DEV} (commit ${BUMP_SHA} pushed)"
note "done."
