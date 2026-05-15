"""Pin the universal SKILL.md authoring convention from SKILL_AUTHORING.md."""
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "plugins" / "new-project" / "skills"

# Each required section MUST appear as a markdown heading (`#`, `##`, or `###`)
# whose text matches one of the patterns below (case-insensitive). Substring
# matching is too lax: "output" trivially appears in any English prose, and
# "trigger" can appear inside body text without an actual section.
REQUIRED_SECTION_PATTERNS = [
    ("trigger examples", re.compile(r"^#{1,4}\s+.*trigger\b", re.IGNORECASE | re.MULTILINE)),
    ("IO examples",      re.compile(r"^#{1,4}\s+.*(io\s+examples?|input/output|examples?)\b",
                                    re.IGNORECASE | re.MULTILINE)),
    ("drift policy",     re.compile(r"^#{1,4}\s+.*drift\b", re.IGNORECASE | re.MULTILINE)),
    ("concrete output",  re.compile(r"^#{1,4}\s+.*output\b", re.IGNORECASE | re.MULTILINE)),
]


class TestSkillConvention(unittest.TestCase):
    def test_each_skill_md_contains_required_section_headings(self) -> None:
        skill_dirs = [p for p in SKILLS_ROOT.iterdir() if p.is_dir()]
        self.assertGreaterEqual(len(skill_dirs), 4, "expected ≥4 skills")
        for d in skill_dirs:
            content = (d / "SKILL.md").read_text()
            for section_name, pattern in REQUIRED_SECTION_PATTERNS:
                self.assertRegex(
                    content,
                    pattern,
                    f"{d.name}/SKILL.md missing required section heading: {section_name}",
                )


if __name__ == "__main__":
    unittest.main()
