# Claude Plugin v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship v0.1.0 of the python-project-scaffold Claude Code plugin to a self-hosted marketplace in the same repo. Plugin packages 4 already-created skills (`new-project`, `release-helper`, `changelog-normalizer`, `audit-runner`) with full manifests, supporting docs, CI gates, and migration cleanup.

**Architecture:** Approach B — conventional Claude Code plugin layout. `.claude-plugin/marketplace.json` at repo root advertises one plugin at `plugins/new-project/`. Plugin has own `plugin.json` + own `CHANGELOG.md`, decoupled from scaffold versioning. Spec source: `docs/superpowers/specs/2026-05-14-claude-plugin-design.md`.

**Tech Stack:** Bash + Python 3.11+ for scripts. JSON for manifests. Markdown for docs. GitHub Actions for CI. `gh` CLI for marketplace publishing path.

**Current state:** All 4 skills exist under `plugins/new-project/skills/`. Reviewer-found blocker + 4 majors already fixed. Spec section 5.3 (changelog-normalizer) was revised by user after skill creation — Phase 3 reconciles the existing skill to match the revised spec.

---

## Phase 1 — Plugin Manifests

### Task 1: Create `.claude-plugin/marketplace.json`

**Files:**
- Create: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Verify schema reference**

The Claude Code marketplace manifest schema is documented at https://docs.claude.com/en/docs/claude-code/plugins-marketplaces. Required top-level fields: `name`, `owner`, `plugins[]`. Each plugin entry needs `name`, `source`, `description`.

- [ ] **Step 2: Create the file**

```json
{
  "name": "python-project-scaffold",
  "owner": {
    "name": "YuZh98",
    "url": "https://github.com/YuZh98"
  },
  "plugins": [
    {
      "name": "new-project",
      "source": "./plugins/new-project",
      "description": "Python project scaffolding toolkit: scaffold new repos, run release flows, normalize CHANGELOGs, and run pre-PR audits using a scaffold-aware framework."
    }
  ]
}
```

- [ ] **Step 3: Validate JSON syntax**

Run: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))" && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add marketplace manifest for self-hosted plugin distribution"
```

---

### Task 2: Create `plugins/new-project/plugin.json`

**Files:**
- Create: `plugins/new-project/plugin.json`

- [ ] **Step 1: Create the manifest**

```json
{
  "name": "new-project",
  "version": "0.1.0",
  "description": "Scaffold Python projects, normalize CHANGELOGs, automate releases, and run pre-PR audits.",
  "author": {
    "name": "YuZh98",
    "url": "https://github.com/YuZh98"
  },
  "homepage": "https://github.com/YuZh98/python-project-scaffold",
  "license": "MIT",
  "keywords": ["python", "scaffold", "changelog", "release", "audit"]
}
```

- [ ] **Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('plugins/new-project/plugin.json'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add plugins/new-project/plugin.json
git commit -m "feat: add plugin manifest (v0.1.0)"
```

---

## Phase 2 — Plugin-Internal Supporting Docs

### Task 3: Create `plugins/new-project/README.md`

**Files:**
- Create: `plugins/new-project/README.md`

- [ ] **Step 1: Write the README**

```markdown
# new-project (Claude Code plugin)

Scaffold-aware Claude Code skills for Python project lifecycle:

- **new-project** — scaffold fresh Python repos via `python-project-scaffold`
- **release-helper** — automate the release sequence (rotate CHANGELOG, tag, push)
- **changelog-normalizer** — normalize CHANGELOGs to consistent Keep-a-Changelog style
- **audit-runner** — pre-PR independent audit using an 11-dimension framework

## Install

```bash
/plugin marketplace add YuZh98/python-project-scaffold
/plugin install new-project@python-project-scaffold
```

## Usage

Each skill auto-triggers on natural language. See each `skills/<name>/SKILL.md` for trigger phrases and IO examples.

## Requirements

- `git` (the `new-project` skill clones the scaffold at a pinned tag)
- `gh` CLI with authentication (`gh auth login`)
- Python 3.11+
- `make`

## Version

See `CHANGELOG.md`.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/new-project/README.md
git commit -m "docs: add plugin README with install + usage"
```

---

### Task 4: Create `plugins/new-project/CHANGELOG.md`

**Files:**
- Create: `plugins/new-project/CHANGELOG.md`

- [ ] **Step 1: Write initial CHANGELOG**

```markdown
# Changelog

All notable changes to the new-project plugin. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions: [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
### Changed
### Fixed
### Removed
### Deprecated
### Security

## [0.1.0] - 2026-05-14

Initial plugin release. Packages four scaffold-aware skills for the Python project lifecycle.

### Added
- Scaffold a fresh Python repo via natural-language invocation. Refactored from the existing hand-written skill into a thin orchestrator plus `scripts/*.sh`; reduces context load per invocation. (#1)
- Automate the release sequence (rotate `[Unreleased]`, commit, annotated tag, push, version bump). Composes the changelog-normalizer skill as a pre-step. (#1)
- Normalize `CHANGELOG.md` entries to a consistent Keep-a-Changelog style. Strips process narrative, enforces subheading order, refuses to fabricate refs. (#1)
- Run pre-PR audits using an 11-dimension framework with two-axis mode flags (scope + depth). Coordinator agent walks 6 core dims; on-demand sub-agents spawn for context-aware dims when surface triggers are detected in the diff. (#1)

[Unreleased]: https://github.com/YuZh98/python-project-scaffold/compare/plugin-v0.1.0...HEAD
[0.1.0]: https://github.com/YuZh98/python-project-scaffold/releases/tag/plugin-v0.1.0
```

- [ ] **Step 2: Commit**

```bash
git add plugins/new-project/CHANGELOG.md
git commit -m "docs: add plugin CHANGELOG with v0.1.0 entry"
```

---

### Task 5: Create `plugins/new-project/LICENSE`

**Files:**
- Create: `plugins/new-project/LICENSE`

- [ ] **Step 1: Inherit root LICENSE via copy**

Run: `cp LICENSE plugins/new-project/LICENSE`

Verify: `head -1 plugins/new-project/LICENSE`
Expected: License text first line (e.g. `MIT License`).

- [ ] **Step 2: Commit**

```bash
git add plugins/new-project/LICENSE
git commit -m "docs: copy LICENSE into plugin dir"
```

---

### Task 6: Create `plugins/new-project/SKILL_AUTHORING.md`

**Files:**
- Create: `plugins/new-project/SKILL_AUTHORING.md`

- [ ] **Step 1: Write the universal convention doc**

```markdown
# SKILL.md Authoring Convention

Every SKILL.md in this plugin MUST include the four sections below. New skills follow the same shape; existing skills are pinned to it by `tests/test_skill_convention.py`.

## Required sections

1. **Trigger examples** — natural-language phrasings that should activate this skill. List at least 4. Distinct enough from other skills in the plugin to prevent wrong-skill activation.

2. **IO examples** — at least 3 concrete input/output pairs:
   - Golden path: typical successful invocation
   - Edge case A: a refuse/failure case the skill must handle cleanly
   - Edge case B: an ambiguity the skill resolves by asking the user

3. **Drift policy** — explicit rule for when the skill must ask the user before producing output. If the user request diverges substantively from the IO examples, the skill asks confirmation rather than extrapolate.

4. **Concrete output examples** — what the skill produces. For text-output skills (e.g. `changelog-normalizer`), include reference examples or links to canonical examples. For action-output skills (e.g. `new-project`), include a sample of the final shell output the user will see.

## Why these four

- Trigger examples anchor what activates the skill (prevents drift in classification)
- IO examples anchor what the skill produces (prevents drift in behavior)
- Drift policy anchors what to do when the request leaves the anchor zone (prevents silent extrapolation)
- Output examples anchor what "done" looks like (prevents partial completion)

## Peer-skill invocation

When one skill in this plugin composes another (e.g. `release-helper` calls `changelog-normalizer`), describe the composition in prose AND quote the invocation form:

> Invokes the `changelog-normalizer` skill on `CHANGELOG.md` as a pre-step.

Do not use pseudo-syntax like `Skill(skill="...")` — that varies by runtime. Prose first, runtime-specific syntax only inside scripts that actually execute.

## Forbidden in any SKILL.md

- `Co-Authored-By: Claude` mentions
- Process narrative ("after an audit pass", "per Claude review")
- Magic numbers (use named constants in scripts)
- `print()` debug statements (use logging or remove)

These mirror the user's global `CLAUDE.md` rules and are enforced at PR-audit time by `audit-runner`.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/new-project/SKILL_AUTHORING.md
git commit -m "docs: add SKILL.md authoring convention for plugin skills"
```

---

## Phase 3 — Reconcile changelog-normalizer with Revised Spec 5.3

The spec section 5.3 was revised after the skill was created. Update the skill + Python script to match.

### Task 7: Add first-time-invocation Q&A to changelog-normalizer SKILL.md

**Files:**
- Modify: `plugins/new-project/skills/changelog-normalizer/SKILL.md`

- [ ] **Step 1: Read current SKILL.md to locate insertion point**

Run: `head -50 plugins/new-project/skills/changelog-normalizer/SKILL.md`

Expected: see existing trigger examples + drift policy sections.

- [ ] **Step 2: Insert first-time-invocation section after trigger examples**

Add immediately after the "Trigger examples" section:

```markdown
## First-time invocation (per project)

Before the first rewrite in any project, ask the user two setup questions and cache the answers in skill state (e.g. a `.claude/changelog-normalizer.json` at the project root):

1. **Mention `Co-Authored-By: Claude` in entries?** — default: no. The user's global `CLAUDE.md` §1 forbids AI/agent mentions in committed artifacts.
2. **Prose preference: concise or verbose?** — default: concise (one-line, user-impact framing). Verbose allows multi-sentence entries when the change genuinely needs context.

On subsequent invocations, load the cached answers without re-prompting unless the user explicitly says "reset changelog preferences".
```

- [ ] **Step 3: Commit**

```bash
git add plugins/new-project/skills/changelog-normalizer/SKILL.md
git commit -m "feat: add first-time invocation Q&A to changelog-normalizer"
```

---

### Task 8: Replace BEFORE/AFTER examples with embedded production excerpts + reference links

**Files:**
- Modify: `plugins/new-project/skills/changelog-normalizer/SKILL.md`

- [ ] **Step 1: Locate the BEFORE/AFTER section**

Run: `grep -n "BEFORE\|AFTER" plugins/new-project/skills/changelog-normalizer/SKILL.md | head -20`

Expected: a list of line numbers where the existing BEFORE/AFTER pairs live.

- [ ] **Step 2: Replace the BEFORE/AFTER section with embedded production excerpts**

Per spec §5.3 "Concrete output examples (REQUIRED in SKILL.md)", embed verbatim excerpts from production CHANGELOGs. These satisfy the universal SKILL.md convention's "concrete output examples" requirement without external lookup. Replace the existing BEFORE/AFTER section with this content. Preserve everything before and after it.

````markdown
## Concrete output examples

These verbatim excerpts from production CHANGELOGs anchor "what good output looks like."

### Example A — single-sentence summary + multi-entry Fixed section

From `python-project-scaffold/CHANGELOG.md` v1.7.7:

```markdown
## [v1.7.7] - 2026-05-14

Correctness fixes found by independent multi-agent audit. The most impactful: non-MIT license files were being generated with incorrect text (a condensed paraphrase of Apache-2.0 instead of the full SPDX text), and several shell-level guards that the skill described in prose weren't actually enforced.

### Fixed
- Apache-2.0 license text was a condensed paraphrase; replaced with the full canonical SPDX verbatim. (#18)
- Non-MIT license rewrite used `cd` to change directories, which doesn't persist across tool calls; now uses `git -C` to operate without changing cwd. (#18)
- Dry-run relied on Claude reading instructions to skip GitHub steps; now an explicit shell gate exits before any network operation. (#18)
- Bootstrapping into an existing directory produced undefined behaviour; skill now aborts with a clear message if the target path already exists. (#18)
- License script was sourced from a hardcoded install path, breaking for users who copied only SKILL.md; now tries the bundled path first and falls back to the cloned scaffold. (#18)
```

### Example B — small release with Added + Changed

From `python-project-scaffold/CHANGELOG.md` v1.7.6:

```markdown
## [v1.7.6] - 2026-05-13

The skill can now be installed with a single command. CI automatically builds a `.skill` zip file and attaches it to every GitHub Release on tag push — no manual packaging step needed.

### Added
- CI workflow that builds and uploads `new-project.skill` to GitHub Releases on every version tag. (#15)

### Changed
- README install instructions updated to use `gh release download --latest`. (#15)
```

### Example C — concise refactor entry

From `python-project-scaffold/CHANGELOG.md` v1.7.5:

```markdown
## [v1.7.5] - 2026-05-13

Skill cut from 452 to 212 lines. License texts moved to a bundled helper script that loads only when needed; several redundant sections removed.

### Changed
- Skill condensed 53%; license texts extracted to `scripts/write_license.py`. (#14)
```

### What these examples illustrate

- One-sentence summary leads each version, explaining what the release is *about* in user-impact terms
- Entries say WHAT changed and WHY it matters; HOW (file paths, step numbers) is omitted
- Imperative mood frames the change
- Each entry ends with `(#PR)` or `(commit-hash)` in parens
- No process narrative, no `Co-Authored-By: Claude`, no bolding overuse

### Reference link (additional canonical examples)

- `https://github.com/YuZh98/python-project-scaffold/blob/main/CHANGELOG.md?plain=1`
- `https://github.com/YuZh98/latex2arxiv/blob/main/CHANGELOG.md?plain=1`

These stay current as the linked CHANGELOGs evolve. For patterns not covered by Examples A-C, point the user at the relevant section of these files.
````

- [ ] **Step 3: Commit**

```bash
git add plugins/new-project/skills/changelog-normalizer/SKILL.md
git commit -m "docs: embed concrete production changelog excerpts as SKILL.md examples"
```

---

### Task 8b: Update `audit-runner/dimensions/docs.md` to add DESIGN/GUIDELINES drift sweeps

**Files:**
- Modify: `plugins/new-project/skills/audit-runner/dimensions/docs.md`

- [ ] **Step 1: Read current docs.md**

Run: `cat plugins/new-project/skills/audit-runner/dimensions/docs.md`

- [ ] **Step 2: Add the new sub-checks per revised spec §5.4 dim #5**

Add a new subsection "DESIGN.md / GUIDELINES.md drift sweeps" with two checks. The checklist below adds these to the existing checklist; integrate so they appear in the same checklist style the file already uses (do not duplicate format):

```markdown
## DESIGN.md / GUIDELINES.md drift sweeps

These are checks for written-doc rot in long-lived design and rule files. Run them when the diff touches `DESIGN.md`, `GUIDELINES.md`, ADRs under `docs/adr/`, or any file the diff comments reference.

### History-as-guidance check

Past decisions stated as binding when current context has shifted. Look for:
- Rules whose stated rationale no longer holds (cite the rule + the diff that invalidated the rationale)
- Decisions that read as "we did X for reason Y" when Y is gone
- "Current practice is Z" statements that the diff contradicts
- ADRs marked `Accepted` whose substance has been superseded without a `Superseded by` link

The fix is usually a one-line status update, a supersession marker, or a rewrite of the rationale — not a wholesale removal.

### WHAT-vs-HOW/WHY overspec check

DESIGN/GUIDELINES files are intended for decisions and surviving rationale. Implementation details belong in code. Look for:
- Step-by-step recipes (move to runbook or script docstring)
- File-path enumerations that will rot as the codebase moves
- "Currently we use library X version Y.Z" specifics (move to `pyproject.toml`)
- HOW or WHY prose where WHAT alone suffices (e.g. "We use snake_case" needs no chapter on snake_case history)

Severity guide: drift in DESIGN.md = major when active code disagrees; minor when prose is correct but stale. Overspec = minor unless the recipe is wrong (then major).
```

- [ ] **Step 3: Validate the file is still well-formed markdown**

Run: `head -1 plugins/new-project/skills/audit-runner/dimensions/docs.md && wc -l plugins/new-project/skills/audit-runner/dimensions/docs.md`
Expected: file starts with a `#` heading and line count grew (not zero).

- [ ] **Step 4: Commit**

```bash
git add plugins/new-project/skills/audit-runner/dimensions/docs.md
git commit -m "feat: add DESIGN/GUIDELINES drift sweeps to audit-runner docs dimension"
```

---

### Task 9: Add one-sentence version-summary rule to SKILL.md

**Files:**
- Modify: `plugins/new-project/skills/changelog-normalizer/SKILL.md`

- [ ] **Step 1: Add rule in the "Structural rules" subsection**

Insert this bullet near the start of structural rules:

```markdown
- Each version section opens with a **one-sentence summary** of what the release is about, before any `###` subheading. Enforced by `template/tests/test_cohesion.py::TestChangelogFormat`.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/new-project/skills/changelog-normalizer/SKILL.md
git commit -m "docs: require one-sentence version summary per release"
```

---

### Task 10: Add WHAT/WHY-over-HOW + grouping rules to SKILL.md

**Files:**
- Modify: `plugins/new-project/skills/changelog-normalizer/SKILL.md`

- [ ] **Step 1: Add content-rules subsection if not present, with these bullets**

```markdown
## Content rules

- **WHAT changes and WHY it matters, not HOW.** Skip file paths, step numbers, implementation details.
- Group related changes into ONE bullet at the user-impact level (imperative mood).
  - Poor: `Step 5: replaced cd with git -C in the license-amend block.`
  - Good: `Fix license rewrite silently failing when shell cwd doesn't persist.`
- End each entry with PR# or commit hash in parens — e.g. `(#42)` or `(abc1234)`.
- Strip process narrative: any mention of `Claude`, `agent`, `audit pass`, `AI`, `re-audit`, review iterations.
- Do not overuse bolding (`**text**`) — sparingly, for genuine emphasis only.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/new-project/skills/changelog-normalizer/SKILL.md
git commit -m "docs: add content rules (WHAT/WHY over HOW; user-impact grouping)"
```

---

### Task 11: Add state-cache support to `normalize_changelog.py`

**Files:**
- Modify: `plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py`

- [ ] **Step 1: Write the failing test**

Create `tests/skills/changelog_normalizer/test_state_cache.py`:

```python
import json
from pathlib import Path
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                      / "plugins/new-project/skills/changelog-normalizer/scripts"))
from normalize_changelog import load_preferences, save_preferences  # noqa: E402


class TestStateCache(unittest.TestCase):
    def test_load_returns_defaults_when_no_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prefs = load_preferences(Path(tmp))
            self.assertEqual(prefs.mention_coauthor, False)
            self.assertEqual(prefs.prose_style, "concise")

    def test_save_then_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            save_preferences(Path(tmp), mention_coauthor=False, prose_style="verbose")
            prefs = load_preferences(Path(tmp))
            self.assertEqual(prefs.prose_style, "verbose")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/skills/changelog_normalizer/test_state_cache.py -v`
Expected: FAIL with `ImportError: cannot import name 'load_preferences'`.

- [ ] **Step 3: Add the implementation**

Append to `plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py`:

```python
# ---------------------------------------------------------------------------
# Preferences cache
# ---------------------------------------------------------------------------

from dataclasses import dataclass
import json as _json_for_prefs


PREFERENCES_FILENAME = ".claude/changelog-normalizer.json"


@dataclass
class Preferences:
    mention_coauthor: bool = False
    prose_style: str = "concise"  # "concise" | "verbose"


def load_preferences(project_root: Path) -> Preferences:
    """Load cached preferences for this project, or defaults if missing."""
    cache_path = project_root / PREFERENCES_FILENAME
    if not cache_path.exists():
        return Preferences()
    data = _json_for_prefs.loads(cache_path.read_text())
    return Preferences(
        mention_coauthor=bool(data.get("mention_coauthor", False)),
        prose_style=str(data.get("prose_style", "concise")),
    )


def save_preferences(project_root: Path, *, mention_coauthor: bool, prose_style: str) -> None:
    """Persist preferences to the project-local cache."""
    cache_path = project_root / PREFERENCES_FILENAME
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(_json_for_prefs.dumps({
        "mention_coauthor": mention_coauthor,
        "prose_style": prose_style,
    }, indent=2) + "\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/skills/changelog_normalizer/test_state_cache.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py \
        tests/skills/changelog_normalizer/test_state_cache.py
git commit -m "feat: add per-project preferences cache to changelog-normalizer"
```

---

## Phase 4 — Repo-Level Supporting Artifacts

### Task 12: Add ADR for decoupled plugin versioning

**Files:**
- Create: `docs/adr/0001-decoupled-plugin-versioning.md`

- [ ] **Step 1: Check ADR numbering**

Run: `ls docs/adr/ 2>/dev/null || mkdir -p docs/adr`

Pick the next available number. If `0001-…` exists, use the next sequential number.

- [ ] **Step 2: Write the ADR**

```markdown
# ADR 0001: Decoupled scaffold and plugin versioning

**Status:** Accepted
**Date:** 2026-05-14

## Context

This repository hosts two products in a monorepo:
- the python-project-scaffold CLI (`scripts/init-project.py` + `template/`)
- the Claude Code plugin (`plugins/new-project/`)

The plugin consumes the scaffold (its `new-project` skill clones the scaffold at a pinned tag and runs `init-project.py`). Two options for versioning:

1. **Lockstep:** plugin version == scaffold version. Every scaffold release re-publishes the plugin; every plugin change forces a scaffold release.
2. **Decoupled:** plugin and scaffold version independently. Plugin pins which scaffold tag it was tested against.

## Decision

Use decoupled versioning. The plugin maintains its own `plugins/new-project/CHANGELOG.md` and its own `plugin.json` version (initial: `0.1.0`). The scaffold continues using its existing top-level `CHANGELOG.md` and tag scheme (`vX.Y.Z`). Plugin tags use a separate prefix: `plugin-vX.Y.Z`.

## Consequences

**Positive:**
- Plugin can ship skill prose fixes without forcing a scaffold release
- Scaffold can ship internal-only changes without re-publishing the plugin
- Independent release cadences match the products' actual change rates

**Negative:**
- Two CHANGELOGs in one repo — risk of routing confusion. Mitigated by the routing rule documented in `CONTRIBUTING.md`.
- Cross-cutting changes (plugin needs new scaffold flag) require entries in BOTH CHANGELOGs and a scaffold release before the plugin release.

## Alternatives considered

- **Lockstep:** rejected — forces scaffold bump for plugin-only changes
- **Single CHANGELOG with sub-sections:** rejected — readers expect one CHANGELOG per published artifact
```

- [ ] **Step 3: Commit**

```bash
git add docs/adr/0001-decoupled-plugin-versioning.md
git commit -m "docs: add ADR 0001 for decoupled scaffold/plugin versioning"
```

---

### Task 13: Add dual-changelog routing rule to CONTRIBUTING.md

**Files:**
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Read current CONTRIBUTING.md**

Run: `cat CONTRIBUTING.md`

Identify where to add the routing section (likely after an existing "Commit" or "PR" section).

- [ ] **Step 2: Append the routing rule**

Append this section:

```markdown
## CHANGELOG routing (scaffold vs plugin)

This monorepo has two CHANGELOGs. Route entries by what changed:

| What changed | CHANGELOG to update |
|---|---|
| `scripts/init-project.py`, `template/`, scaffold-only files | Top-level `CHANGELOG.md` |
| `plugins/new-project/**` (skills, scripts, manifests, docs) | `plugins/new-project/CHANGELOG.md` |
| Cross-cutting (e.g. plugin adds flag requiring scaffold support) | Entry in BOTH CHANGELOGs, with a one-line cross-reference linking the partner entry |

Cross-cutting changes additionally require a scaffold release BEFORE the plugin release that consumes the new feature, so the plugin's pinned `SCAFFOLD_VERSION` can be advanced to a tag that includes the new behavior.

See `docs/adr/0001-decoupled-plugin-versioning.md` for the why.
```

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add dual-CHANGELOG routing rule (scaffold vs plugin)"
```

---

## Phase 5 — CI Gates

### Task 14: Scaffold ↔ plugin contract test

The plugin's `bootstrap.sh` shells out to `scripts/init-project.py` with specific flags (`--target`, `--values`, `--yes`). Lock the flag surface so a scaffold refactor that renames flags breaks CI BEFORE it breaks the plugin at runtime.

**Files:**
- Create: `tests/contracts/test_init_project_cli.py`
- Create: `.github/workflows/plugin-contract.yml`

- [ ] **Step 1: Write the contract test**

Create `tests/contracts/test_init_project_cli.py`:

```python
"""Contract test: plugin's bootstrap.sh depends on these init-project.py flags."""
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FLAGS = {"--target", "--values", "--yes"}


class TestInitProjectCLI(unittest.TestCase):
    def test_required_flags_present_in_help(self) -> None:
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "scripts" / "init-project.py"), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        help_text = result.stdout + result.stderr
        for flag in REQUIRED_FLAGS:
            self.assertIn(
                flag,
                help_text,
                f"plugin depends on {flag}; init-project.py --help no longer mentions it",
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test locally to verify it passes**

Run: `python3 -m pytest tests/contracts/test_init_project_cli.py -v`
Expected: PASS (1 passed) — assuming `init-project.py --help` currently shows all three flags.

If it fails, the plugin's `bootstrap.sh` is out of sync with the actual scaffold CLI. Investigate before continuing.

- [ ] **Step 3: Create the CI workflow**

Create `.github/workflows/plugin-contract.yml`:

```yaml
name: Plugin contract

on:
  pull_request:
    paths:
      - "scripts/init-project.py"
      - "plugins/new-project/skills/new-project/scripts/bootstrap.sh"
      - "tests/contracts/**"
      - ".github/workflows/plugin-contract.yml"
  push:
    branches: [main]

jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run contract test
        run: python3 -m pytest tests/contracts/ -v
```

- [ ] **Step 4: Validate workflow YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/plugin-contract.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add tests/contracts/test_init_project_cli.py .github/workflows/plugin-contract.yml
git commit -m "test: pin plugin↔scaffold CLI contract via init-project.py --help"
```

---

### Task 15: Plugin smoke test (install + invoke)

**Files:**
- Create: `tests/skills/test_plugin_smoke.py`
- Create: `.github/workflows/plugin-smoke.yml`

- [ ] **Step 1: Write the smoke test**

Create `tests/skills/test_plugin_smoke.py`:

```python
"""Smoke test: plugin files exist, manifests parse, surface_detect runs on empty diff."""
import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "new-project"
SKILLS_ROOT = PLUGIN_ROOT / "skills"
SKILL_NAMES = ["new-project", "release-helper", "changelog-normalizer", "audit-runner"]


class TestPluginSmoke(unittest.TestCase):
    def test_marketplace_manifest_parses(self) -> None:
        data = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
        self.assertEqual(data["name"], "python-project-scaffold")
        self.assertEqual(len(data["plugins"]), 1)

    def test_plugin_manifest_parses(self) -> None:
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        self.assertEqual(data["name"], "new-project")
        self.assertTrue(data["version"])

    def test_all_skills_have_skill_md(self) -> None:
        for name in SKILL_NAMES:
            skill_md = SKILLS_ROOT / name / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"missing {skill_md}")

    def test_surface_detect_on_empty_diff(self) -> None:
        result = subprocess.run(
            ["python3", str(SKILLS_ROOT / "audit-runner" / "scripts" / "surface_detect.py")],
            input="",
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run locally to verify it passes**

Run: `python3 -m pytest tests/skills/test_plugin_smoke.py -v`
Expected: PASS (4 passed).

- [ ] **Step 3: Create CI workflow**

Create `.github/workflows/plugin-smoke.yml`:

```yaml
name: Plugin smoke

on:
  pull_request:
    paths:
      - "plugins/**"
      - ".claude-plugin/**"
      - "tests/skills/**"
      - ".github/workflows/plugin-smoke.yml"
  push:
    branches: [main]

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run plugin smoke tests
        run: python3 -m pytest tests/skills/ -v
```

- [ ] **Step 4: Validate YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/plugin-smoke.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add tests/skills/test_plugin_smoke.py .github/workflows/plugin-smoke.yml
git commit -m "test: plugin smoke (manifests parse, skills present, surface_detect runs)"
```

---

### Task 16: SKILL.md convention pinning test

**Files:**
- Create: `tests/skills/test_skill_convention.py`

- [ ] **Step 1: Write the pinning test**

Per global rule §7 ("no rule lands without enforcement"), the universal SKILL.md convention defined in `SKILL_AUTHORING.md` must have a passing test.

Create `tests/skills/test_skill_convention.py`:

```python
"""Pin the universal SKILL.md authoring convention from SKILL_AUTHORING.md."""
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "plugins" / "new-project" / "skills"

REQUIRED_SECTION_KEYWORDS = [
    "Trigger",       # Trigger examples
    "IO examples",   # IO examples / Input-output
    "Drift",         # Drift policy
    "output",        # Concrete output examples
]


class TestSkillConvention(unittest.TestCase):
    def test_each_skill_md_contains_required_sections(self) -> None:
        skill_dirs = [p for p in SKILLS_ROOT.iterdir() if p.is_dir()]
        self.assertGreaterEqual(len(skill_dirs), 4, "expected 4 skills")
        for d in skill_dirs:
            content = (d / "SKILL.md").read_text().lower()
            for keyword in REQUIRED_SECTION_KEYWORDS:
                self.assertIn(
                    keyword.lower(),
                    content,
                    f"{d.name}/SKILL.md missing required keyword: {keyword}",
                )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run locally**

Run: `python3 -m pytest tests/skills/test_skill_convention.py -v`
Expected: PASS. If any skill is missing a keyword, the test surfaces which one.

- [ ] **Step 3: Commit**

```bash
git add tests/skills/test_skill_convention.py
git commit -m "test: pin SKILL.md authoring convention (trigger/IO/drift/output sections)"
```

---

### Task 17: changelog-normalizer `--check` gate on plugin CHANGELOG

**Files:**
- Modify: `.github/workflows/plugin-smoke.yml` (add step)

- [ ] **Step 1: Add a step to the smoke workflow**

Edit `.github/workflows/plugin-smoke.yml`. Append this step under `jobs.smoke.steps`:

```yaml
      - name: Normalize-check plugin CHANGELOG
        run: |
          python3 plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py \
            plugins/new-project/CHANGELOG.md --check
```

- [ ] **Step 2: Validate YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/plugin-smoke.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 3: Verify the check passes on current CHANGELOG**

Run: `python3 plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py plugins/new-project/CHANGELOG.md --check`
Expected: exit 0 (no violations). If violations are reported, fix the plugin CHANGELOG so it conforms — that IS the rule landing.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/plugin-smoke.yml
git commit -m "ci: gate plugin CHANGELOG on changelog-normalizer --check"
```

---

## Phase 6 — Self-Audit Before Tag

The audit-runner skill exists. Eat our own dogfood: run it on the v0.1 diff before tagging.

### Task 18: Run audit-runner on the v0.1 diff

**Files:** (none modified by this task — outputs are advisory)

- [ ] **Step 1: Generate the diff for review**

Run: `git diff main...HEAD > /tmp/plugin-v0.1.diff`

If you're not on a feature branch, generate the diff covering all the commits from this plan:
`git log --oneline | head -30` to identify the starting commit, then `git diff <start-sha>..HEAD > /tmp/plugin-v0.1.diff`.

- [ ] **Step 2: Run surface_detect on the diff**

Run: `python3 plugins/new-project/skills/audit-runner/scripts/surface_detect.py --diff-file /tmp/plugin-v0.1.diff --pretty`

Expected: JSON list (likely with `dependency_hygiene` triggers from `plugin.json` and `marketplace.json`).

- [ ] **Step 3: Invoke audit-runner skill via Claude with the diff**

In Claude Code, in the repo root, run a turn:
> Audit the v0.1 plugin diff at /tmp/plugin-v0.1.diff against the spec at docs/superpowers/specs/2026-05-14-claude-plugin-design.md. Use scope=all depth=major+.

The audit-runner skill should produce a findings table.

- [ ] **Step 4: Triage findings**

For each blocker or major finding:
- If valid: create a follow-up task in this plan or fix immediately
- If invalid: note in the review doc why

For minor / nit: file as follow-up GitHub issues, do not block v0.1.

- [ ] **Step 5: Save the audit report**

Save the audit output to `docs/superpowers/audits/2026-05-14-plugin-v0.1-audit.md` for posterity:

```bash
mkdir -p docs/superpowers/audits
# (paste the audit report content into the file)
git add docs/superpowers/audits/2026-05-14-plugin-v0.1-audit.md
git commit -m "review: capture pre-tag audit of plugin v0.1 diff"
```

---

## Phase 7 — Migration & Cleanup

### Task 19: Mark `tooling/claude-code/` deprecated (do not delete yet)

**Files:**
- Create: `tooling/claude-code/DEPRECATED.md`

- [ ] **Step 1: Write the deprecation notice**

```markdown
# DEPRECATED

This directory is the previous home of the hand-written `new-project` Claude Code skill. As of plugin v0.1.0 (2026-05-14), the skill lives at `plugins/new-project/skills/new-project/` and is distributed via the marketplace at `.claude-plugin/marketplace.json`.

## Migration for existing users

If you previously installed the skill manually at `~/.claude/skills/new-project/`:

```bash
rm -rf ~/.claude/skills/new-project/
# Then in Claude Code:
/plugin marketplace add YuZh98/python-project-scaffold
/plugin install new-project@python-project-scaffold
```

## Scheduled removal

This directory will be removed in plugin v0.2.0 or scaffold v1.8.0, whichever ships first.
```

- [ ] **Step 2: Commit**

```bash
git add tooling/claude-code/DEPRECATED.md
git commit -m "docs: deprecate tooling/claude-code/ (superseded by plugin)"
```

---

### Task 20: Update top-level README.md to mention the plugin

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Locate the install/usage section**

Run: `head -40 README.md`

- [ ] **Step 2: Add a plugin section after the scaffold install section**

Append this section (adjust placement to fit existing structure):

```markdown
## Claude Code plugin

This repo also ships a Claude Code plugin that wraps the scaffold (and ships sibling skills for releases, changelog normalization, and pre-PR audits).

```bash
/plugin marketplace add YuZh98/python-project-scaffold
/plugin install new-project@python-project-scaffold
```

See `plugins/new-project/README.md` for details.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: link to Claude Code plugin from top-level README"
```

---

### Task 21: Update top-level CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md` (scaffold's CHANGELOG)

- [ ] **Step 1: Add entry under `[Unreleased]`**

Add this entry under the appropriate subheading:

```markdown
### Added
- Claude Code plugin (`plugins/new-project/`) packaging the scaffold's existing skill plus three sibling skills (release-helper, changelog-normalizer, audit-runner). Distributed via self-hosted marketplace at `.claude-plugin/marketplace.json`. See ADR 0001 for the decoupled-versioning rationale. (#1)
```

- [ ] **Step 2: Run normalize-check**

Run: `python3 plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py CHANGELOG.md --check`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: note Claude Code plugin in scaffold CHANGELOG"
```

---

## Phase 8 — Tag & Publish

### Task 22: Tag plugin v0.1.0

**Files:** (none modified)

- [ ] **Step 1: Verify all CI passes locally**

Run:
```bash
python3 -m pytest tests/contracts/ tests/skills/ -v
python3 plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py plugins/new-project/CHANGELOG.md --check
python3 plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py CHANGELOG.md --check
```
Expected: all green.

- [ ] **Step 2: Rotate plugin CHANGELOG `[Unreleased]` → `[0.1.0]` (already done in Task 4)**

Verify `plugins/new-project/CHANGELOG.md` already has `## [0.1.0] - 2026-05-14` section populated (it was created with this structure in Task 4). If `[Unreleased]` was edited during Phase 3-7, rotate any remaining entries down into `[0.1.0]` manually.

- [ ] **Step 3: Create annotated tag**

```bash
git tag -a plugin-v0.1.0 -m "Plugin v0.1.0 — initial release"
```

- [ ] **Step 4: Push commits and tag together**

```bash
git push && git push --tags
```

- [ ] **Step 5: Verify tag visible on GitHub**

Run: `gh release view plugin-v0.1.0 2>&1 || echo "Tag pushed, release page not yet created — that's fine"`

- [ ] **Step 6: (Optional) Create GitHub release**

```bash
gh release create plugin-v0.1.0 \
  --title "Plugin v0.1.0" \
  --notes-file plugins/new-project/CHANGELOG.md
```

---

## Self-Review

Run this checklist after the plan is written:

**1. Spec coverage:**
- §1 Background → Phase 0 (no task; context only) ✓
- §2 Architecture → Tasks 1–6 (manifests + docs in conventional layout) ✓
- §3 v0.1 Scope → Tasks 1–22 cover all 4 skills + distribution ✓
- §4 Universal SKILL.md Convention → Task 6 (SKILL_AUTHORING.md) + Task 16 (pinning test) ✓
- §5.1 new-project → Skill already exists; no new task except integration tests (Task 14) ✓
- §5.2 release-helper → Skill already exists; integration tested via smoke (Task 15) ✓
- §5.3 changelog-normalizer revised spec → Tasks 7–11 reconcile skill to revised rules ✓
- §5.4 audit-runner → Skill already exists; self-audit at Task 18 ✓
- §6 Scaffold ↔ Plugin Contract → Task 14 (contract test + CI) ✓
- §7 CI Gates → Tasks 14, 15, 16, 17 ✓
- §8 Versioning & Routing → Task 12 (ADR) + Task 13 (CONTRIBUTING) ✓
- §9 Release Path → Task 22 ✓
- §10 Migration Plan → Tasks 19–22 ✓
- §11 Open Implementation Notes → Addressed in earlier review pass (pipx fix etc.) ✓

**2. Placeholder scan:** No `TBD`, `TODO`, or vague descriptions. Every step has the actual content the engineer needs.

**3. Type consistency:** `Preferences`, `load_preferences`, `save_preferences`, `PREFERENCES_FILENAME` are used consistently across Task 11. CI workflow names (`plugin-contract`, `plugin-smoke`) referenced consistently.

---

## Execution Notes

- Tasks 7–11 (Phase 3) modify a file that was already committed. Each task is a small, isolated commit.
- Tasks 12–17 (Phases 4–5) can run in parallel between agents (no shared files).
- Task 18 (self-audit) MUST run AFTER Tasks 1–17 are merged to main, since it audits the integrated diff.
- Task 22 is the final gate. Do not push the tag until every preceding task is complete and CI is green.
