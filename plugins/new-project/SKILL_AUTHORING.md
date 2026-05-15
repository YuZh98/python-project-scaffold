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
