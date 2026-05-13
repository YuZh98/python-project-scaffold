"""Pinning tests for load-bearing rules from GUIDELINES.md.

Each rule is asserted via static analysis (AST inspection) of production code.
A failing test means a rule was violated — fix the rule violation, do not loosen
the test, unless GUIDELINES is updated first.

When a new rule is codified before the codebase is fully compliant, mark the
test ``@pytest.mark.xfail(strict=False, reason="...; closes #N")`` and link the
follow-on PR that will close the gap. Aspirational rules without a bridge are
policy fiction (see CLAUDE.md universal rule: "no rule lands without its enforcement").
"""

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

_SRC_DIR = REPO_ROOT / "src"


# ── Rule: No print() in production code ───────────────────────────────────────


class TestNoPrintDebugInProductionCode:
    """No print() calls in production source code under src/.

    print() in production code pollutes stdout and indicates leftover debugging.
    Use logging instead.

    Excluded from this check: tests/, .venv/, docs/, __pycache__/.
    """

    _SCOPE_DIRS = [_SRC_DIR]

    def test_no_print_calls_in_src(self) -> None:
        """Assert that no bare print() call appears in any src/ file.

        Walks each file's AST and finds ast.Call nodes whose func is an
        ast.Name with id == 'print'. Method calls (obj.print()) are not flagged.
        """
        violations: list[str] = []

        for scope in self._SCOPE_DIRS:
            for file_path in sorted(scope.rglob("*.py")):
                src = file_path.read_text(encoding="utf-8")
                tree = ast.parse(src)

                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "print"
                    ):
                        rel = file_path.relative_to(REPO_ROOT)
                        violations.append(
                            f"{rel}:{node.lineno}: print() call in production code. "
                            f"Remove before committing — use logging instead."
                        )

        assert not violations, (
            "No-print violation(s) — print() calls found in src/:\n"
            + "\n".join(f"  {v}" for v in violations)
        )


# ── Rule: No secrets in repo ──────────────────────────────────────────────────


class TestNoSecretsInRepo:
    """No hardcoded secrets in src/ or repo root files.

    Scans for common secret patterns: API keys, passwords, private keys,
    AWS access key IDs, OpenAI-style keys, and Bearer tokens.

    Excluded: tests/, .git/, .venv/, docs/.
    """

    _SCAN_DIRS = [_SRC_DIR]
    _ROOT_GLOB_PATTERNS = ["*.py", "*.toml", "*.cfg", "*.ini", "*.yml", "*.yaml"]
    _SECRET_PATTERNS = [
        re.compile(r"API_KEY\s*=\s*['\"][^'\"]{8,}['\"]"),
        re.compile(r"PASSWORD\s*=\s*['\"][^'\"]{4,}['\"]"),
        re.compile(r"PRIVATE_KEY"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        re.compile(r"Bearer [A-Za-z0-9._-]+"),
    ]

    def _scan_file(self, file_path: Path) -> list[str]:
        violations: list[str] = []
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return violations
        for lineno, line in enumerate(lines, start=1):
            for pattern in self._SECRET_PATTERNS:
                if pattern.search(line):
                    rel = file_path.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel}:{lineno}: potential secret matched pattern "
                        f"'{pattern.pattern}'. Remove or move to env var."
                    )
                    break  # one report per line is enough
        return violations

    def test_no_secrets_in_src(self) -> None:
        """Assert that no common secret pattern appears in src/ or repo-root config files."""
        violations: list[str] = []

        for scope in self._SCAN_DIRS:
            for file_path in sorted(scope.rglob("*.py")):
                violations.extend(self._scan_file(file_path))

        for pattern in self._ROOT_GLOB_PATTERNS:
            for file_path in sorted(REPO_ROOT.glob(pattern)):
                violations.extend(self._scan_file(file_path))

        assert not violations, "Secret pattern(s) found in repo:\n" + "\n".join(
            f"  {v}" for v in violations
        )


# ── Rule: Every public function has type hints ────────────────────────────────


class TestEveryPublicFnHasTypeHints:
    """Every top-level non-private function in src/ must have type annotations.

    - Parameter annotations required (excluding self/cls).
    - Return annotation required.
    - Private functions (names starting with _) are excluded.
    - Methods inside classes are also included (excluding self/cls).
    """

    _SCOPE_DIRS = [_SRC_DIR]
    _EXCLUDED_PARAMS = {"self", "cls"}

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: Path
    ) -> list[str]:
        violations: list[str] = []
        if node.name.startswith("_"):
            return violations

        rel = file_path.relative_to(REPO_ROOT)

        # Check return annotation
        if node.returns is None:
            violations.append(
                f"{rel}:{node.lineno}: public function '{node.name}' missing "
                f"return type annotation. Add '-> <type>' per GUIDELINES §4."
            )

        # Check parameter annotations (skip self/cls)
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            if arg.arg in self._EXCLUDED_PARAMS:
                continue
            if arg.annotation is None:
                violations.append(
                    f"{rel}:{node.lineno}: public function '{node.name}' "
                    f"parameter '{arg.arg}' missing type annotation. "
                    f"Per GUIDELINES §4."
                )

        return violations

    def test_public_fns_have_type_hints(self) -> None:
        """Assert that every public function/method in src/ has full type annotations."""
        violations: list[str] = []

        for scope in self._SCOPE_DIRS:
            for file_path in sorted(scope.rglob("*.py")):
                src = file_path.read_text(encoding="utf-8")
                tree = ast.parse(src)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        violations.extend(self._check_function(node, file_path))

        assert not violations, (
            "Type-hint violation(s) — public functions missing annotations:\n"
            + "\n".join(f"  {v}" for v in violations)
        )


# ── Rule: No mutable default arguments ───────────────────────────────────────


class TestNoMutableDefaultArgs:
    """No mutable default arguments (list, dict, set) in any src/ function.

    Mutable defaults are a classic Python gotcha — the same object is shared
    across all calls. Use None and instantiate inside the function body instead.
    """

    _SCOPE_DIRS = [_SRC_DIR]
    _MUTABLE_TYPES = (ast.List, ast.Dict, ast.Set)

    def test_no_mutable_default_args_in_src(self) -> None:
        """Assert that no function in src/ uses a mutable literal as a default argument."""
        violations: list[str] = []

        for scope in self._SCOPE_DIRS:
            for file_path in sorted(scope.rglob("*.py")):
                src = file_path.read_text(encoding="utf-8")
                tree = ast.parse(src)

                for node in ast.walk(tree):
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    for default in node.args.defaults + node.args.kw_defaults:
                        if default is None:
                            continue
                        if isinstance(default, self._MUTABLE_TYPES):
                            type_name = type(default).__name__.replace("ast.", "")
                            rel = file_path.relative_to(REPO_ROOT)
                            violations.append(
                                f"{rel}:{node.lineno}: function '{node.name}' has "
                                f"a mutable default argument ({type_name} literal). "
                                f"Use None and instantiate in the body instead."
                            )

        assert not violations, "Mutable-default violation(s):\n" + "\n".join(
            f"  {v}" for v in violations
        )


# ── Rule: Import contract ────────────────────────────────────────────────────


class TestImportContract:
    """Import contract placeholder — fill in after writing ADR-0001.

    _FORBIDDEN_PAIRS lists (importer_module, imported_module) pairs that
    violate the layered import contract defined in ADR-0001. Entries are
    matched against dotted module names relative to the package root.

    Ship with an empty list so this test always passes on a fresh scaffold.
    Add entries when ADR-0001 is written.

    Empty default — fill in when ADR-0001 names the import-contract layers.
    Until then this test passes vacuously by design (see module docstring).

    Example (do not uncomment until ADR-0001 is written):
        _FORBIDDEN_PAIRS = [
            ("<<PACKAGE_NAME>>.ui", "<<PACKAGE_NAME>>.db"),  # ui must not import db directly
        ]
    """

    _FORBIDDEN_PAIRS: list[tuple[str, str]] = []

    _SCOPE_DIRS = [_SRC_DIR]

    def _dotted_name(self, file_path: Path) -> str:
        """Convert a src/<package>/sub/module.py path to a dotted module name."""
        rel = file_path.relative_to(_SRC_DIR)
        parts = list(rel.with_suffix("").parts)
        return ".".join(parts)

    def test_import_contract(self) -> None:
        """Assert that no forbidden (importer, imported) pair exists in src/.

        With _FORBIDDEN_PAIRS = [], this test always passes. Fill in the pairs
        after writing ADR-0001 to enforce the layered import contract.
        """
        if not self._FORBIDDEN_PAIRS:
            return  # nothing to check until ADR-0001 is written

        violations: list[str] = []

        for scope in self._SCOPE_DIRS:
            for file_path in sorted(scope.rglob("*.py")):
                importer = self._dotted_name(file_path)
                src = file_path.read_text(encoding="utf-8")
                tree = ast.parse(src)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.ImportFrom):
                            imported = node.module or ""
                        else:
                            imported = ", ".join(alias.name for alias in node.names)

                        for (
                            forbidden_importer,
                            forbidden_imported,
                        ) in self._FORBIDDEN_PAIRS:
                            if importer.startswith(
                                forbidden_importer
                            ) and imported.startswith(forbidden_imported):
                                rel = file_path.relative_to(REPO_ROOT)
                                violations.append(
                                    f"{rel}:{node.lineno}: '{importer}' imports "
                                    f"'{imported}', which violates the import contract "
                                    f"(ADR-0001). Forbidden pair: "
                                    f"({forbidden_importer}, {forbidden_imported})."
                                )

        assert not violations, (
            "Import-contract violation(s) — ADR-0001 boundary crossed:\n"
            + "\n".join(f"  {v}" for v in violations)
        )


# ── Rule: Parameterised SQL only ─────────────────────────────────────────────


class TestNoStringConcatenatedSQL:
    """Pinning test for "parameterized SQL only" (GUIDELINES §5).

    Scans every src/**/*.py for ``execute(`` or ``executemany(`` calls
    where the SQL argument is built via f-string or ``+`` concatenation.
    Both patterns leak user input into the SQL — a classic injection vector.

    Vacuous-pass behaviour: when no DB library is imported anywhere under
    src/, the test passes (no SQL means no violation). When a project
    starts using sqlite3 / psycopg2 / asyncpg / SQLAlchemy and the test
    finds string-concatenated SQL, it fires.
    """

    _DB_IMPORT_HINTS = (
        "sqlite3",
        "psycopg2",
        "asyncpg",
        "sqlalchemy",
        "duckdb",
        "mysql",
    )

    def test_no_string_concatenated_sql(self) -> None:
        src = REPO_ROOT / "src"
        if not src.is_dir():
            pytest.skip("No src/ directory yet — bootstrapping scaffold.")
        violations: list[str] = []
        for py_file in src.rglob("*.py"):
            try:
                src_text = py_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            # Cheap pre-filter: only walk AST if file imports a DB library.
            if not any(hint in src_text for hint in self._DB_IMPORT_HINTS):
                continue
            try:
                tree = ast.parse(src_text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in {"execute", "executemany"}
                ):
                    continue
                if not node.args:
                    continue
                arg = node.args[0]
                # Flag f-string or ``+`` concatenation as the SQL string.
                bad = False
                if isinstance(arg, ast.JoinedStr):  # f-string
                    bad = True
                elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                    bad = True
                if bad:
                    rel = py_file.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel}:{node.lineno}: string-concatenated SQL detected; "
                        f"use parameterised queries "
                        f'(cursor.execute("SELECT ... WHERE x = ?", (val,))).'
                    )
        assert not violations, "\n".join(violations)
