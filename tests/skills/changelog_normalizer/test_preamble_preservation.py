"""Pin parser+renderer preservation of version preamble content.

Background: a CHANGELOG that ships with an HTML comment block under
`## [Unreleased]` (Keep-a-Changelog scaffolding) or a one-sentence summary
paragraph under a versioned section is the common case for projects that
follow the spec's recommendations. Previously the parser had no rule for
"preamble between version header and first `### Subsection`", so the
default-mode rewrite silently stripped both. Users lost intentional content
on every normalization run; the only recovery was the `.bak` file.

These tests pin that the parser now captures preamble lines and the renderer
emits them verbatim, so the round-trip is content-preserving.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[3]
        / "plugins/new-project/skills/changelog-normalizer/scripts"),
)
from normalize_changelog import normalize, parse, render  # type: ignore[import-not-found]  # noqa: E402


class TestPreamblePreservation(unittest.TestCase):
    """Summary paragraphs and HTML comment blocks survive parse → render."""

    def test_summary_paragraph_under_versioned_section_preserved(self) -> None:
        text = (
            "# Changelog\n"
            "\n"
            "## [Unreleased]\n"
            "\n"
            "## [1.2.0] - 2026-01-15\n"
            "\n"
            "Fixes a regression in the foo subsystem and adds a bar flag.\n"
            "\n"
            "### Added\n"
            "- Add the bar flag. (#5)\n"
            "\n"
            "### Fixed\n"
            "- Fix the foo regression. (#6)\n"
        )
        doc = parse(text)
        normalize(doc)
        rendered = render(doc)
        self.assertIn(
            "Fixes a regression in the foo subsystem and adds a bar flag.",
            rendered,
            "summary paragraph under versioned section was stripped",
        )

    def test_html_comment_block_under_unreleased_preserved(self) -> None:
        text = (
            "# Changelog\n"
            "\n"
            "## [Unreleased]\n"
            "\n"
            "<!--\n"
            "Keep-a-Changelog conventions:\n"
            "  - Recommended: one-sentence summary leads each version.\n"
            "  - Six legal headings: Added · Changed · Deprecated · Removed · Fixed · Security.\n"
            "-->\n"
            "\n"
            "## [1.2.0] - 2026-01-15\n"
            "\n"
            "### Added\n"
            "- Add foo. (#1)\n"
        )
        doc = parse(text)
        normalize(doc)
        rendered = render(doc)
        self.assertIn("Keep-a-Changelog conventions:", rendered,
                      "HTML comment block under [Unreleased] was stripped")
        self.assertIn("Six legal headings:", rendered,
                      "multi-line HTML comment lost interior lines")

    def test_empty_preamble_emits_no_extra_blank_line(self) -> None:
        """A version with no preamble must round-trip without inserting one."""
        text = (
            "# Changelog\n"
            "\n"
            "## [Unreleased]\n"
            "\n"
            "## [1.2.0] - 2026-01-15\n"
            "\n"
            "### Added\n"
            "- Add foo. (#1)\n"
        )
        doc = parse(text)
        normalize(doc)
        rendered = render(doc)
        # No extra empty line between version header and first subsection.
        self.assertNotRegex(
            rendered,
            r"## \[1\.2\.0\][^\n]*\n\n\n+### Added",
            "empty preamble produced spurious blank line",
        )

    def test_preamble_round_trip_idempotent(self) -> None:
        """parse → render → parse → render must be stable when preamble is present."""
        text = (
            "# Changelog\n"
            "\n"
            "## [Unreleased]\n"
            "\n"
            "<!-- contributor scaffolding -->\n"
            "\n"
            "## [1.2.0] - 2026-01-15\n"
            "\n"
            "Brief summary of what 1.2.0 contains.\n"
            "\n"
            "### Added\n"
            "- Add foo. (#1)\n"
        )
        once = render(normalize(parse(text)) or parse(text))
        twice = render(normalize(parse(once)) or parse(once))
        self.assertEqual(once, twice, "preamble round-trip is not idempotent")


if __name__ == "__main__":
    unittest.main()
