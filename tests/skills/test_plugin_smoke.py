"""Smoke test: plugin files exist, manifests parse, surface_detect runs on empty diff."""
import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "new-project"
SKILLS_ROOT = PLUGIN_ROOT / "skills"
SKILL_NAMES = ["new-project", "release-helper", "changelog-normalizer", "audit-runner"]


class TestPluginSmoke(unittest.TestCase):
    def test_marketplace_manifest_parses(self) -> None:
        data = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
        self.assertEqual(data["name"], "python-project-scaffold")
        self.assertEqual(len(data["plugins"]), 1)

    def test_plugin_manifest_parses(self) -> None:
        # Plugin manifest lives at <plugin-dir>/.claude-plugin/plugin.json per
        # Claude Code's documented plugin layout. Locating it elsewhere causes
        # `/plugin install` to silently fail.
        data = json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(data["name"], "new-project")
        self.assertTrue(data["version"])

    def test_all_skills_have_skill_md(self) -> None:
        for name in SKILL_NAMES:
            skill_md = SKILLS_ROOT / name / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"missing {skill_md}")

    def test_surface_detect_on_empty_diff(self) -> None:
        result = subprocess.run(
            ["python3", str(SKILLS_ROOT / "audit-runner" / "scripts" / "surface_detect.py")],
            input="",
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout), [])


if __name__ == "__main__":
    unittest.main()
