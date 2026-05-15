# Dimension: correctness

**Tier:** CORE (always evaluated)

## Purpose

Catch logic bugs, edge cases, and — most importantly — **silent breakage**: changes
that compile and pass tests but quietly alter behaviour in ways the test suite was never
designed to catch. Correctness is the dim with the highest blocker rate; spend the time
budget here.

## Surface triggers

Not applicable — this dim is always evaluated regardless of trigger detection.

## Checklist

Walk each item against the diff. Note findings with file:line and severity.

1. **Logic bugs.** Off-by-one in loops, range bounds, slice indices. Wrong operator
   (`<` vs `<=`, `and` vs `or`). Conditions that always evaluate one way.

2. **Null / Optional handling.** New code dereferences a value that prior code treated
   as `Optional[T]`. New code accepts a `None` it cannot handle. Removed `is None`
   check.

3. **Error paths.** Every `raise` in new code: who catches it? Is the exception type
   appropriate? Does the caller's exception handler understand the new type?

4. **Edge cases.** Empty input, single-element input, very large input, unicode
   surprises (length-in-bytes vs length-in-chars), timezone-aware vs naive datetimes,
   floating-point comparison.

5. **Race conditions.** New shared state without locking. Time-of-check-vs-time-of-use
   on filesystem paths. Async tasks reading mutable state.

6. **Silent-breakage sweep.** **Mandatory.** For every change:
   - **Removed guard.** Was an `if/raise` / `assert` / type-narrow removed without
     a paired explicit decision? (Most common silent-breakage shape.)
   - **Changed default.** Did a kwarg default change value? Did a class attribute
     default change? Existing callers may rely on the old default.
   - **Narrowed precondition.** Does the function now require something it previously
     tolerated? (e.g. now rejects empty strings where it used to allow them.)
   - **Widened postcondition.** Does the function now return values it previously
     didn't? (e.g. returns `None` where it used to always return a `T`.)

7. **State transitions.** New code mutates state in an order the existing model
   doesn't expect. Partial mutation on error path leaves state inconsistent.

## Drift sweep

What in correctness's scope drifted from another source?

- Docstring says one thing, code does another (primary-dim → `docs`, but flag here
  if the discrepancy hides a logic bug).
- Type annotation contradicts runtime behaviour (e.g. `-> str` but returns `None` on
  one branch).
- Test name implies one invariant, test body asserts a different one (primary-dim →
  `tests`).

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Silent breakage with downstream callers; data corruption; security-adjacent logic flaw; missing error handling on a path that will hit production. |
| major    | Edge case that will fire under realistic input; race that's hard to reproduce but real; widened postcondition without a test. |
| minor    | Defensive-coding gap on a path unlikely to fire; off-by-one in a comment or log message. |
| nit      | Naming that *might* obscure intent under unusual input. |

## Common patterns

**Good.** New guards are paired with tests. Removed guards are accompanied by an
explicit comment ("guard now enforced upstream by X") and a test that pins the new
boundary. Default changes have an entry in CHANGELOG and a passing test for the new
default.

**Bad.** Removed guards with no comment. New `if/else` where the `else` branch has no
test. Refactor that silently changes return type from `T` to `Optional[T]`. Wrapping
a call in `try/except Exception: pass` without a logged message.
