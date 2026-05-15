"""Refresh dev-dep lower bounds in a requirements file to current upstream minors.

For each package line shaped as `<name>>=<X.Y[.Z]>,<<upper>`, query PyPI for the
current latest version, compute the major.minor floor, and rewrite the lower
bound. The upper bound is preserved untouched.

Why: the template's `requirements-dev.txt` ships frozen lower bounds. Time
passes, upstream releases new minors, and Dependabot opens "bump the floor"
PRs the moment a fresh repo is bootstrapped. Refreshing the floors at
bootstrap time so they already match current upstream leaves Dependabot
nothing to do on day one.

Best-effort: if PyPI is unreachable or returns an error for a package, the
line is left unchanged and a warning is emitted. Bootstrap should not fail on
a transient network issue.

Usage:
    python3 scripts/refresh_dev_deps.py <path-to-requirements-file>

Exit codes:
    0 — Success. Some lines may have been left unchanged due to network
        errors; warnings emitted to stderr. The bootstrap caller should
        treat exit 0 as "proceed" regardless of how many floors moved.
    2 — Argument error (no file path, bad path, unreadable file).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

PINNED_RE = re.compile(
    r"^(?P<name>[a-zA-Z0-9][a-zA-Z0-9_.\-]*)"
    r"(?P<extras>\[[^\]]+\])?"
    r"\s*>=\s*"
    r"(?P<floor>[0-9]+(?:\.[0-9]+){0,2})"
    r"\s*,\s*"
    r"<\s*"
    r"(?P<ceiling>[0-9]+(?:\.[0-9]+){0,2})"
    r"\s*$"
)

PYPI_TIMEOUT_SECONDS = 5.0


def fetch_latest_version(pkg: str, timeout: float = PYPI_TIMEOUT_SECONDS) -> str | None:
    """Return the current latest released version of `pkg` on PyPI, or None on failure."""
    url = f"https://pypi.org/pypi/{pkg}/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.load(resp)
    except Exception as exc:
        sys.stderr.write(f"refresh-dev-deps: warn — could not fetch {pkg}: {exc}\n")
        return None
    version = data.get("info", {}).get("version")
    return version if isinstance(version, str) else None


def major_minor(version: str) -> str:
    """Return the 'major.minor' prefix of a dotted version string."""
    parts = version.split(".")
    if len(parts) < 2:
        return version
    return f"{parts[0]}.{parts[1]}"


def rewrite_line(line: str, fetcher=fetch_latest_version) -> tuple[str, bool]:
    """Rewrite a `<pkg>>=<floor>,<<ceiling>` line.

    Returns (new_line, changed). Lines that don't match the expected shape, or
    where the fetcher returns None, are returned verbatim with `changed=False`.
    The injectable `fetcher` parameter exists so tests can stub PyPI access.
    """
    stripped = line.rstrip("\n")
    m = PINNED_RE.match(stripped.strip())
    if m is None:
        return line, False
    name = m.group("name")
    extras = m.group("extras") or ""
    current_floor = m.group("floor")
    ceiling = m.group("ceiling")
    latest = fetcher(name)
    if latest is None:
        return line, False
    new_floor = major_minor(latest)
    if new_floor == current_floor:
        return line, False
    suffix = "\n" if line.endswith("\n") else ""
    return f"{name}{extras}>={new_floor},<{ceiling}{suffix}", True


def refresh(path: Path, fetcher=fetch_latest_version) -> int:
    """Refresh `path` in place. Returns process exit code."""
    if not path.is_file():
        sys.stderr.write(f"refresh-dev-deps: file not found: {path}\n")
        return 2
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_lines: list[str] = []
    changed_count = 0
    for line in lines:
        new_line, changed = rewrite_line(line, fetcher=fetcher)
        new_lines.append(new_line)
        if changed:
            changed_count += 1
    if changed_count:
        path.write_text("".join(new_lines), encoding="utf-8")
        sys.stderr.write(
            f"refresh-dev-deps: rewrote {changed_count} floor(s) in {path}\n"
        )
    else:
        sys.stderr.write(f"refresh-dev-deps: no changes for {path}\n")
    return 0


def main() -> None:
    if len(sys.argv) != 2:
        sys.stderr.write(f"usage: {sys.argv[0]} <requirements-file>\n")
        sys.exit(2)
    sys.exit(refresh(Path(sys.argv[1])))


if __name__ == "__main__":
    main()
