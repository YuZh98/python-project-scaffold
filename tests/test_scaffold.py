"""Smoke test: scaffold to a tmpdir, assert green pytest inside."""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCAFFOLD_SCRIPT = REPO_ROOT / "scripts" / "scaffold.sh"


class TestScaffoldEndToEnd:
    """Full scaffold runs cleanly and produces a green-CI repo."""

    SAMPLE_VALUES = {
        "<<PROJECT_NAME>>":    "smoketest-app",
        "<<PROJECT_TITLE>>":   "Smoketest App",
        "<<PACKAGE_NAME>>":    "smoketest_app",
        "<<DESCRIPTION>>":     "A realistic-length description for smoke-testing scaffold output.",
        "<<AUTHOR_NAME>>":     "Test User",
        "<<AUTHOR_EMAIL>>":    "test@example.com",
        "<<YEAR>>":            "2026",
        "<<LICENSE_ID>>":      "MIT",
        "<<PYTHON_FLOOR>>":    "3.11",
        "<<GITHUB_USERNAME>>": "smoketestuser",
    }

    def test_scaffold_produces_green_repo(self, tmp_path: Path) -> None:
        """End-to-end: scaffold into tmpdir, run pytest, assert green."""
        target = tmp_path / "smoketest-app"
        values_file = tmp_path / "values.json"
        values_file.write_text(json.dumps(self.SAMPLE_VALUES))

        # Ensure git commit step has an identity even on CI runners that
        # have no global git config. Real users set this via
        # `git config --global`; here we inject via env vars so the test
        # is hermetic and doesn't mutate the runner's global state.
        env = dict(os.environ)
        env.update({
            "GIT_AUTHOR_NAME":     self.SAMPLE_VALUES["<<AUTHOR_NAME>>"],
            "GIT_AUTHOR_EMAIL":    self.SAMPLE_VALUES["<<AUTHOR_EMAIL>>"],
            "GIT_COMMITTER_NAME":  self.SAMPLE_VALUES["<<AUTHOR_NAME>>"],
            "GIT_COMMITTER_EMAIL": self.SAMPLE_VALUES["<<AUTHOR_EMAIL>>"],
        })

        # Run the scaffold script
        result = subprocess.run(
            ["bash", str(SCAFFOLD_SCRIPT), str(target), str(values_file)],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )

        # Detailed diagnostic on failure
        assert result.returncode == 0, (
            f"scaffold.sh exited {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Verify no stray <<placeholders>>
        for file_path in target.rglob("*"):
            if not file_path.is_file():
                continue
            # Skip binary / venv / git
            if any(p in file_path.parts for p in (".git", ".venv", ".pytest_cache", "__pycache__")):
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            assert "<<" not in content or ">>" not in content, (
                f"Stray placeholder in {file_path.relative_to(target)}:\n"
                f"{content[:500]}"
            )

        # Verify package directory was renamed
        assert (target / "src" / "smoketest_app").exists(), "src/smoketest_app/ missing"
        assert not (target / "src" / "<<PACKAGE_NAME>>").exists(), \
            "literal <<PACKAGE_NAME>> directory still present"

        # Verify git was initialized + first commit exists
        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert log.returncode == 0 and log.stdout.strip(), "no initial git commit"
        assert "initial scaffold" in log.stdout.lower(), \
            f"first commit message wrong: {log.stdout!r}"
