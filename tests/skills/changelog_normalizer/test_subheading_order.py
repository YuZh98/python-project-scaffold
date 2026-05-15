"""Pin the canonical Keep-a-Changelog 1.1.0 subheading order.

Per https://keepachangelog.com/en/1.1.0/ the canonical order is:
    Added · Changed · Deprecated · Removed · Fixed · Security

A regression that re-orders these (e.g. Fixed before Deprecated) silently
re-orders every changelog the normalizer touches and contradicts the spec
the SKILL.md cites as authority. This test prevents that drift.
"""
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                      / "plugins/new-project/skills/changelog-normalizer/scripts"))
from normalize_changelog import CANONICAL_SUBHEADINGS  # type: ignore[import-not-found]  # noqa: E402


class TestSubheadingOrder(unittest.TestCase):
    def test_canonical_subheadings_match_keepachangelog_1_1_0(self) -> None:
        expected = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
        self.assertEqual(CANONICAL_SUBHEADINGS, expected)


if __name__ == "__main__":
    unittest.main()
