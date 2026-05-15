"""Pin the contract of refresh_dev_deps.py.

The script bumps lower bounds (`>=X.Y,<Z`) of dev-deps in a requirements file
to the current upstream minor at bootstrap time, so a fresh repo doesn't
inherit stale floors that Dependabot would immediately PR. Three contracts
this test pins:

1. A floor that is stale gets rewritten to current major.minor.
2. A floor that already matches current upstream is left unchanged.
3. A network-failure scenario (fetcher returns None) leaves the line untouched
   — bootstrap must not abort on a transient PyPI issue.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from refresh_dev_deps import refresh, rewrite_line  # type: ignore[import-not-found]  # noqa: E402


class TestRewriteLine(unittest.TestCase):
    """Unit-level: rewrite_line behaviour on individual lines."""

    def test_stale_floor_bumped_to_current_minor(self) -> None:
        new, changed = rewrite_line(
            "ruff>=0.6,<2\n",
            fetcher=lambda _pkg: "0.15.3",
        )
        self.assertTrue(changed)
        self.assertEqual(new, "ruff>=0.15,<2\n")

    def test_current_floor_left_alone(self) -> None:
        new, changed = rewrite_line(
            "ruff>=0.15,<2\n",
            fetcher=lambda _pkg: "0.15.3",
        )
        self.assertFalse(changed)
        self.assertEqual(new, "ruff>=0.15,<2\n")

    def test_pypi_failure_leaves_line_unchanged(self) -> None:
        original = "ruff>=0.6,<2\n"
        new, changed = rewrite_line(original, fetcher=lambda _pkg: None)
        self.assertFalse(changed)
        self.assertEqual(new, original)

    def test_unmatched_line_shape_left_alone(self) -> None:
        """Comments, blank lines, and unconstrained packages don't get rewritten."""
        for original in [
            "# Upper bounds prevent silent major-version breakage.\n",
            "\n",
            "ruff\n",
            "ruff==0.15.3\n",
            "ruff>=0.6\n",  # no ceiling
        ]:
            new, changed = rewrite_line(original, fetcher=lambda _pkg: "1.0.0")
            self.assertFalse(changed, f"expected no rewrite for: {original!r}")
            self.assertEqual(new, original)

    def test_three_part_floor_normalized_to_major_minor(self) -> None:
        """A floor like `>=8.0.0,<10` gets rewritten to major.minor only."""
        new, changed = rewrite_line(
            "pytest>=8.0.0,<10\n",
            fetcher=lambda _pkg: "9.2.1",
        )
        self.assertTrue(changed)
        self.assertEqual(new, "pytest>=9.2,<10\n")


class TestRefreshFile(unittest.TestCase):
    """Integration: end-to-end refresh on a temp requirements file."""

    def test_mixed_file_rewrites_only_pinned_floors(self, _versions={
        "ruff": "0.15.3", "pyright": "1.1.420", "pytest": "9.2.1",
    }) -> None:
        from tempfile import NamedTemporaryFile
        original = (
            "# Upper bounds prevent silent major-version breakage.\n"
            "ruff>=0.6,<2\n"
            "pyright>=1.1,<2\n"
            "pytest>=8.0,<10\n"
            "\n"
            "# pre-commit pinned by hand — unmatched by the regex.\n"
            "pre-commit==4.0.1\n"
        )
        f = NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        try:
            f.write(original)
            f.close()
            rc = refresh(Path(f.name), fetcher=lambda pkg: _versions.get(pkg))
            self.assertEqual(rc, 0)
            result = Path(f.name).read_text()
            self.assertIn("ruff>=0.15,<2\n", result)
            self.assertIn("pyright>=1.1,<2\n", result)  # unchanged
            self.assertIn("pytest>=9.2,<10\n", result)
            self.assertIn("# Upper bounds prevent silent major-version breakage.\n", result)
            self.assertIn("pre-commit==4.0.1\n", result)
        finally:
            Path(f.name).unlink(missing_ok=True)

    def test_missing_file_returns_error_code(self) -> None:
        rc = refresh(Path("/nonexistent/path/requirements-dev.txt"))
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
