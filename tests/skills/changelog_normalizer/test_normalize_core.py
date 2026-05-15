"""Characterization tests for the core parse/normalize/render pipeline.

These tests pin the current observable behavior of the normalizer so that silent
regressions in the 757-line script are caught. They cover three things:

1. Round-trip idempotency: parse -> render -> parse -> render is stable.
2. ``--check`` exits non-zero on a CHANGELOG with violations.
3. ``--check`` exits zero on a fully canonical CHANGELOG.
4. Past-tense / gerund first words are rewritten to imperative mood.

The tense test exercises ``_normalize_entry_text`` indirectly by running the
full ``parse -> normalize -> render`` pipeline on a one-entry CHANGELOG.
Constructing ``Entry``/``Section``/``Document`` instances by hand to call the
private helper directly would couple the test to internal data-class shape;
the public pipeline is the stable surface the script's CLI and consumers use.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                      / "plugins/new-project/skills/changelog-normalizer/scripts"))
from normalize_changelog import normalize, parse, render  # type: ignore[import-not-found]  # noqa: E402


SCRIPT_PATH: Path = (
    Path(__file__).resolve().parents[3]
    / "plugins/new-project/skills/changelog-normalizer/scripts/normalize_changelog.py"
)


# A canonical, fully-normalized CHANGELOG used by both the round-trip and the
# clean-input --check tests. Sections are in canonical order, every entry has
# a ref, every entry is imperative, every entry ends in a period.
CLEAN_CHANGELOG: str = """# Changelog

## [Unreleased]

## [1.2.0] - 2026-01-15

### Added
- Add the bar option. (#5)

### Fixed
- Fix the baz crash. (#6)

## [1.1.0] - 2025-12-01

### Added
- Add the initial foo flag. (#1)
"""


class TestParseRenderRoundtrip(unittest.TestCase):
    def test_parse_render_roundtrip_idempotent(self) -> None:
        """parse -> render -> parse -> render must not oscillate between states."""
        text = (
            "# Changelog\n"
            "\n"
            "## [Unreleased]\n"
            "\n"
            "### Added\n"
            "- Add the foo flag. (#10)\n"
            "\n"
            "## [1.2.0] - 2026-01-15\n"
            "\n"
            "### Added\n"
            "- Add the bar option. (#5)\n"
            "\n"
            "### Fixed\n"
            "- Fix the baz crash. (#6)\n"
        )
        doc1 = parse(text)
        normalize(doc1)
        rendered1 = render(doc1)

        doc2 = parse(rendered1)
        normalize(doc2)
        rendered2 = render(doc2)

        self.assertEqual(
            rendered1,
            rendered2,
            msg="normalizer oscillates between two states across successive runs",
        )


class TestCheckMode(unittest.TestCase):
    def test_check_mode_exits_nonzero_on_violations(self) -> None:
        """A CHANGELOG with a drifted subheading and missing ref must fail --check."""
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "CHANGELOG.md"
            # Violations: 'New Features' is a drifted subheading alias for 'Added';
            # the entry has no ref; the first word 'Added' is past tense.
            bad_path.write_text(
                "# Changelog\n"
                "\n"
                "## [Unreleased]\n"
                "\n"
                "### New Features\n"
                "- Added support for foo bar\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(bad_path), "--check"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(
                result.returncode,
                0,
                msg=f"expected non-zero exit; stderr was: {result.stderr!r}",
            )

    def test_check_mode_exits_zero_on_clean_input(self) -> None:
        """A fully canonical CHANGELOG must pass --check with exit code 0."""
        with tempfile.TemporaryDirectory() as tmp:
            clean_path = Path(tmp) / "CHANGELOG.md"
            clean_path.write_text(CLEAN_CHANGELOG, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(clean_path), "--check"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=(
                    f"expected exit 0 on clean input; "
                    f"stderr={result.stderr!r} stdout={result.stdout!r}"
                ),
            )


class TestTenseNormalization(unittest.TestCase):
    def test_tense_normalization_via_pipeline(self) -> None:
        """Past-tense first word ('Added') must be rewritten to imperative ('Add').

        ``_normalize_entry_text`` is the function under test, but it operates on
        Entry/Section/Document instances. We exercise it via the public
        parse -> normalize -> render pipeline to avoid coupling to internal
        dataclass shape.
        """
        text = (
            "# Changelog\n"
            "\n"
            "## [Unreleased]\n"
            "\n"
            "### Added\n"
            "- Added new --dry-run flag (#42)\n"
        )
        doc = parse(text)
        normalize(doc)
        rendered = render(doc)

        self.assertIn(
            "- Add ",
            rendered,
            msg=f"expected imperative 'Add' in output; got: {rendered!r}",
        )
        self.assertNotIn(
            "- Added ",
            rendered,
            msg=f"past tense 'Added' should have been rewritten; got: {rendered!r}",
        )


if __name__ == "__main__":
    unittest.main()
