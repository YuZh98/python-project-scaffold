# Dimension: docs

**Tier:** CORE (always evaluated)

## Purpose

Documentation, comments, CHANGELOG, ADRs, README accuracy, deprecation notices, and
user-facing error message clarity. Also the home for most **drift findings** — when
two sources disagree, the fix usually lives in docs.

## Surface triggers

Not applicable — always evaluated.

## Checklist

1. **CHANGELOG `[Unreleased]` entry — content, not format.**
   Format checks (Keep-a-Changelog subheadings in order, refs on every entry,
   no process narrative) belong to `changelog-normalizer` and are reliably
   covered there; re-flagging them from this dim is what makes the audit
   feel inconsistent with the sibling skill. Limit this checklist item to
   what the auditor uniquely can verify against the diff:
   - Does the diff add an entry at all? (If the diff is behaviour-changing
     and there is no entry, that's a blocker regardless of format.)
   - Does the entry's verb match the diff's actual effect? "Added X" when the
     diff is a fix, "Removed Y" when Y was demoted/reworded — these
     drift-style mismatches the auditor catches because it has the diff;
     the normalizer does not.

   Mood, KaC structure, ref-trailer presence, and process-narrative leakage
   are explicitly **out of scope here**. If the report would have flagged
   one of those, route the finding to a note "run changelog-normalizer
   before re-audit" instead of opening a row in the findings table.

2. **ADR if architectural.** Hard-to-reverse architectural decisions are strong
   candidates for an ADR. Does the diff introduce one? Examples worth an ADR:
   - New external service dependency.
   - Schema migration with a non-trivial rollback path.
   - Choice of one library over another for a load-bearing concern.
   - New layer or boundary in the architecture.

3. **ADR status field.** If the diff touches an existing ADR, is its `Status` still
   `Accepted` / `Superseded` / `Deprecated` (no other values allowed)? A
   `Superseded` ADR references its successor by ID.

4. **Docstrings on public API.** Every public (non-`_`-prefixed) function has a
   docstring. Style follows the project's convention (Google / NumPy / reST per
   GUIDELINES.md).

5. **Comment quality.** Comments explain **WHY**, not **WHAT**. No comment rot
   (comment describes the code as it was, not as it is now). No `TODO` without a
   ticket reference.

6. **README accuracy.** If the diff changes a feature, public API, or installation
   step that README documents, does the README still match? Code examples in README
   that the diff invalidates are a `major`.

7. **Deprecation notices.** A removed-or-renamed public symbol should have a
   deprecation notice landed at least one release prior. If the diff removes a public
   symbol with no prior notice, flag it (primary-dim may move to `interface` if the
   *fix* is to restore the symbol with a deprecation shim).

8. **User-facing error clarity.** Exception messages and CLI error output are user
   docs. Do they say what went wrong and what the user can do? `"Error"` and
   `"Invalid"` are not messages.

9. **Type hints as documentation.** Public API has type hints (overlaps with
   `conventions`); flag here only when the hints contradict the docstring (drift).

## Drift sweep

This is **the** dim for drift. Sweep for cross-source disagreements:

- CHANGELOG entry says "Added X" but `pyproject.toml` version not bumped (or
  vice versa).
- Comment describes the code as it was, code as it is.
- ADR `Status: Accepted` but the diff implements its rejection.
- README example uses a function signature the diff just changed.
- Docstring `:returns:` claims one type, code returns another.
- Cross-reference anchor in one doc points at a heading that was renamed in another.
- One canonical cross-reference form per project — mixed anchor shapes in the same
  doc are a drift finding.

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

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Public API change with no CHANGELOG entry and no deprecation; user-facing error message that misrepresents the failure (could cause data loss decisions). |
| major    | README example invalidated by the diff; missing ADR for a clearly hard-to-reverse architectural decision. |
| minor    | Docstring style inconsistent with project convention; comment that says what the code says; TODO without ticket. |
| nit      | Minor wording in a comment or CHANGELOG entry. |

## Common patterns

**Good.** CHANGELOG entry lands with the diff, ends with `(#142)`. New public function
has a one-paragraph docstring explaining the WHY and a code example. README updated
in the same commit as the feature it documents.

**Bad.** Diff adds a feature, CHANGELOG untouched. Comment says "TODO: fix this"
with no ticket. Public function with a docstring that just repeats its name in prose.
User-facing exception message that says `"failed"`. ADR status field set to `Draft`
or `Proposed` (not one of the three allowed values).
