"""Drift guard: SKILL.md's values.json key list must include every required placeholder.

This test catches the class of bug where SKILL.md and template.manifest.json silently
diverge — i.e. SKILL omits a placeholder that substitute.py declares required, leading
to exit-code-2 failures on every skill invocation.

The test parses SKILL.md to extract the keys = [...] block in the python3 heredoc
of Step 5, and compares against the manifest's required placeholders.

CI-skip behaviour: SKILL.md lives at ~/.claude/skills/new-project/SKILL.md, which is
a user-local file absent on CI runners. The test calls pytest.skip() when the path
does not exist so CI stays green. The test fires on any developer machine that has the
skill installed and runs pytest.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "template.manifest.json"
SKILL_PATH = Path.home() / ".claude" / "skills" / "new-project" / "SKILL.md"


class TestSkillManifestParity:
    """SKILL.md's values.json keys must cover every required manifest placeholder."""

    # Auto-derived placeholders (computed by substitute.py from other values) — exempt.
    AUTO_DERIVED = {"<<RUFF_TARGET>>"}

    def test_skill_includes_all_required_placeholders(self) -> None:
        # Required keys per manifest.
        manifest = json.loads(MANIFEST_PATH.read_text())
        required = {
            key for key, spec in manifest["placeholders"].items()
            if spec.get("required", False)
        } - self.AUTO_DERIVED

        # SKILL.md may not exist on CI (it's a user-personal file). If missing, skip.
        if not SKILL_PATH.exists():
            import pytest
            pytest.skip(f"SKILL.md not present at {SKILL_PATH} (CI runner has no user skill).")

        skill_text = SKILL_PATH.read_text()
        # Extract the keys = [...] list from SKILL.md
        match = re.search(r"keys\s*=\s*\[([^\]]+)\]", skill_text, re.DOTALL)
        assert match, "Could not find 'keys = [...]' block in SKILL.md"
        keys_block = match.group(1)
        skill_keys = set(re.findall(r'"(<<[A-Z_]+>>)"', keys_block))

        missing = required - skill_keys
        extra = skill_keys - required

        assert not missing, (
            f"SKILL.md is missing required placeholders: {missing}. "
            f"Every required placeholder in template.manifest.json must appear in "
            f"the keys list of SKILL.md Step 5 — otherwise substitute.py will exit 2."
        )
        assert not extra, (
            f"SKILL.md has placeholders not in manifest: {extra}. "
            f"Either add to manifest or remove from SKILL.md."
        )
