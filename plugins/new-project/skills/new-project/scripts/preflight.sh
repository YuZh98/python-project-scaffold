#!/usr/bin/env bash
# Preflight checks for the new-project skill.
#
# Refuses cleanly (non-zero exit, message on stderr) if the environment is
# not ready to scaffold a fresh Python repo. Writes nothing.
#
# Checks (in order):
#   1. cwd is NOT inside an existing git repo (skill creates a new sibling dir)
#   2. `gh` is installed and authenticated with sufficient scope
#   3. git global user.name + user.email are configured
#   4. python3 is available (init-project.py needs it)
#   5. make is available (scaffold's setup phase uses it)
#   6. git is available (we clone the scaffold at a pinned tag and run init-project.py)
#
# Side effects: prints the active gh login to stdout on success (so the
# orchestrator can capture it). Diagnostics go to stderr.

set -euo pipefail

die() {
  echo "preflight: $*" >&2
  exit 1
}

# 1. Refuse if inside a git repo. The skill creates a new directory below cwd;
#    nesting a fresh repo inside an existing one is almost never what the user
#    wants and silently confuses git.
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  die "refusing to run inside an existing git repo. cd to a parent directory and re-invoke."
fi

# 2. gh authenticated. Without this, repo creation + branch protection fail
#    mid-flow and leave a confusing local-only repo.
if ! command -v gh >/dev/null 2>&1; then
  die "gh CLI not installed. Install from https://cli.github.com/ and run 'gh auth login'."
fi
if ! gh auth status >/dev/null 2>&1; then
  die "gh is not authenticated. Run 'gh auth login' (needs 'repo' scope). Multiple accounts: 'gh auth switch'."
fi

# 3. git identity. The scaffold's first commit uses these; missing values
#    produce a commit attributed to "(none)" which is hard to fix later.
if [[ -z "$(git config --global user.name 2>/dev/null || true)" ]]; then
  die "git user.name is unset. Run: git config --global user.name '<name>'"
fi
if [[ -z "$(git config --global user.email 2>/dev/null || true)" ]]; then
  die "git user.email is unset. Run: git config --global user.email '<email>'"
fi

# 4. python3. init-project.py is python; without it bootstrap is a non-starter.
if ! python3 --version >/dev/null 2>&1; then
  die "python3 not found. Install Python 3.11+ and retry."
fi

# 5. make. The scaffold's post-init setup phase invokes `make install`.
if ! make --version >/dev/null 2>&1; then
  die "make not found. macOS: xcode-select --install   Linux: sudo apt install build-essential"
fi

# 6. git. We clone the scaffold at a pinned tag and run init-project.py directly.
if ! git --version >/dev/null 2>&1; then
  die "git not found. macOS: xcode-select --install   Linux: sudo apt install git"
fi

# Success. Emit the active gh login so the orchestrator can use it.
gh api user --jq .login
