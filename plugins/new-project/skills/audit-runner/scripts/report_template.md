<!--
audit-runner report template.

The coordinator fills this in verbatim. Section order is fixed. Sections marked OPTIONAL
may be omitted entirely if they would contain nothing concrete; do NOT emit placeholders
or "N/A" for them — silence is preferable to filler.

Sections marked REQUIRED must always appear, even if empty (use "(none)" as the body).
-->

## Verdict
{Approve | Approve with nits | Request changes}

## Executive summary
(2-3 sentences. State the verdict, the count of blockers and majors, and the single
most important thing the reader should fix first. No diff recap.)

## Findings table
<!-- REQUIRED. One row per finding. If no findings, write "(none)" below the header. -->
| ID  | Primary dim | Severity | File:Line | Finding | Suggested fix |
|-----|-------------|----------|-----------|---------|---------------|
| F1  | ...         | ...      | ...:...   | ...     | ...           |

## Cross-cutting observations
<!-- OPTIONAL. Multi-dim patterns; drift findings whose home is genuinely ambiguous;
     anything that does not fit one row. Bullet list, each entry 1-2 lines. Omit the
     section entirely if there are no cross-cutting observations. -->

## Per-dimension N/A justifications
<!-- Emit ONE bullet PER context-aware dim that was NOT evaluated. OMIT dims that were
     evaluated (their findings appear in the Findings table above). Omit the section
     entirely if every context-aware dim was evaluated. Format:
     - <dim>: N/A because <reason> (triggers considered: <pattern1>, <pattern2>, ...) -->
- <example>: N/A because no surface in diff (triggers considered: subprocess., eval, os.environ write)

## What I did NOT check and why
<!-- REQUIRED. Honest blind-spot disclosure. At minimum: tests not executed (audit is
     static); runtime behaviour not observed. Add any deferrals from time budget or
     scope flags. -->
- ...

## What's done well
<!-- OPTIONAL. ONE line only, citing a specific decision in the diff. Omit if there is
     nothing concrete to cite — performative praise is worse than silence. -->

## Open questions
<!-- OPTIONAL. Genuine questions to the implementer. Adaptive count; zero is acceptable
     if the diff is unambiguous. Omit the section if there are none. -->
- ...
