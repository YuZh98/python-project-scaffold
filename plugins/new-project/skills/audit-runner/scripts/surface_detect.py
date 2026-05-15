#!/usr/bin/env python3
"""Diff scanner for audit-runner.

Reads a unified diff (from stdin or --diff-file), scans the added/removed lines for
trigger patterns associated with each of the five context-aware audit dimensions, and
emits a JSON list of findings to stdout. The coordinator agent reads this output to
decide which context-aware sub-agents to spawn.

Output schema (list of objects, each):
    {
        "dim": "<security|performance|observability|interface|dependency>",
        "trigger": "<pattern-slug>",
        "file": "<path>",
        "line": <int>            # post-diff line number in the new file
    }

Exit codes:
    0  — scan completed (output may be an empty list).
    2  — invalid invocation or unreadable input.

This is intentionally conservative: it errs toward *flagging* triggers rather than
missing them. False positives cost one sub-agent invocation; false negatives cause
silent skips, which is exactly what the audit framework is designed to prevent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Iterator


# --------------------------------------------------------------------------------------
# Trigger patterns per dimension.
#
# Each pattern is a (slug, compiled regex) pair. The regex is matched against added
# (`+`) lines only — removed lines do not "introduce" a surface, with one explicit
# exception: the `interface` dim cares about *removed* public symbols. We handle that
# branch separately.
#
# Patterns target Python source unless noted; file-level filters narrow scope (e.g.
# `dependency` triggers only fire inside pyproject.toml / requirements*.txt / uv.lock).
# --------------------------------------------------------------------------------------

SECURITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("subprocess.", re.compile(r"\bsubprocess\.")),
    ("eval(", re.compile(r"\beval\s*\(")),
    ("exec(", re.compile(r"\bexec\s*\(")),
    ("os.environ_write", re.compile(r"\bos\.environ\s*\[\s*['\"][^'\"]+['\"]\s*\]\s*=")),
    ("os.environ_setdefault", re.compile(r"\bos\.environ\.setdefault\s*\(")),
    ("network_urlopen", re.compile(r"\burllib\.request\.urlopen\b|\brequests\.\w+\s*\(|\bhttpx\.\w+\s*\(")),
    ("pickle_load", re.compile(r"\bpickle\.loads?\s*\(")),
    ("yaml_load_unsafe", re.compile(r"\byaml\.load\s*\((?![^)]*Loader\s*=\s*yaml\.SafeLoader)")),
    ("path_from_input", re.compile(r"\bPath\s*\(\s*(?:input\s*\(|sys\.argv|request\.)")),
    ("sql_string_format", re.compile(r"\b(execute|executemany)\s*\(\s*(?:f['\"]|['\"][^'\"]*%\s|['\"][^'\"]*\.format)")),
    ("auth_path", re.compile(r"\b(authenticate|authorize|verify_token|check_password|hash_password)\b")),
]

PERFORMANCE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Narrow DB-query patterns. Bare `.get(`/`.filter(` collide with dict and
    # framework methods (false positives in tests, requests.get, dict.get).
    # Restrict to session/cursor/connection calls that are unambiguously DB.
    ("db_session_call", re.compile(r"\bsession\.(execute|query|add|delete|commit|flush|merge)\b")),
    ("db_cursor_execute", re.compile(r"\b(cursor|conn(?:ection)?)\.execute(?:many)?\s*\(")),
    ("sync_in_async", re.compile(r"\btime\.sleep\s*\(|\brequests\.\w+\s*\(")),
    ("removed_index", re.compile(r"\bDROP\s+INDEX\b", re.IGNORECASE)),
    ("new_external_call", re.compile(r"\b(httpx|requests|aiohttp)\.\w+\s*\(")),
    ("nested_loop_over_query", re.compile(r"^\s*for\s+\w+\s+in\s+.*\.(all|filter|query)\s*\(", re.MULTILINE)),
]

OBSERVABILITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("exception_swallowed", re.compile(r"^\s*(except\s+[\w.,\s()]*:\s*$|except\s+[\w.,\s()]*:\s*pass\b)", re.MULTILINE)),
    ("bare_except", re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)),
    ("log_level_changed", re.compile(r"\blog(?:ger)?\.(debug|info|warning|error|critical|exception)\s*\(")),
    ("new_failure_path", re.compile(r"\braise\s+\w+|^\s*assert\s+", re.MULTILINE)),
    ("metric_call", re.compile(r"\b(statsd|prometheus|metrics)\.\w+\s*\(|\bcounter\.\w+\s*\(|\bhistogram\.\w+\s*\(")),
]

INTERFACE_PATTERNS_ADDED: list[tuple[str, re.Pattern[str]]] = [
    # Default-kwarg semantics change: a kwarg's default literal changed on an added
    # `def` line. Detected weakly here; coordinator confirms with paired removals.
    ("default_kwarg_added", re.compile(r"^\s*def\s+\w+\s*\([^)]*=\s*[^)]+\)")),
    # return_type_narrowed removed: regex `->\s+\w+\s*:` matched every annotated
    # function, making the interface dim effectively always-on. Real narrowing
    # detection requires diff-context awareness (was a type changed/widened?),
    # which is out of scope for a line-pattern scanner. The sub-agent confirms
    # interface concerns via the dimension checklist; surface_detect is the
    # trigger, not the diagnosis.
    ("new_exception_type", re.compile(r"^\s*class\s+\w+(?:Error|Exception)\s*\(", re.MULTILINE)),
]

# Interface also looks at REMOVED lines for public-symbol deletions.
INTERFACE_PATTERNS_REMOVED: list[tuple[str, re.Pattern[str]]] = [
    ("public_symbol_removed", re.compile(r"^\s*(def|class)\s+(?!_)\w+")),
    ("public_constant_removed", re.compile(r"^\s*[A-Z][A-Z0-9_]*\s*[:=]")),
]

DEPENDENCY_FILES = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "uv.lock",
    "poetry.lock",
    "setup.cfg",
    "setup.py",
)


# --------------------------------------------------------------------------------------
# Diff parsing.
# --------------------------------------------------------------------------------------


@dataclass
class HunkLine:
    """One line inside a diff hunk, after the prefix `+`/`-`/` ` is stripped."""

    file: str
    new_lineno: int  # post-diff line number; -1 if this is a removed line
    old_lineno: int  # pre-diff line number; -1 if this is an added line
    kind: str        # "+", "-", or " "
    text: str


_FILE_HEADER_RE = re.compile(r"^\+\+\+ b/(.+)$")
_OLD_FILE_HEADER_RE = re.compile(r"^--- a/(.+)$")
_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_diff(diff_text: str) -> Iterator[HunkLine]:
    """Yield one HunkLine per non-header line in a unified diff.

    Skips file-mode lines and binary indicators. Tracks current file path and the
    paired old/new line counters from each `@@` hunk header.
    """
    current_file = ""
    old_lineno = 0
    new_lineno = 0
    in_hunk = False
    for raw in diff_text.splitlines():
        # New-file path line: `+++ b/path/to/file`
        m = _FILE_HEADER_RE.match(raw)
        if m:
            current_file = m.group(1)
            in_hunk = False
            continue
        # Old-file path line: ignore (we track via `+++` for new path; deletions of an
        # entire file use `/dev/null` on the `+++` side, which we tolerate).
        if _OLD_FILE_HEADER_RE.match(raw):
            in_hunk = False
            continue
        # Hunk header: reset counters.
        m = _HUNK_HEADER_RE.match(raw)
        if m:
            old_lineno = int(m.group(1))
            new_lineno = int(m.group(2))
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if not raw:
            # Blank line inside a hunk is a context line of length 0.
            yield HunkLine(file=current_file, new_lineno=new_lineno, old_lineno=old_lineno, kind=" ", text="")
            old_lineno += 1
            new_lineno += 1
            continue
        prefix, body = raw[0], raw[1:]
        if prefix == "+":
            yield HunkLine(file=current_file, new_lineno=new_lineno, old_lineno=-1, kind="+", text=body)
            new_lineno += 1
        elif prefix == "-":
            yield HunkLine(file=current_file, new_lineno=-1, old_lineno=old_lineno, kind="-", text=body)
            old_lineno += 1
        elif prefix == " ":
            yield HunkLine(file=current_file, new_lineno=new_lineno, old_lineno=old_lineno, kind=" ", text=body)
            old_lineno += 1
            new_lineno += 1
        elif prefix == "\\":
            # "\ No newline at end of file" — ignore.
            continue
        else:
            # Unknown prefix; skip silently.
            continue


# --------------------------------------------------------------------------------------
# Surface detection.
# --------------------------------------------------------------------------------------


@dataclass
class Finding:
    dim: str
    trigger: str
    file: str
    line: int


def _is_python(path: str) -> bool:
    return path.endswith(".py")


def _is_dependency_file(path: str) -> bool:
    name = Path(path).name
    return name in DEPENDENCY_FILES or (name.startswith("requirements") and name.endswith(".txt"))


def _is_sql(path: str) -> bool:
    return path.endswith(".sql")


def scan_lines(lines: Iterable[HunkLine]) -> list[Finding]:
    """Apply all trigger patterns to a stream of diff lines.

    Returns a deduped list of Finding records. Dedup key is
    (dim, trigger, file, line) so the same pattern matching twice on the same line
    yields one finding.
    """
    findings: list[Finding] = []
    seen: set[tuple[str, str, str, int]] = set()

    def _add(dim: str, trigger: str, file: str, line: int) -> None:
        key = (dim, trigger, file, line)
        if key in seen:
            return
        seen.add(key)
        findings.append(Finding(dim=dim, trigger=trigger, file=file, line=line))

    for hl in lines:
        # Added-line patterns: security / performance / observability / interface(added).
        if hl.kind == "+" and _is_python(hl.file):
            for slug, pat in SECURITY_PATTERNS:
                if pat.search(hl.text):
                    _add("security", slug, hl.file, hl.new_lineno)
            for slug, pat in PERFORMANCE_PATTERNS:
                if pat.search(hl.text):
                    _add("performance", slug, hl.file, hl.new_lineno)
            for slug, pat in OBSERVABILITY_PATTERNS:
                if pat.search(hl.text):
                    _add("observability", slug, hl.file, hl.new_lineno)
            for slug, pat in INTERFACE_PATTERNS_ADDED:
                if pat.search(hl.text):
                    _add("interface", slug, hl.file, hl.new_lineno)

        # Added-line SQL files: parameterised-query heuristics on SQL itself are out of
        # scope here (the security `sql_string_format` regex targets Python callsites).
        # We *do* flag dropped indexes in `.sql` files.
        if hl.kind == "+" and _is_sql(hl.file):
            for slug, pat in PERFORMANCE_PATTERNS:
                if slug == "removed_index" and pat.search(hl.text):
                    _add("performance", slug, hl.file, hl.new_lineno)

        # Removed-line patterns: only interface cares about deletions.
        if hl.kind == "-" and _is_python(hl.file):
            for slug, pat in INTERFACE_PATTERNS_REMOVED:
                if pat.search(hl.text):
                    # Removed lines lack a new_lineno; we report the old_lineno so the
                    # auditor can find the line in the base ref.
                    _add("interface", slug, hl.file, hl.old_lineno)

        # Dependency triggers fire on any change inside dependency files. The trigger
        # is the file-level event, not a regex match — we emit one finding per modified
        # dep file line that introduces or bumps a package.
        if hl.kind == "+" and _is_dependency_file(hl.file):
            text = hl.text.strip()
            if not text or text.startswith("#"):
                continue
            # pyproject.toml dependency lines look like `"package>=1.0",` inside a
            # `dependencies = [` array. requirements*.txt lines look like `package==1.0`.
            # We emit `new_dep_added` for any non-comment, non-blank added line in a dep
            # file; the dependency sub-agent decides whether it's a bump vs new add.
            if re.search(r"^[\"\']?[A-Za-z0-9_.\-]+[\"\']?\s*[><=~!]", text) or re.search(
                r"^[A-Za-z0-9_.\-]+\s*==", text
            ):
                _add("dependency", "new_dep_added_or_bumped", hl.file, hl.new_lineno)

    return findings


# --------------------------------------------------------------------------------------
# CLI.
# --------------------------------------------------------------------------------------


def _read_diff(diff_file: str | None) -> str:
    if diff_file is None or diff_file == "-":
        return sys.stdin.read()
    path = Path(diff_file)
    if not path.is_file():
        sys.stderr.write(f"surface_detect: diff file not found: {diff_file}\n")
        sys.exit(2)
    return path.read_text(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a unified diff for audit-runner surface triggers. Emits a JSON list "
            "of (dim, trigger, file, line) findings to stdout."
        ),
    )
    parser.add_argument(
        "--diff-file",
        default=None,
        help="Path to a unified-diff file. If omitted or '-', reads from stdin.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output (default: compact one-line-per-finding).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    diff_text = _read_diff(args.diff_file)
    findings = scan_lines(parse_diff(diff_text))
    payload = [asdict(f) for f in findings]
    if args.pretty:
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    else:
        sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
