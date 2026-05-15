# Dimension: dependency

**Tier:** CONTEXT-AWARE (evaluate if surface triggers fire; otherwise emit explicit
N/A, never silent skip)

## Purpose

Hygiene of project dependencies: licensing, pinning, supply-chain concerns, duplicates,
install bloat, transitive risk. Most projects accumulate deps faster than they
audit them; this dim is the gate that keeps the cost visible.

## Surface triggers

Spawn this sub-agent **only if** the diff contains:

- A new line in `pyproject.toml` `dependencies` / `dev-dependencies` /
  `optional-dependencies`.
- A version bump in any of the above.
- A change in `requirements*.txt`, `uv.lock`, `poetry.lock`, `setup.cfg`,
  `setup.py`.

If **none** fire, the coordinator emits:
> `dependency: N/A because no surface in diff (triggers considered: <list>)`

## Checklist

(Only reached when at least one trigger fired.)

1. **License compatibility.** The new dep's license must be compatible with the
   project's license. Quick reference:
   - `MIT` / `BSD-*` / `Apache-2.0` / `ISC` / `Python-2.0` — compatible with most
     projects.
   - `LGPL-*` — usually compatible if dynamically linked; check.
   - `GPL-*` / `AGPL-*` — generally incompatible with permissive-licensed projects.
   - Unknown / no license — blocker until clarified.

2. **Pinning.** Per project policy (often documented in CONTRIBUTING.md), production
   deps may be pinned (`==`) or constrained (`>=,<`). New deps must follow the policy.

3. **Supply-chain risk.**
   - New dep with very few downloads / low maintenance signal — flag.
   - Dep with no recent releases and no patches for known CVEs — flag.
   - Maintainer concentration (single maintainer, abandoned-looking org) — flag.
   - Typosquat names (`requets` vs `requests`, `python-dateutil` vs
     `python-dateutils`) — blocker.

4. **Duplicate functionality.** Project already has `requests`; diff adds `httpx`.
   Sometimes intentional (async vs sync); often accidental. Force the rationale.

5. **Install bloat.** Heavy transitive trees for marginal gain (e.g. adding `pandas`
   for one DataFrame slice). Ask whether a lighter alternative exists.

6. **Native code / C extension.** New dep with native code complicates cross-platform
   builds. Note it, especially if the project's CI matrix is cross-platform.

7. **Vulnerability hits.** If the new version is known-vulnerable (advisor / CVE),
   blocker. (Audit-runner is static; flag the concern and recommend running
   `pip-audit` / `safety` / `uv audit`.)

8. **Version bump implications.**
   - **Patch** (`1.2.3 → 1.2.4`) — usually safe; spot-check the changelog.
   - **Minor** (`1.2.3 → 1.3.0`) — read upstream changelog for deprecations.
   - **Major** (`1.2.3 → 2.0.0`) — read upstream changelog, run
     `pytest -W error::DeprecationWarning` (global rules §7).

9. **Lock file consistency.** If the project uses a lock file (`uv.lock`,
   `poetry.lock`), the change to `pyproject.toml` and the change to the lock file must
   land together. Missing lock-file delta is a drift finding.

## Drift sweep

What in dependency's scope drifted from another source?

- `pyproject.toml` lists a dep that the lock file doesn't pin.
- Two dep files (`pyproject.toml` and `requirements-dev.txt`) pin different versions
  of the same package.
- A dep is listed but never imported anywhere in source — dead dependency.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Known CVE in the added version; license incompatibility; typosquat; deps file and lock file out of sync in a way that won't build. |
| major    | Heavy transitive tree for marginal use; duplicate-functionality dep without rationale; new dep on a clearly abandoned project. |
| minor    | Patch bump without spot-checking changelog; bump on a transitive that's only used by one dep. |
| nit      | Cosmetic constraint style (`>=1.2,<2` vs `^1.2`) inconsistent with the rest of the file. |

## Common patterns

**Good.** Added deps land with: a rationale (PR description or CHANGELOG), a license
check, an updated lock file, and (for any major bump) a deprecation-strict pytest
run. The new import is visible in source.

**Bad.** A dep added to `pyproject.toml` with no lock-file delta and no import in
the diff. A version bump that skips a deprecation cycle. A new dep duplicating
existing functionality with no comment explaining why. A dep with no license metadata.
