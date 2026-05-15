"""Smoke test for init-project.py --in-place mode.

CRITICAL: must run inside a `shutil.copytree` of the scaffold REPO_ROOT,
NEVER against the live source. The script self-modifies + self-deletes; any
in-source run permanently damages the scaffold.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


class TestInitProjectInPlace:
    SAMPLE_VALUES = {
        "<<PROJECT_NAME>>": "smoketest-app",
        "<<PROJECT_TITLE>>": "Smoketest App",
        "<<PACKAGE_NAME>>": "smoketest_app",
        "<<DESCRIPTION>>": "Init-project smoke test.",
        "<<AUTHOR_NAME>>": "Test User",
        "<<AUTHOR_EMAIL>>": "test@example.com",
        "<<YEAR>>": "2026",
        "<<LICENSE_ID>>": "MIT",
        "<<PYTHON_FLOOR>>": "3.11",
        "<<GITHUB_USERNAME>>": "smoketestuser",
    }

    def test_in_place_self_bootstraps_repo(self, tmp_path: Path) -> None:
        # Live-source guard.
        live_script = REPO_ROOT / "scripts" / "init-project.py"
        assert live_script.exists(), (
            "Live source missing — test must run against a fresh checkout "
            "with scripts/init-project.py intact."
        )

        # Copy the entire scaffold to an isolated fork.
        fork = tmp_path / "fork"
        shutil.copytree(
            REPO_ROOT,
            fork,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__"
            ),
        )
        # Init git inside the fork so the script's commit step works.
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=fork,
            check=True,
            capture_output=True,
        )

        # Pre-populated git author for the fork's commits (CI has no global config).
        env: dict[str, str] = {}
        env.update(os.environ)
        env.update(
            {
                "GIT_AUTHOR_NAME": self.SAMPLE_VALUES["<<AUTHOR_NAME>>"],
                "GIT_AUTHOR_EMAIL": self.SAMPLE_VALUES["<<AUTHOR_EMAIL>>"],
                "GIT_COMMITTER_NAME": self.SAMPLE_VALUES["<<AUTHOR_NAME>>"],
                "GIT_COMMITTER_EMAIL": self.SAMPLE_VALUES["<<AUTHOR_EMAIL>>"],
            }
        )

        values_path = tmp_path / "values.json"
        values_path.write_text(json.dumps(self.SAMPLE_VALUES))

        result = subprocess.run(
            [
                sys.executable,
                "scripts/init-project.py",
                "--values",
                str(values_path),
                "--no-install",
                "--keep-history",
                "--yes",
            ],
            cwd=fork,
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, (
            f"init-project.py exited {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

        # Verify template/, scripts/, scaffold-only files gone.
        for rel in (
            "template",
            "scripts/init-project.py",
            "scripts/scaffold.sh",
            "template.manifest.json",
            "tests/test_scaffold.py",
            "tests/test_init_project.py",
        ):
            assert not (fork / rel).exists(), f"{rel} still present in fork"

        # Verify template files moved to root.
        for rel in (
            "pyproject.toml",
            "README.md",
            "Makefile",
            "src/smoketest_app/__init__.py",
            "tests/test_rules.py",
        ):
            assert (fork / rel).exists(), f"{rel} missing from bootstrapped fork"

        # Verify no stray placeholders.
        # `plugins/` and `tooling/` are scaffold-monorepo infra (Claude Code plugin
        # source + deprecated skill source); they're not part of a bootstrapped
        # project and legitimately contain `<<…>>` tokens as JSON keys in
        # bootstrap.sh. Skip during the placeholder sweep.
        for path in fork.rglob("*"):
            if not path.is_file():
                continue
            if any(
                p in path.parts
                for p in (".git", ".venv", ".pytest_cache", "__pycache__",
                          "plugins", "tooling")
            ):
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            assert not ("<<" in content and ">>" in content) or all(
                ph not in content for ph in self.SAMPLE_VALUES
            ), f"Stray placeholder in {path.relative_to(fork)}"

        # Verify first commit exists.
        log = subprocess.run(
            ["git", "log", "--oneline"], cwd=fork, capture_output=True, text=True
        )
        assert log.returncode == 0
        assert "scaffold" in log.stdout.lower() or "bootstrap" in log.stdout.lower()
