"""Example module — DELETE this file AND ``tests/test_example.py`` together.

This is a paired hello-world demonstrating idiomatic patterns the scaffold's
pinning tests enforce:

- Type hints on every public function parameter and return value.
- Docstrings on every public function and class.
- ``@dataclass`` for value containers — PascalCase class name; type-annotated
  fields (the pinning tests inspect both top-level functions and class methods).
- No mutable default arguments. No ``print()`` debug — return values or raise
  exceptions instead.

Delete this file together with ``tests/test_example.py`` when you write your
first real module. Keeping one without the other leaves the test suite red.
"""

from __future__ import annotations

from dataclasses import dataclass


def greet(name: str, greeting: str = "Hello") -> str:
    """Return a greeting message for the given name.

    Args:
        name: The recipient's name.
        greeting: Optional greeting word. Defaults to ``"Hello"``.

    Returns:
        A formatted greeting string like ``"Hello, World!"``.
    """
    return f"{greeting}, {name}!"


@dataclass
class Greeter:
    """Stateful greeter that remembers a greeting word.

    Attributes:
        greeting: The greeting word used for every call to ``say()``.
    """

    greeting: str = "Hello"

    def say(self, name: str) -> str:
        """Return a greeting for ``name`` using this Greeter's word."""
        return f"{self.greeting}, {name}!"
