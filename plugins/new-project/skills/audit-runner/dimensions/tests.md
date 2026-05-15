# Dimension: tests

**Tier:** CORE (always evaluated)

## Purpose

Tests are two sub-questions, and the auditor **must answer both**:

1. **Discipline** — was TDD followed? Does new behaviour have a failing-then-passing
   test? Is the project's coverage gate met for new code?
2. **Code quality of the tests themselves** — mock abuse, brittleness to refactor,
   isolation, intent-revealing names, gaps on critical paths.

A common failure mode is reporting on (2) and forgetting (1), or vice versa. The
report's findings table should make clear which sub-question each finding addresses.

## Surface triggers

Not applicable — always evaluated. Tests are CORE even when the diff is test-only
(audit-runner is the structural gate; test-only PRs still go through it).

## Checklist

### Discipline

1. **New behaviour → new test.** Every new public function or new branch in existing
   code should have an accompanying test. If not, flag it.

2. **TDD cadence visible in commits.** Recommended default for multi-sub-task feature
   work: `test:` (red) → `feat:` (green) → `chore:` (rollup). Note deviations as a
   minor unless the project pins the cadence as a hard rule. Single-commit refactors
   with no behaviour change are exempt.

3. **Coverage gate met for new code.** The audit is static — you can't run coverage —
   but you can spot obvious gaps: a new `try/except` branch with no test that exercises
   the exception, a new function with no callers in any test file, a new public method
   on an existing class where the class's test file is untouched.

4. **Failing-then-passing pattern.** Was each new behaviour proved to fail without the
   implementation? You can't check the test runs, but you can check: is the test
   meaningful? Does it actually exercise the new code path, or does it pass trivially?

### Code quality of tests

5. **Mock abuse.** A test that mocks everything it touches asserts nothing real. Flag:
   - Mocking the unit under test.
   - Patching internals of the unit under test instead of its dependencies.
   - Asserting `mock.assert_called_with(...)` as the *only* assertion.

6. **Brittleness.** Test names and bodies are coupled to implementation, not behaviour
   (e.g. asserting internal method call counts that would change on harmless refactor).

7. **Isolation.** Tests share state through module-level fixtures without clear teardown.
   Tests depend on execution order.

8. **Intent-revealing names.** `test_foo_1`, `test_it_works`, `test_returns_correct`
   are red flags. Good names describe the scenario and the expected outcome:
   `test_rollback_raises_on_empty_tag`.

9. **Critical-path gap.** A new code path that is *not* trivial to test (filesystem
   side-effect, network call) — was it tested at all, or did the author skip it as
   "too hard"? Flag the gap, suggest a stub/fake.

10. **Test code follows the same rules as production code.** Type hints on shared
    fixtures; no `print()`; no magic numbers without names. Tests are read more often
    than they are written.

## Drift sweep

What in tests's scope drifted from another source?

- Test docstring/name describes one invariant; assertion checks a different one.
- A test was renamed but the corresponding feature wasn't (or vice versa).
- Coverage config in `pyproject.toml` excludes the new module — flag this, it's
  almost always a mistake.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | New public behaviour with no test at all; critical-path branch (error handler, security check) with no test. Coverage gate explicitly bypassed (`# pragma: no cover` on new code) without justification. |
| major    | Mock-only "test" that asserts nothing about behaviour; brittle test coupled to internals; obvious branch gap on a non-critical path. |
| minor    | Test name unclear; missing isolation; small magic number in test body. |
| nit      | Single uninformative test name; one mock that could be a fake. |

## Common patterns

**Good.** Each new function has one test for the happy path and one per error branch.
Test names read as sentences. Fixtures are explicit, narrowly scoped, and named for the
scenario they construct.

**Bad.** A test file added with `def test_*()` containing only `assert True`. Mock
patches of the unit under test itself. Tests that pass without the implementation
under test (verify by mentally deleting the implementation — would the test still
pass?). Coverage `pragma: no cover` on a new error branch.
