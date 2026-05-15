# Dimension: ci

**Tier:** CORE (always evaluated)

## Purpose

CI configuration, pre-commit hooks, and — critically — the global rules §7 enforcement
gate: **no rule lands without its enforcement**. A new rule codified in GUIDELINES.md
or CLAUDE.md must ship with a passing pinning test OR an explicit `xfail(strict=False)`
with a reason linking the follow-up PR.

This is the dim most often glossed over and the dim most often responsible for policy
fiction.

## Surface triggers

Not applicable — always evaluated.

## Checklist

1. **GitHub Actions YAML validity.** Any `.github/workflows/*.yml` change parses as
   YAML? Indentation correct? Required keys present (`name`, `on`, `jobs`)?

2. **Pre-commit hook updated if a new rule lands.** If the diff adds a rule to
   GUIDELINES.md, is there a corresponding hook in `.pre-commit-config.yaml`? If the
   rule is mechanical (formatter, linter), a hook is mandatory. If judgment-tier, a
   hook may be impossible — note that and require the pinning test instead.

3. **§7 enforcement gate (the big one).** For any PR that adds or strengthens a rule
   in GUIDELINES.md, CLAUDE.md, DESIGN.md, or `pyproject.toml`'s tool configs:
   - **Either** a passing pinning test in the same PR that fails if the rule is
     violated,
   - **OR** an explicit `pytest.mark.xfail(strict=False)` with a `reason` that links
     the follow-up PR which will close the gap.
   - **Neither → blocker.** This is the policy-fiction failure mode.

4. **Coverage gate covers new code.** If the project has a coverage threshold, does
   the new code count toward it? Look for `# pragma: no cover` on new code without
   justification.

5. **CI matrix covers `requires-python` versions.** If `pyproject.toml`'s
   `requires-python = ">=3.11"`, the matrix must include 3.11, 3.12, 3.13 (whatever
   versions exist in the range). Adding a version to one without the other is a drift
   finding.

6. **Deprecation-strict gate (per global rules §7).** Before any major dependency
   bump, the project must run `pytest -W error::DeprecationWarning`. If the diff
   bumps a major version, has this gate been exercised?

7. **No skipped hooks.** Look for `git commit --no-verify` evidence (unusual commit
   messages, missing formatter-introduced changes) and for `# noqa` / `# type: ignore`
   without justification.

## Drift sweep

What in CI's scope drifted from another source?

- `pyproject.toml` declares `python = ">=3.11"` but CI matrix only lists 3.12.
- `.pre-commit-config.yaml` references a tool version older than `pyproject.toml`'s
  dev-dependency pin.
- A new GUIDELINES rule has no corresponding hook AND no pinning test (the §7 trip).
- Two CI workflows running the same job differently (e.g. lint job and ci job both
  invoking ruff with different rule sets).

## Severity guide

| Severity | When |
|----------|------|
| blocker  | New rule codified with neither pinning test nor `xfail(strict=False)` with reason — policy fiction. CI matrix missing a `requires-python`-listed version. GHA YAML that won't parse. |
| major    | Pre-commit hook missing for a mechanical new rule. Coverage threshold drift. Deprecation-strict gate not run before a major bump. |
| minor    | One redundant CI step; matrix version ordering inconsistency. |
| nit      | YAML key order quibble. |

## Common patterns

**Good.** Every new rule has a paired pinning test in the same PR (or an explicit
xfail bridge with a linked follow-up). Pre-commit hooks updated atomically with
GUIDELINES changes. CI matrix derived from a single source (e.g. a generated job
matrix from `pyproject.toml`).

**Bad.** A new rule in GUIDELINES.md with no test and no xfail — the most insidious
form of drift, because it looks like progress. CI passing with a rule that's actually
unenforced. `# pragma: no cover` on a new function. A major dependency bump with no
deprecation-strict pytest run noted in the PR.
