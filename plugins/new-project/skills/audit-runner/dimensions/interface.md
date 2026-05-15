# Dimension: interface

**Tier:** CONTEXT-AWARE (evaluate if surface triggers fire; otherwise emit explicit
N/A, never silent skip)

## Purpose

Backwards-compatibility of public API. A public symbol is anything callers outside the
module can reach: not `_`-prefixed, exported in `__all__` or `__init__.py`, or
documented as a public API in README/docstrings.

Interface changes are particularly dangerous because they're often invisible at the
call site — code keeps compiling, but semantics shifted underneath.

## Surface triggers

`scripts/surface_detect.py` fires the `interface` dim when any of these are visible
on a single diff line (the patterns it can match without paired-line diff context):

- Public symbol removed (function, class, constant, module) — caught on `-` lines.
- Default kwarg value present on an added `def` (weakly flagged; sub-agent confirms by
  inspecting the paired removal).
- New exception subclass (`class FooError(...)` / `class FooException(...)`).

These triggers narrow the scanner's job to "could this diff plausibly touch the public
contract?". Once the sub-agent is spawned, it widens to the full checklist below —
including concerns the line scanner cannot reliably detect:

- Return type narrowed or widened (requires comparing the old and new signatures, which
  is diff-paired context outside the line scanner's scope).
- Exception type raised by an existing function changed.
- `__all__` membership shifted (added or removed).
- Module-level name removed from a package's `__init__.py`.
- Public dataclass field added.

If **no** trigger fires, the coordinator emits:
> `interface: N/A because no surface in diff (triggers considered: <list>)`

## Checklist

(Only reached when at least one trigger fired.)

1. **Removed public symbol.** If a public function/class/constant was removed, it must
   have had a deprecation period or be major-version-breaking. Otherwise blocker.

2. **Renamed public symbol.** Same rule. A rename without a deprecation shim
   (old name kept as alias) is a breaking change.

3. **Default kwarg change.** Changing `def f(x, mode="strict")` to `def f(x,
   mode="lenient")` is a semantic shift for every caller relying on the default.
   Document in CHANGELOG and consider whether the old default needs a deprecation
   period.

4. **Return type narrowed.** `-> Sequence[T]` becoming `-> list[T]` is fine; the
   reverse breaks callers who relied on list-specific methods. `-> Optional[T]`
   becoming `-> T` is fine; the reverse may break callers who assumed non-None.

5. **Return type widened.** A function that used to return `T` now returns
   `Optional[T]`. Callers must now handle `None`. Blocker unless callers verified.

6. **Exception type changed.** A function that used to raise `ValueError` now raises
   `MyDomainError`. Any caller's `except ValueError` no longer catches it. Either
   subclass appropriately or treat as a breaking change.

7. **New exception class on existing path.** A public function that used to raise
   only `ValueError` now also raises `RuntimeError`. Document and ensure callers are
   prepared.

8. **`__all__` drift.** `__all__` shrinks or grows. If it shrinks, the removed name
   was effectively unpublished (breaking). If it grows, the new name is now a
   commitment to maintain.

9. **CLI flag changes.** For CLI tools, flags are public API. Removing a flag,
   changing its default, or changing how it's named is a breaking change. Same rules.

10. **Public dataclass fields.** Adding a non-default-valued field to a public
    dataclass breaks instantiation by positional args. Adding with a default is
    safer.

## Drift sweep

What in interface's scope drifted from another source?

- Public function exists in code but not in `__all__`.
- Function documented as public in README but module name is `_internal`.
- Two `__init__.py` files in the same package re-export different things.
- CHANGELOG announces a deprecation but the symbol is already gone.

## Severity guide

| Severity | When |
|----------|------|
| blocker  | Public symbol removed without deprecation; return type narrowed in a breaking way; exception type changed and the old type was documented. |
| major    | Default kwarg changed without CHANGELOG entry; new exception raised on existing path without docs. |
| minor    | `__all__` drift that's likely intended but undocumented; type hint tightened in a way that's mostly benign. |
| nit      | Style of the deprecation message. |

## Common patterns

**Good.** Removed symbols have a one-release deprecation period via `warnings.warn(...
DeprecationWarning)` and a CHANGELOG entry under `Deprecated`. Renames keep the old
name as an alias for one release. Default-value changes are called out in CHANGELOG
and in the function's docstring.

**Bad.** A public function vanishes from `__init__.py` with no deprecation. A return
type silently narrows. A function used to raise `KeyError` and now raises a custom
`NotFoundError` with no inheritance from `KeyError` — every caller's `except KeyError`
breaks silently.
