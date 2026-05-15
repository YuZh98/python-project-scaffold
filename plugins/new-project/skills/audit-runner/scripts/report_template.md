<!--
audit-runner report template.

Two modes, selected by finding count:

- COMPACT mode (default for diffs with ≤2 findings AND no blockers).
  Emit ONLY: Verdict + Executive summary + Findings table.
  All other sections omitted. A small audit with one nit does not need
  cross-cutting observations, N/A justifications, blind-spot disclosure,
  praise, or open questions — those are scaffolding for substantive
  reports, not for sanity checks.

- FULL mode (≥3 findings OR any blocker).
  Emit every REQUIRED section below. Sections marked OPTIONAL may still
  be omitted in this mode if they would contain nothing concrete.

The coordinator picks the mode AFTER all findings are collected — never
before. Picking the mode upfront defeats the purpose; you might find more
findings than expected during the walk.

Sections marked REQUIRED must always appear in FULL mode; use "(none)"
as the body if they would otherwise be empty. Sections marked OPTIONAL
may be omitted entirely in either mode if they would contain only filler.
-->

## Verdict
{Approve | Approve with nits | Request changes}

## Executive summary
<!-- REQUIRED in both modes. 1-2 sentences in COMPACT mode; 2-3 sentences in
     FULL mode. State the verdict, the count of blockers and majors, and the
     single most important thing the reader should fix first. No diff recap.
     In COMPACT mode, also list any context-aware dims with no surface in one
     short line at the end (e.g. "N/A dims: security, performance,
     observability, interface, dependency.") so the omission isn't silent. -->

## Findings table
<!-- REQUIRED in both modes. One row per finding. If no findings, write
     "(none)" below the header. -->
| ID  | Primary dim | Severity | File:Line | Finding | Suggested fix |
|-----|-------------|----------|-----------|---------|---------------|
| F1  | ...         | ...      | ...:...   | ...     | ...           |

<!-- ====== COMPACT MODE ENDS HERE ====== -->
<!-- The remaining sections appear ONLY in FULL mode. -->

## Cross-cutting observations
<!-- OPTIONAL. Multi-dim patterns; drift findings whose home is genuinely ambiguous;
     anything that does not fit one row. Bullet list, each entry 1-2 lines. Omit the
     section entirely if there are no cross-cutting observations. -->

## Per-dimension N/A justifications
<!-- FULL mode only. Emit ONE bullet PER context-aware dim that was NOT evaluated.
     Omit dims that were evaluated (their findings appear in the Findings table above).
     Omit the section entirely if every context-aware dim was evaluated.
     Format:
     - <dim>: N/A because <reason> (triggers considered: <pattern1>, <pattern2>, ...) -->
- <example>: N/A because no surface in diff (triggers considered: subprocess., eval, os.environ write)

## What I did NOT check and why
<!-- REQUIRED in FULL mode; OMITTED entirely in COMPACT mode. Honest blind-spot
     disclosure. At minimum: tests not executed (audit is static); runtime behaviour
     not observed. Add any deferrals from time budget or scope flags. -->
- ...

## What's done well
<!-- OPTIONAL. ONE line only, citing a specific decision in the diff. Omit if there is
     nothing concrete to cite — performative praise is worse than silence. -->

## Open questions
<!-- OPTIONAL. Genuine questions to the implementer. Adaptive count; zero is acceptable
     if the diff is unambiguous. Omit the section if there are none. -->
- ...
