"""Pinning tests for project-wide structural invariants (cohesion).

These complement `test_rules.py` (rule-level checks) by asserting that the
file tree / import graph follows ADR-0001 (the import contract). Empty
initially — fill in when ADR-0001 is written.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


class TestSrcLayoutPresent:
    """Sanity: src/ exists and contains at least one package __init__.py.

    This is a structural smoke test — if the src layout collapses, lots of
    downstream pinning tests stop matching anything and silently pass.
    """

    def test_src_dir_exists_with_init(self) -> None:
        src = REPO_ROOT / "src"
        assert src.exists() and src.is_dir(), f"src/ missing at {src}"
        init_files = list(src.glob("*/__init__.py"))
        assert init_files, (
            "No package __init__.py found under src/ — "
            "create at least one src/<package>/__init__.py."
        )


class TestChangelogFormat:
    """Keep-a-Changelog discipline pinning test (GUIDELINES §10).

    Enforces: [Unreleased] section present; subsection headings limited
    to the six legal Keep-a-Changelog tokens (Added/Changed/Fixed/
    Removed/Deprecated/Security); each versioned section leads with a
    summary paragraph before its first subsection. Tokens inside HTML
    comments are allowed — they're documentation.
    """

    LEGAL_HEADINGS = {"Added", "Changed", "Fixed", "Removed", "Deprecated", "Security"}

    def test_unreleased_section_present(self) -> None:
        changelog = REPO_ROOT / "CHANGELOG.md"
        assert changelog.exists(), "CHANGELOG.md missing at repo root."
        content = changelog.read_text(encoding="utf-8")
        # Strip HTML comments to avoid false positives.
        stripped = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
        unreleased_count = len(
            re.findall(r"^## \[Unreleased\]", stripped, flags=re.MULTILINE)
        )
        assert unreleased_count == 1, (
            f"CHANGELOG.md should contain exactly one ## [Unreleased] heading; "
            f"found {unreleased_count}."
        )

    def test_only_legal_subsection_headings(self) -> None:
        changelog = REPO_ROOT / "CHANGELOG.md"
        content = changelog.read_text(encoding="utf-8")
        stripped = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
        # Find every ### heading after a ## [...] section.
        violations = []
        for match in re.finditer(r"^### (.+)$", stripped, flags=re.MULTILINE):
            heading = match.group(1).strip()
            if heading not in self.LEGAL_HEADINGS:
                line_no = stripped[: match.start()].count("\n") + 1
                violations.append(
                    f"CHANGELOG.md:{line_no}: illegal subsection heading '{heading}' "
                    f"— legal: {sorted(self.LEGAL_HEADINGS)}"
                )
        assert not violations, "\n".join(violations)

    # (Removed in v0.1.1: test_versioned_sections_have_summary. The
    # summary-paragraph-before-bullets convention is a stylistic preference
    # that helps top-down readability but isn't part of the KaC spec. It is
    # documented as a recommendation in template/CHANGELOG.md's HTML comment
    # and is no longer mechanically enforced.)
