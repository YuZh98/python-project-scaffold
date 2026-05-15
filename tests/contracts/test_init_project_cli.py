"""Contract test: plugin's bootstrap.sh depends on these init-project.py flags."""
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_FLAGS = {"--target", "--values", "--yes"}


class TestInitProjectCLI(unittest.TestCase):
    def test_required_flags_present_in_help(self) -> None:
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "scripts" / "init-project.py"), "--help"],
            capture_output=True,
            text=True,
            check=True,
        )
        help_text = result.stdout + result.stderr
        for flag in REQUIRED_FLAGS:
            self.assertIn(
                flag,
                help_text,
                f"plugin depends on {flag}; init-project.py --help no longer mentions it",
            )


if __name__ == "__main__":
    unittest.main()
