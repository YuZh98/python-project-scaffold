"""Characterization tests for the core parse/normalize/render pipeline.

These tests pin the current observable behavior of the normalizer so that silent
regressions in the script are caught. They cover three things:

1. Round-trip idempotency: parse -> render -> parse -> render is stable.
2. ``--check`` exits non-zero on a CHANGELOG with violations.
3. ``--check`` exits zero on a fully canonical CHANGELOG.

(Removed in v0.1.1: tense-normalization test. Imperative-mood rewriting was
taste-level enforcement, not industry-universal. The normalizer no longer
rewrites verbs.)
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
# a ref, every entry ends in a period.
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
            # the entry has no ref. (Note: imperative-mood enforcement removed in v0.1.1.)
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


if __name__ == "__main__":
    unittest.main()
