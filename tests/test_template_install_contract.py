"""Pinning test: template CI workflow + Makefile install the package itself.

Background: the template uses a `src/` layout (`src/<package_name>/...`) and
`pytest.ini` declares `pythonpath = .`. With that combination, tests written
as `from <package_name>.example import ...` only resolve when the package is
installed (editable or otherwise) — not by mere presence of `src/`.

Historically the template's CI step and `make install` target installed only
`requirements.txt` + `requirements-dev.txt`, never the package itself. The
first push to a freshly scaffolded repo turned every CI run red — Dependabot
PRs included — with `ModuleNotFoundError: No module named '<package>'`.

ADR-0000 D1 specifies `pip install -e .` as the intended workflow. This test
pins that intent into mechanical enforcement so the gap can't silently
reappear.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_CI = REPO_ROOT / "template" / ".github" / "workflows" / "ci.yml"
TEMPLATE_MAKEFILE = REPO_ROOT / "template" / "Makefile"

EDITABLE_INSTALL_RE = re.compile(r"pip\s+install\s+(?:-e|--editable)\s+\.")


class TestTemplateInstallsPackage:
    """Both CI and Makefile must install the scaffolded package itself.

    Without this, tests using src-layout imports fail collection on a freshly
    scaffolded repo's very first push.
    """

    def test_ci_workflow_pip_installs_package(self) -> None:
        content = TEMPLATE_CI.read_text(encoding="utf-8")
        assert EDITABLE_INSTALL_RE.search(content), (
            f"{TEMPLATE_CI.relative_to(REPO_ROOT)} must contain "
            "`pip install -e .` after the requirements install — without it, "
            "pytest collection fails with ModuleNotFoundError on a src-layout "
            "package. See ADR-0000 D1."
        )

    def test_makefile_install_target_installs_package(self) -> None:
        content = TEMPLATE_MAKEFILE.read_text(encoding="utf-8")
        assert EDITABLE_INSTALL_RE.search(content), (
            f"{TEMPLATE_MAKEFILE.relative_to(REPO_ROOT)} must contain "
            "`pip install -e .` in the install target — without it, "
            "`make test` after `make install` fails with ModuleNotFoundError. "
            "See ADR-0000 D1."
        )
