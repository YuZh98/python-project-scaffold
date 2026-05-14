# Test Plan: `new-project` Skill

**Date:** 2026-05-13 (updated through v1.7.6)
**Scope:** Manual and automated testing of the `new-project` Claude Code skill (`tooling/claude-code/new-project.md`).
**Out of scope:** Scaffold engine (`init-project.py`, `substitute.py`) — covered by `tests/test_scaffold.py`.

---

## Background

### v1.7.1 — Three bugs fixed during `lobster-imbalance` bootstrap

1. **E501 docstring overflow** — `__init__.py` template used single-line `"""<<PROJECT_TITLE>>: <<DESCRIPTION>>"""`, overflowing ruff's 100-char limit for any realistic description. Fixed: multi-line docstring in template.
2. **SSH push failure** — `gh repo create --push` defaulted to SSH, failing for users without SSH keys. Fixed: decouple create from push; set HTTPS remote explicitly before `git push`.
3. **Skill recovery path missing** — when `init-project.py` exited non-zero, no recovery instructions were shown. Fixed: skill error handler now prints recovery commands.

### v1.7.2 — Dry-run fix

`init-project.py` `--target` mode ignored `--dry-run` and wrote files unconditionally. Fixed: early-return guard at top of `_mode_target` prints values and exits without touching disk or git.

### v1.7.3–v1.7.4 — Description optimization + 4 questions + private default

- Skill description optimized for better triggering.
- **4th question added: License** (MIT default; Apache-2.0, BSD-3-Clause, Unlicense also valid).
- **Visibility default changed** from public → private.
- Non-MIT licenses: `scripts/write_license.py` rewrites `$TARGET/LICENSE` + `git commit --amend --no-edit`.

### v1.7.5–v1.7.6 — Condensation + CI auto-publish

- Skill condensed 53% by extracting license texts to bundled `scripts/write_license.py`.
- CI workflow (`release-skill.yml`) now auto-builds and uploads `new-project.skill` to every GitHub Release on tag push.

---

## Approach

Ordered checklist. Run top-to-bottom. Mark each scenario **PASS / FAIL / SKIP** with one-line notes.

**Automated** — can be run via bash or direct Python invocation without a live Claude Code session.
**User-only** — requires an interactive Claude Code session; cannot be delegated to a subagent.

Live tests (T7–T10, T14) create real GitHub repos — delete after:
```bash
gh repo delete YuZh98/<name> --yes
rm -rf /Users/zhengyu/Desktop/Claude/Project/<name>
```

---

## Scenarios

### Group 1 — Pre-flight failures (Automated)

**T1: Run from inside existing git repo**
- Setup: `cd python-project-scaffold/`
- Automated check:
  ```bash
  git rev-parse --is-inside-work-tree 2>/dev/null && echo "INSIDE_GIT=yes"
  ```
- Full skill test (user-only): invoke `/new-project` from inside the repo; expected abort: "Refusing to run inside an existing git repo. cd to a parent directory and re-invoke."
- Verify: no new directory created under cwd

**T2: `gh` not authenticated (User-only)**
- Setup: `gh auth logout` (re-login after)
- Expected: abort with "Run 'gh auth login' first."
- Verify: no new directory created

---

### Group 2 — Input validation (User-only)

These require interactive Claude Code to present the re-prompt.

**T3: Uppercase in project name**
- Input name: `My-Project`
- Expected: re-prompt "Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit. Got: 'My-Project'. Try: my-cool-tool"

**T4: Name starting with hyphen**
- Input name: `-bad-name`
- Expected: re-prompt with same validation message

**T5: Empty description**
- Input name: `test-desc-empty`, description: (press Enter with no text)
- Expected: either re-prompt or accept — document actual behavior
- Note: spec doesn't define validation for empty description; result is informational

---

### Group 3 — Confirmation gate (User-only)

**T6: Decline at Proceed? prompt**
- Proceed through all 4 questions with valid inputs, then answer "n" at Proceed?
- Expected: clean abort, no directory created under cwd, no GitHub repo created
- Verify: `ls` shows no new directory; `gh repo list` shows no new repo

---

### Group 4 — Live integration (User-only)

**T7: No spec, no context**
- Invoke: `/new-project` with no prior context
- Expected: Claude asks all 4 questions interactively (name, description, visibility, license)
- Probe: does Claude make up values, or wait for user input on each?

**T8: Simple verbal description only**
- Provide: "I want to build a CLI tool that converts Markdown to HTML"
- Expected: Claude extracts a reasonable name (`markdown-to-html` or similar) and description, confirms via Step 3 summary before proceeding

**T9: Full spec file (baseline — already done)**
- Input: `lobster-imbalance` via `QUANT_PROJECT_SPEC.md`
- Result: PASS (2026-05-13). Claude pre-filled all answers from spec, HTTPS push worked, branch protection enabled.

**T10: Mixed-stack spec (Python + Rust via PyO3)**
- Provide a spec that requires Rust extensions (e.g., "a Python package with a Rust core for hot-path computation via PyO3")
- Expected: Claude creates the Python layer using the scaffold, then explicitly notes that the Rust crate must be added manually — scaffold is Python-only
- Probe: does Claude attempt to modify the scaffold structure, or correctly scope itself to the Python wrapper?

---

### Group 5 — Dry-run (Automated — dry-run fix shipped in v1.7.2)

Both can be tested via direct `init-project.py` invocation without a full skill session.

**T11: Long description, dry-run**
```bash
cd /Users/zhengyu/Desktop/Claude/Project/python-project-scaffold
VALUES=$(python3 - <<'PY'
import json
print(json.dumps({
  "<<PROJECT_NAME>>": "tick-data-harness",
  "<<PROJECT_TITLE>>": "Tick Data Harness",
  "<<PACKAGE_NAME>>": "tick_data_harness",
  "<<DESCRIPTION>>": "A tick-level limit-order-book replay and microstructure signal harness for NASDAQ ITCH data analysis",
  "<<AUTHOR_NAME>>": "Test User",
  "<<AUTHOR_EMAIL>>": "test@example.com",
  "<<YEAR>>": "2026",
  "<<LICENSE_ID>>": "MIT",
  "<<PYTHON_FLOOR>>": "3.11",
  "<<GITHUB_USERNAME>>": "YuZh98"
}))
PY
)
TMPVAL=$(mktemp)
echo "$VALUES" > "$TMPVAL"
python3 scripts/init-project.py --target /tmp/dry-run-test --values "$TMPVAL" --dry-run
rm -f "$TMPVAL"
```
- Expected: prints `[DRY-RUN] --target mode: would bootstrap project at /tmp/dry-run-test`, lists values, `No files written`
- Verify: `/tmp/dry-run-test` does NOT exist after the run
- Regression for Bug 1 (E501 fix) — description is 100 chars; verify `__init__.py` output shows multi-line docstring

**T12: Normal happy path, dry-run**
- Same as T11 but with a short description (e.g., "CLI tool for managing X.")
- Expected: `[DRY-RUN]` confirmed; no local directory created

---

### Group 6 — License and visibility (v1.7.4+)

**T13: Invalid license input → re-prompt (User-only)**
- At license question, enter: `GPL-3.0`
- Expected: re-prompt "License must be one of: MIT, Apache-2.0, BSD-3-Clause, Unlicense. Got: 'GPL-3.0'."
- Follow-up: enter `Apache-2.0` → accepted, proceeds normally

**T14: Non-MIT license file rewrite (User-only)**
- Complete live flow with `LICENSE_ID=Apache-2.0`
- Expected:
  - `$TARGET/LICENSE` contains "Apache License" text (not MIT)
  - `git log --oneline` in target shows only one commit (scaffold commit; amend replaced it)
  - `git show HEAD:LICENSE` shows Apache text
- Cleanup: delete the created repo after

**T15: Visibility default → private (Automated — verify skill text; User-only for live test)**
- Skill text check:
  ```bash
  grep -n "private" tooling/claude-code/new-project.md | head -5
  ```
  Expected: Step 2 shows `private` as the default for visibility question
- Live test (user-only): at visibility question, press Enter without typing → confirm summary shows `private`, resulting repo is private

---

### Group 7 — Skill install (Automated)

**T16: `.skill` install via `gh release download`**
```bash
gh release download --latest -R YuZh98/python-project-scaffold \
  --pattern "new-project.skill" -D /tmp
ls -lh /tmp/new-project.skill
unzip -l /tmp/new-project.skill
```
- Expected: download succeeds; zip contains `new-project/SKILL.md` and `new-project/scripts/write_license.py`
- Install check:
  ```bash
  unzip -o /tmp/new-project.skill -d /tmp/skill-install-test
  ls /tmp/skill-install-test/new-project/
  diff /tmp/skill-install-test/new-project/SKILL.md ~/.claude/skills/new-project/SKILL.md
  ```
  Expected: diff is clean (installed skill matches live skill)
- Cleanup: `rm -rf /tmp/skill-install-test /tmp/new-project.skill`

---

## Success criteria

| Group | Pass condition |
|---|---|
| Pre-flight | Exact expected abort message; no artifacts left |
| Input validation | Re-prompt with correct message on bad input |
| Confirmation gate | Clean abort; `ls` and `gh repo list` confirm nothing created |
| Live integration | Claude fills values correctly from context; HTTPS push works; Rust case scoped correctly |
| Dry-run | `[DRY-RUN]` confirmed; no files written; no E501 in `__init__.py` docstring |
| License + visibility | Invalid license re-prompts; non-MIT LICENSE content correct after amend; blank visibility defaults to private |
| Skill install | `.skill` zip present on latest release; contents match live skill |

---

## Tracking

| Test | Mode | Status | Notes |
|---|---|---|---|
| T1 | Automated (partial) / User-only (full) | PASS (auto) | git check fires; full skill test pending |
| T2 | User-only | — | |
| T3 | User-only | PASS | 2026-05-13; re-prompt fired correctly |
| T4 | User-only | — | |
| T5 | User-only | — | |
| T6 | User-only | — | |
| T7 | User-only | PASS | 2026-05-13; Claude asked all 4 questions interactively |
| T8 | User-only | — | |
| T9 | User-only | PASS | lobster-imbalance, 2026-05-13 |
| T10 | User-only | — | |
| T11 | Automated | PASS | 2026-05-13; `[DRY-RUN]` printed, target not created |
| T12 | Automated | PASS | 2026-05-13; `[DRY-RUN]` printed, target not created |
| T13 | User-only | — | v1.7.4+ |
| T14 | User-only | — | v1.7.4+ |
| T15 | Automated (text) / User-only (live) | PASS (text) | default `private` confirmed in skill; live test pending |
| T16 | Automated | PASS | 2026-05-13; zip contains both files; diff vs live clean |
