"""Pinning tests for project-wide structural invariants (cohesion).

These complement `test_rules.py` (rule-level checks) by asserting that the
file tree / import graph follows ADR-0001 (the import contract). Empty
initially — fill in when ADR-0001 is written.
"""

import ast
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
            f"No package __init__.py found under src/ — "
            f"create at least one src/<package>/__init__.py."
        )
