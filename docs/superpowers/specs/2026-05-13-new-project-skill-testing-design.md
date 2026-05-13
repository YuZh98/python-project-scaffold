# Test Plan: `new-project` Skill

**Date:** 2026-05-13
**Scope:** Manual testing of the `new-project` Claude Code skill (`tooling/claude-code/new-project.md`).
**Out of scope:** Scaffold engine (`init-project.py`, `substitute.py`) — covered by `tests/test_scaffold.py`.

---

## Background

Three bugs were found and fixed during the `lobster-imbalance` bootstrap session (v1.7.1):

1. **E501 docstring overflow** — `__init__.py` template used single-line `"""<<PROJECT_TITLE>>: <<DESCRIPTION>>"""`, overflowing ruff's 100-char limit for any realistic description. Fixed: multi-line docstring in template.
2. **SSH push failure** — `gh repo create --push` defaulted to SSH, failing for users without SSH keys. Fixed: decouple create from push; set HTTPS remote explicitly before `git push`.
3. **Skill recovery path missing** — when `init-project.py` exited non-zero, no recovery instructions were shown. Fixed: skill error handler now prints `cd $TARGET && git add -A && git commit -m "chore: scaffold $NAME"`.

A fourth issue (`rule-check-bash.sh` false positives on non-`.py` files and RST double-backtick docstrings) was fixed in the hook directly and is not skill-specific.

A `--dry-run` bug is being fixed in a parallel session. Scenarios T7–T8 are blocked on that fix.

---

## Approach

Ordered checklist. Run top-to-bottom. Mark each scenario **PASS / FAIL / SKIP** with one-line notes on actual behavior. Live tests create real GitHub repos — delete them after unless they have value.

---

## Scenarios

### Group 1 — Pre-flight failures

These require no dry-run; abort before any files are written.

**T1: Run from inside existing git repo**
- Setup: `cd` into any existing git repo (e.g., `python-project-scaffold/`)
- Invoke: `/new-project`
- Expected: abort with "Refusing to run inside an existing git repo. cd to a parent directory and re-invoke."
- Verify: no new directory created

**T2: `gh` not authenticated**
- Setup: `gh auth logout` (re-login after test)
- Invoke: `/new-project`
- Expected: abort with "Run 'gh auth login' first."
- Verify: no new directory created

---

### Group 2 — Input validation

**T3: Uppercase in project name**
- Input name: `My-Project`
- Expected: re-prompt with "Project name must be lowercase letters/digits/hyphens, start+end with a letter or digit. Got: 'My-Project'. Try: my-cool-tool"

**T4: Name starting with hyphen**
- Input name: `-bad-name`
- Expected: re-prompt with same validation message

**T5: Empty description**
- Input name: `test-desc-empty`, description: (press Enter with no text)
- Expected: either re-prompt or accept — document actual behavior
- Note: spec doesn't define validation for this field; result is informational

---

### Group 3 — Confirmation gate

**T6: Decline at Proceed? prompt**
- Proceed through 3 questions with valid inputs, then answer "n" at Proceed?
- Expected: clean abort message, no directory created under cwd, no GitHub repo created
- Verify: `ls` shows no new directory; `gh repo list` shows no new repo

---

### Group 4 — Live integration (different input setups)

These test Claude's behavior when using the skill — how it extracts project info from context.

**T7: No spec, no context**
- Invoke: `/new-project` with no prior context
- Expected: Claude asks all 3 questions interactively (name, description, visibility)
- Probe: does Claude make up values, or wait for user input on each?

**T8: Simple verbal description only**
- Provide: "I want to build a CLI tool that converts Markdown to HTML"
- Expected: Claude extracts a reasonable name (`markdown-to-html` or similar) and description, confirms via Step 3 summary before proceeding

**T9: Full spec file (baseline — already done)**
- Input: `lobster-imbalance` via `QUANT_PROJECT_SPEC.md`
- Result: PASS (this session). Claude pre-filled all 3 answers from spec, HTTPS push worked, branch protection enabled.

**T10: Mixed-stack spec (Python + Rust via PyO3)**
- Provide a spec that requires Rust extensions (e.g., "a Python package with a Rust core for hot-path computation via PyO3")
- Expected: Claude creates the Python layer using the scaffold, then explicitly notes that the Rust crate (`lobster_core/` or similar) must be added manually — scaffold is Python-only
- Probe: does Claude attempt to modify the scaffold structure, or correctly scope itself to the Python wrapper?

---

### Group 5 — Dry-run (blocked on parallel fix)

**T11: Long description, dry-run**
- Description: 85+ chars (e.g., "A tick-level limit-order-book replay and microstructure signal harness for NASDAQ ITCH data analysis")
- Invoke: `/new-project --dry-run`
- Expected: `[DRY-RUN] No files written, no GitHub repo created.`; generated `__init__.py` content shown with no lines > 100 chars
- Regression for Bug 1 (E501 fix)

**T12: Normal happy path, dry-run**
- Standard inputs, `--dry-run`
- Expected: summary table printed, `[DRY-RUN]` at end, no local directory created

---

## Success criteria

| Group | Pass condition |
|---|---|
| Pre-flight | Exact expected abort message; no artifacts left |
| Input validation | Re-prompt with correct message on bad input |
| Confirmation gate | Clean abort; `ls` and `gh repo list` confirm nothing created |
| Live integration | Claude fills values correctly from context; HTTPS push works; Rust case scoped correctly |
| Dry-run | `[DRY-RUN]` confirmed; no E501 in output |

---

## Cleanup

Live tests (T7–T10) create real GitHub repos. Delete after testing:

```bash
gh repo delete YuZh98/<name> --yes
rm -rf /Users/zhengyu/Desktop/Claude/Project/<name>
```

---

## Tracking

| Test | Status | Notes |
|---|---|---|
| T1 | — | |
| T2 | — | |
| T3 | — | |
| T4 | — | |
| T5 | — | |
| T6 | — | |
| T7 | — | |
| T8 | — | |
| T9 | PASS | lobster-imbalance, 2026-05-13 |
| T10 | — | |
| T11 | BLOCKED | pending --dry-run fix |
| T12 | BLOCKED | pending --dry-run fix |
