"""Example tests — DELETE this file together with ``src/<<PACKAGE_NAME>>/example.py``.

Demonstrates idiomatic pytest patterns:

- Class-level grouping per public symbol under test.
- One ``test_<behaviour>`` method per branch / edge case.
- Plain ``assert`` (no ``unittest`` boilerplate).

100% branch coverage of ``example.py`` so the project's 95% coverage gate stays
green after scaffolding.
"""

from <<PACKAGE_NAME>>.example import Greeter, greet


class TestGreet:
    def test_default_greeting(self) -> None:
        assert greet("World") == "Hello, World!"

    def test_custom_greeting(self) -> None:
        assert greet("World", greeting="Hi") == "Hi, World!"


class TestGreeter:
    def test_default_greeting_word(self) -> None:
        g = Greeter()
        assert g.say("World") == "Hello, World!"

    def test_custom_greeting_word(self) -> None:
        g = Greeter(greeting="Hi")
        assert g.say("World") == "Hi, World!"
