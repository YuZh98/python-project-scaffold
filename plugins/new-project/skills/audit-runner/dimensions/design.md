# Dimension: design

**Tier:** CORE (always evaluated)

## Purpose

Architecture, layer boundaries, single responsibility, file size, abstraction fit, and
**intent-revealing names** (judgment-tier). Design is the dim where the auditor's
taste matters most; severity calibration matters proportionally — design findings
rarely warrant `blocker`.

## Surface triggers

Not applicable — always evaluated.

## Checklist

1. **Layer boundaries.** Does the diff respect the project's declared dependency
   direction (e.g. service → repository → model, never the reverse)? Any new import
   that violates the rule? See GUIDELINES.md / DESIGN.md for the project's specific
   layer model.

2. **Single responsibility per file.** Does a file mix data access with business
   logic, or business logic with display? Has a previously single-purpose file gained
   a second purpose in this diff?

3. **File size.** A file growing past ~400 lines is a flag — not automatic, but worth
   asking "should this be split?" Past ~700 lines, the answer is almost always yes.

4. **Abstraction fit.** Is a new abstraction (class, ABC, protocol, decorator) earning
   its weight? Premature abstraction (one consumer, lots of indirection) is worse than
   duplication. Conversely, blatant duplication across two new modules should be
   refactored before merge.

5. **Single source of truth.** Are status values, thresholds, enum-like literals
   defined in the config layer, not hardcoded in business logic? Magic numbers in new
   code are a primary-dim → `conventions` finding (lint-tier), but the *architectural*
   variant — duplicating a config concept in business logic — is a design issue.

6. **Intent-revealing names.** Is a new function/class/variable name informative? Does
   it describe **what** it represents, not **how** it's implemented? `process_data`,
   `handle`, `helper`, `manager` are red flags unless the context genuinely is generic.

7. **Coupling.** New code reaches into private internals of another module (`_foo`).
   New code couples to an implementation detail that should be abstracted.

8. **Public API surface.** New public symbol that doesn't need to be public, or new
   private symbol that should be public (used across modules but with `_` prefix).

## Drift sweep

What in design's scope drifted from another source?

- DESIGN.md describes a module layout that the diff violates (primary-dim → here).
- ADR declares an architectural decision the diff contradicts (primary-dim → `docs`,
  but flag here if the contradiction is structural rather than narrative).
- Public/private naming convention drift between modules.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Violation of a hard architectural rule in GUIDELINES/DESIGN.md (e.g. circular import introduced). Rare. |
| major    | Mixed-responsibility file that will be hard to navigate; abstraction with no clear cost recovery; layer-boundary violation that future code will copy. |
| minor    | File-size growth approaching the soft threshold; naming that could be clearer; abstraction that's marginal but defensible. |
| nit      | A variable name that could be a touch more specific. |

## Common patterns

**Good.** New module has one clear purpose. New abstraction has at least two callers
or a clearly imminent second. New names read as nouns/verbs that describe domain
concepts, not infrastructure verbs.

**Bad.** A new file named `utils.py` or `helpers.py` with mixed contents. A new ABC
with one implementation. A new function whose name starts with `handle_`, `process_`,
or `do_` and whose body is non-trivial. Circular import "fixed" with a deferred
import inside a function body.
