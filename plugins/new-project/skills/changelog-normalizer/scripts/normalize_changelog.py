#!/usr/bin/env python3
"""Normalize a CHANGELOG.md file to Keep-a-Changelog style.

Mechanical fixes are applied silently. Ambiguous cases (subheading choice, missing
refs, candidate duplicates, multi-sentence collapse) are written to stderr with line
numbers; the script does not guess. In --check mode the script exits non-zero on any
issue and never writes. In --diff mode it prints a unified diff and never writes.
Otherwise it writes the normalized file in place, leaving a .bak alongside.

This script is bundled with the changelog-normalizer skill. The skill orchestrator
reads the stderr warnings and surfaces them to the user before re-running.
"""
from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Canonical vocabulary
# ---------------------------------------------------------------------------

CANONICAL_SUBHEADINGS: tuple[str, ...] = (
    "Added",
    "Changed",
    "Deprecated",
    "Removed",
    "Fixed",
    "Security",
)

# Common drift → canonical name. Keys are lowercased.
SUBHEADING_ALIASES: dict[str, str] = {
    "added": "Added",
    "new": "Added",
    "new features": "Added",
    "features": "Added",
    "additions": "Added",
    "changed": "Changed",
    "changes": "Changed",
    "updates": "Changed",
    "updated": "Changed",
    "improvements": "Changed",
    "enhancements": "Changed",
    "fixed": "Fixed",
    "fixes": "Fixed",
    "bugfixes": "Fixed",
    "bug fixes": "Fixed",
    "bugs": "Fixed",
    "removed": "Removed",
    "removals": "Removed",
    "security": "Security",
    "deprecated": "Deprecated",
    "deprecations": "Deprecated",
}

# Verbs that signal a past-tense / gerund / third-person entry, mapped to their
# imperative form. Order matters only for longest-match safety inside word boundaries.
TENSE_FIXES: dict[str, str] = {
    "Added": "Add",
    "Adds": "Add",
    "Adding": "Add",
    "Removed": "Remove",
    "Removes": "Remove",
    "Removing": "Remove",
    "Fixed": "Fix",
    "Fixes": "Fix",
    "Fixing": "Fix",
    "Changed": "Change",
    "Changes": "Change",
    "Changing": "Change",
    "Updated": "Update",
    "Updates": "Update",
    "Updating": "Update",
    "Refactored": "Refactor",
    "Refactors": "Refactor",
    "Refactoring": "Refactor",
    "Improved": "Improve",
    "Improves": "Improve",
    "Improving": "Improve",
    "Resolved": "Resolve",
    "Resolves": "Resolve",
    "Resolving": "Resolve",
    "Simplified": "Simplify",
    "Simplifies": "Simplify",
    "Simplifying": "Simplify",
    "Dropped": "Drop",
    "Drops": "Drop",
    "Dropping": "Drop",
    "Deprecated": "Deprecate",
    "Deprecates": "Deprecate",
    "Deprecating": "Deprecate",
    "Replaced": "Replace",
    "Replaces": "Replace",
    "Replacing": "Replace",
    "Introduced": "Introduce",
    "Introduces": "Introduce",
    "Introducing": "Introduce",
    "Implemented": "Implement",
    "Implements": "Implement",
    "Implementing": "Implement",
    "Renamed": "Rename",
    "Renames": "Rename",
    "Renaming": "Rename",
    "Supported": "Support",
    "Supports": "Support",
    "Supporting": "Support",
    "Allowed": "Allow",
    "Allows": "Allow",
    "Allowing": "Allow",
    "Exposed": "Expose",
    "Exposes": "Expose",
    "Exposing": "Expose",
}

# Process-narrative phrases that should be stripped silently. Patterns are
# case-insensitive and match phrases anywhere in the entry; the surrounding
# punctuation is cleaned up afterward.
PROCESS_NARRATIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\s*per\s+claude(?:'s)?\s+(?:audit|review)\s+(?:pass|feedback)\s*\d*", re.I),
    re.compile(r"\s*per\s+(?:re-?)?audit\s+(?:pass|feedback)\s*\d*", re.I),
    re.compile(r"\s*per\s+agent(?:'s)?\s+(?:suggestion|feedback|recommendation)", re.I),
    re.compile(r"\s*based\s+on\s+(?:re-?)?audit\s+(?:pass|feedback)\s*\d*\s*findings?", re.I),
    re.compile(r"\s*per\s+ai\s+(?:review|audit|feedback)", re.I),
    re.compile(r"\s*after\s+review\s+iteration\s*\d*", re.I),
    re.compile(r"\s*following\s+claude(?:'s)?\s+(?:review|audit|suggestion)", re.I),
    re.compile(r"\s*as\s+suggested\s+by\s+(?:claude|agent|ai)", re.I),
    re.compile(r"\s*from\s+claude(?:'s)?\s+(?:review|audit)\s+pass\s*\d*", re.I),
)

# Lines to drop entirely if they appear inside the entry body.
DROP_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*Co-Authored-By:\s*Claude.*$", re.I),
    re.compile(r"^\s*Co-Authored-By:\s*.*<noreply@anthropic\.com>.*$", re.I),
    re.compile(r"^\s*Generated\s+(?:with|by)\s+Claude(?:\s+Code)?.*$", re.I),
)

# Verbs that often indicate a subheading is ambiguous between Added/Changed.
AMBIGUOUS_VERBS: tuple[str, ...] = (
    "make",
    "expose",
    "support",
    "allow",
    "enable",
)

# A ref looks like (#123) or (abc1234) — 7 or more hex chars for short SHA.
REF_RE: re.Pattern[str] = re.compile(r"\((#\d+|[0-9a-f]{7,40})\)\s*$")

VERSION_HEADER_RE: re.Pattern[str] = re.compile(
    r"^##\s*"
    r"(?:\[(?P<v_bracket>[^\]]+)\]|v?(?P<v_plain>\d+\.\d+\.\d+))"
    r"\s*(?:[-–—]|\(|\b)\s*"
    r"(?P<date>\d{4}-\d{2}-\d{2})?"
    r"\)?\s*$",
    re.I,
)
UNRELEASED_HEADER_RE: re.Pattern[str] = re.compile(
    r"^##\s*\[?unreleased\]?\s*$", re.I
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Warning_:
    """A normalization warning. Surfaced on stderr; never auto-fixed."""

    line: int
    kind: str
    message: str

    def render(self) -> str:
        return f"line {self.line}: [{self.kind}] {self.message}"


@dataclass
class Entry:
    """A single bullet under a subheading. May span multiple physical lines."""

    text: str  # the entry text without leading "- " and without ref
    ref: str | None  # "(#42)" or "(abc1234)" or None
    raw_lines: list[str] = field(default_factory=list)
    source_line: int = 0


@dataclass
class Section:
    """One ### subheading and its entries."""

    name: str
    entries: list[Entry] = field(default_factory=list)
    source_line: int = 0


@dataclass
class Version:
    """One ## version block."""

    header_line: str  # canonical "## [X.Y.Z] - YYYY-MM-DD" or "## [Unreleased]"
    sections: list[Section] = field(default_factory=list)
    raw_header_source_line: int = 0


@dataclass
class Document:
    """Parsed CHANGELOG."""

    prelude: list[str] = field(default_factory=list)  # everything before first version
    versions: list[Version] = field(default_factory=list)
    link_refs: list[str] = field(default_factory=list)  # bottom-of-file link refs
    warnings: list[Warning_] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse(text: str) -> Document:
    """Parse CHANGELOG text into a Document.

    The parser is forgiving: it accepts drifted subheading names and bullet symbols,
    captures the original lines for diffing, and records warnings for things it
    cannot resolve unambiguously.
    """
    lines = text.splitlines()
    doc = Document()

    i = 0
    n = len(lines)

    # Prelude: everything before the first ## header.
    while i < n and not lines[i].lstrip().startswith("## "):
        doc.prelude.append(lines[i])
        i += 1

    while i < n:
        line = lines[i]
        # Bottom-of-file link refs section start: a line that looks like "[X]: http..."
        # outside a version block ends the version parsing.
        if _is_link_ref(line):
            doc.link_refs.extend(lines[i:])
            break

        if not line.lstrip().startswith("## "):
            # Stray content between version blocks — keep as part of last version's
            # trailing whitespace if it's blank; otherwise warn.
            if line.strip() == "" and doc.versions:
                # Whitespace is harmless.
                i += 1
                continue
            if doc.versions:
                doc.warnings.append(
                    Warning_(i + 1, "stray-content",
                             f"unexpected content outside a version block: {line!r}")
                )
            i += 1
            continue

        version, consumed = _parse_version_block(lines, i, doc)
        doc.versions.append(version)
        i += consumed

    return doc


def _is_link_ref(line: str) -> bool:
    return bool(re.match(r"^\[[^\]]+\]:\s+\S+", line.strip()))


def _parse_version_block(
    lines: list[str], start: int, doc: Document
) -> tuple[Version, int]:
    header = lines[start]
    canonical, ok = _canonicalize_version_header(header, start + 1, doc)
    version = Version(header_line=canonical, raw_header_source_line=start + 1)
    if not ok:
        doc.warnings.append(
            Warning_(start + 1, "version-header",
                     f"could not parse version header {header!r}; left a TODO marker")
        )

    i = start + 1
    n = len(lines)
    current_section: Section | None = None

    while i < n:
        line = lines[i]
        if line.lstrip().startswith("## "):
            break
        if _is_link_ref(line):
            break

        # Subheading?
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            raw_name = m.group(1).strip()
            canon = SUBHEADING_ALIASES.get(raw_name.lower())
            if canon is None:
                # Unknown subheading — flag and skip its entries.
                doc.warnings.append(
                    Warning_(i + 1, "unknown-subheading",
                             f"unknown subheading {raw_name!r}; expected one of "
                             f"{', '.join(CANONICAL_SUBHEADINGS)}")
                )
                # Use the raw name so the writer can pass it through with a marker.
                current_section = Section(name=raw_name, source_line=i + 1)
            else:
                current_section = Section(name=canon, source_line=i + 1)
            version.sections.append(current_section)
            i += 1
            continue

        # Entry?
        entry_match = re.match(r"^([\-*+•])\s+(.*)$", line)
        if entry_match and current_section is not None:
            entry, consumed = _parse_entry(lines, i)
            current_section.entries.append(entry)
            i += consumed
            continue

        # Anything else (blank line, prose) — preserve into the section, or skip.
        i += 1

    return version, i - start


def _canonicalize_version_header(
    header: str, _lineno: int, _doc: Document
) -> tuple[str, bool]:
    """Return (canonical_header, ok). `_lineno`/`_doc` reserved for future diagnostics."""
    del _lineno, _doc
    if UNRELEASED_HEADER_RE.match(header):
        return "## [Unreleased]", True

    m = VERSION_HEADER_RE.match(header)
    if not m:
        # Last-resort: pull a semver out of the header.
        sv = re.search(r"(\d+\.\d+\.\d+)", header)
        if sv:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", header)
            if date_match:
                return f"## [{sv.group(1)}] - {date_match.group(1)}", True
            return f"## [{sv.group(1)}] - YYYY-MM-DD   <!-- TODO: confirm release date -->", False
        return header, False

    version = m.group("v_bracket") or m.group("v_plain") or ""
    date = m.group("date")
    if not date:
        return f"## [{version}] - YYYY-MM-DD   <!-- TODO: confirm release date -->", False
    return f"## [{version}] - {date}", True


def _parse_entry(lines: list[str], start: int) -> tuple[Entry, int]:
    """Parse a bullet entry which may span multiple lines via indented continuation.

    Returns the entry and the number of lines consumed.
    """
    head = lines[start]
    m = re.match(r"^([\-*+•])\s+(.*)$", head)
    assert m is not None
    body = m.group(2)
    raw = [head]
    i = start + 1
    n = len(lines)
    # Continuation lines are indented (>=2 spaces) and not a new bullet/heading.
    while i < n:
        nxt = lines[i]
        if nxt.strip() == "":
            break
        if re.match(r"^([\-*+•])\s+", nxt):
            break
        if nxt.lstrip().startswith("##"):
            break
        if not nxt.startswith((" ", "\t")):
            break
        raw.append(nxt)
        body += "\n" + nxt
        i += 1

    ref = None
    ref_match = REF_RE.search(body.strip())
    if ref_match:
        ref = ref_match.group(0).strip()
        body = body[: ref_match.start()].rstrip()

    return Entry(text=body, ref=ref, raw_lines=raw, source_line=start + 1), i - start


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize(doc: Document) -> Document:
    """Apply mechanical fixes; append warnings for ambiguous cases."""
    for version in doc.versions:
        for section in version.sections:
            for entry in section.entries:
                _normalize_entry_text(entry, section, doc)
            _flag_duplicates(section, doc)
        _sort_sections(version)
        # Empty subheadings under [Unreleased] are workspace scaffolding —
        # contributors add bullets under them as work lands. Drop only from
        # versioned sections (omit-empty-at-release per spec §5.3).
        if not version.header_line.startswith("## [Unreleased]"):
            _drop_empty_sections(version)
        _flag_subheading_ambiguity(version, doc)
    _sort_versions(doc)
    return doc


def _normalize_entry_text(entry: Entry, section: Section, doc: Document) -> None:
    text = entry.text

    # 1. Strip Co-Authored-By and similar lines from continuation.
    new_lines: list[str] = []
    for raw_line in text.split("\n"):
        if any(p.match(raw_line) for p in DROP_LINE_PATTERNS):
            continue
        new_lines.append(raw_line)
    text = "\n".join(new_lines)

    # 2. Strip process-narrative phrases.
    for pattern in PROCESS_NARRATIVE_PATTERNS:
        text = pattern.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    text = text.rstrip(",;: ").strip()

    # 3. BREAKING marker: normalize to **BREAKING**:.
    text = re.sub(r"^\s*BREAKING\s*[:\-]\s*", "**BREAKING**: ", text)

    # 4. First-word imperative conversion. We only touch the first word; if the
    #    entry has already been written in the imperative we leave it alone.
    first_word_match = re.match(r"^(\*\*BREAKING\*\*:\s*)?([A-Za-z][\w'-]*)", text)
    if first_word_match:
        prefix = first_word_match.group(1) or ""
        first_word = first_word_match.group(2)
        imperative = TENSE_FIXES.get(first_word)
        if imperative is not None:
            text = prefix + imperative + text[first_word_match.end():]

    # 5. Capitalize first letter of body (after any BREAKING prefix).
    body_match = re.match(r"^(\*\*BREAKING\*\*:\s*)?(.*)$", text, re.DOTALL)
    if body_match and body_match.group(2):
        prefix = body_match.group(1) or ""
        body = body_match.group(2)
        if body and body[0].islower():
            body = body[0].upper() + body[1:]
        text = prefix + body

    # 6. Terminal punctuation: every entry ends with a period before its ref.
    #    The canonical form is "- Verb object. (#ref)". This matches the user's
    #    concrete examples; multi-sentence entries already have internal periods
    #    and only need to ensure the final clause is terminated.
    text = text.rstrip()
    if text and not text.endswith((".", "!", "?")):
        text = text + "."

    # 7. Nested-bullet flag.
    if any(re.match(r"^\s+[\-*+•]\s+", ln) for ln in entry.raw_lines[1:]):
        doc.warnings.append(
            Warning_(entry.source_line, "nested-bullets",
                     "entry has nested bullets; ask the user to fold them into the parent")
        )

    entry.text = text

    # 8. Missing ref → warning, do not fabricate.
    if entry.ref is None and text.strip():
        doc.warnings.append(
            Warning_(entry.source_line, "missing-ref",
                     f"no PR/commit ref on entry: {text!r}; ask the user for it")
        )

    # 9. Ambiguous-verb flag (only if section is "Changed"; "make X configurable"
    #    might belong under "Added").
    if section.name == "Changed":
        first = text.split(maxsplit=1)[0].lower() if text else ""
        if first in AMBIGUOUS_VERBS:
            doc.warnings.append(
                Warning_(entry.source_line, "ambiguous-subheading",
                         f"entry under 'Changed' starts with {first!r}; could be "
                         f"'Added' if this exposes new functionality. Ask the user.")
            )

    # 10. Verb/section mismatch — when the verb strongly implies a different
    #     subheading than the one the entry currently sits under. Common case:
    #     "Fix X" under "Changed", or "Add X" under "Fixed".
    verb_to_section: dict[str, str] = {
        "add": "Added",
        "introduce": "Added",
        "fix": "Fixed",
        "resolve": "Fixed",
        "remove": "Removed",
        "drop": "Removed",
        "deprecate": "Deprecated",
        "rename": "Changed",
    }
    first_word = text.split(maxsplit=1)[0].lower() if text else ""
    implied = verb_to_section.get(first_word)
    if implied and implied != section.name and section.name in CANONICAL_SUBHEADINGS:
        doc.warnings.append(
            Warning_(entry.source_line, "verb-section-mismatch",
                     f"entry under {section.name!r} starts with {first_word!r}, "
                     f"which implies {implied!r}. Ask the user which is correct "
                     f"before moving.")
        )


def _flag_duplicates(section: Section, doc: Document) -> None:
    """Flag candidate duplicates within a section by shingle similarity."""
    entries = section.entries
    for i in range(len(entries)):
        for j in range(i + 1, len(entries)):
            sim = _shingle_similarity(entries[i].text, entries[j].text)
            if sim >= 0.55:
                doc.warnings.append(
                    Warning_(
                        entries[j].source_line,
                        "candidate-duplicate",
                        f"entry resembles line {entries[i].source_line} "
                        f"(similarity {sim:.2f}); ask the user whether to merge",
                    )
                )


def _shingle_similarity(a: str, b: str) -> float:
    def shingles(s: str) -> set[str]:
        words = re.findall(r"\w+", s.lower())
        return {" ".join(words[k : k + 2]) for k in range(len(words) - 1)} or {s.lower()}

    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _sort_sections(version: Version) -> None:
    order = {name: idx for idx, name in enumerate(CANONICAL_SUBHEADINGS)}
    version.sections.sort(key=lambda s: order.get(s.name, len(order) + 1))


def _drop_empty_sections(version: Version) -> None:
    version.sections = [s for s in version.sections if s.entries]


def _flag_subheading_ambiguity(_version: Version, _doc: Document) -> None:
    # Already handled per-entry; this hook exists for future cross-section checks.
    del _version, _doc
    return


def _sort_versions(doc: Document) -> None:
    """[Unreleased] first; the rest by semver descending where possible."""

    def version_key(v: Version) -> tuple[int, tuple[int, ...]]:
        if v.header_line.startswith("## [Unreleased]"):
            return (0, ())
        m = re.search(r"\[(\d+)\.(\d+)\.(\d+)\]", v.header_line)
        if not m:
            return (2, ())
        parts = tuple(-int(x) for x in m.groups())  # negative for descending
        return (1, parts)

    doc.versions.sort(key=version_key)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render(doc: Document) -> str:
    out: list[str] = []
    out.extend(doc.prelude)
    if doc.prelude and doc.prelude[-1].strip() != "":
        out.append("")

    for version in doc.versions:
        out.append(version.header_line)
        out.append("")
        for section in version.sections:
            if section.name in CANONICAL_SUBHEADINGS:
                out.append(f"### {section.name}")
            else:
                # Unknown subheading preserved but marked.
                out.append(f"### {section.name}   <!-- TODO: canonical subheading -->")
            for entry in section.entries:
                out.append(_render_entry(entry))
            out.append("")

    if doc.link_refs:
        # Ensure exactly one blank line before link refs.
        while out and out[-1].strip() == "":
            out.pop()
        out.append("")
        out.extend(doc.link_refs)

    # Trim trailing blank lines, then ensure one final newline.
    while out and out[-1].strip() == "":
        out.pop()
    return "\n".join(out) + "\n"


def _render_entry(entry: Entry) -> str:
    parts = entry.text.split("\n")
    head = parts[0]
    if entry.ref:
        line = f"- {head} {entry.ref}"
    else:
        line = f"- {head} <!-- TODO: ref -->"
    if len(parts) > 1:
        # Preserve continuation lines verbatim under the bullet.
        tail = "\n".join(parts[1:])
        line = f"{line}\n{tail}"
    return line


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_with_backup(path: Path, content: str) -> Path:
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    path.write_text(content, encoding="utf-8")
    return backup


def _diff(original: str, normalized: str, path: Path) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            normalized.splitlines(keepends=True),
            fromfile=f"{path} (original)",
            tofile=f"{path} (normalized)",
        )
    )


def _emit_warnings(warnings: Iterable[Warning_], stream) -> int:
    count = 0
    for w in warnings:
        stream.write(w.render() + "\n")
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize CHANGELOG.md to Keep-a-Changelog style.",
    )
    parser.add_argument("path", type=Path, help="Path to CHANGELOG.md")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="CI mode: report issues, exit non-zero on any, do not write.",
    )
    group.add_argument(
        "--diff",
        action="store_true",
        help="Print unified diff of proposed changes; do not write.",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        sys.stderr.write(f"error: {args.path} does not exist\n")
        return 2

    original = _read(args.path)
    doc = parse(original)
    normalize(doc)
    normalized = render(doc)

    issue_count = _emit_warnings(doc.warnings, sys.stderr)
    changed = normalized != original

    if args.check:
        if issue_count or changed:
            sys.stderr.write(
                f"check failed: {issue_count} warning(s), "
                f"{'content changes needed' if changed else 'no content changes'}\n"
            )
            return 1
        return 0

    if args.diff:
        diff = _diff(original, normalized, args.path)
        if diff:
            sys.stdout.write(diff)
        return 1 if (issue_count or changed) else 0

    if changed:
        backup = _write_with_backup(args.path, normalized)
        sys.stderr.write(f"wrote {args.path} (backup: {backup})\n")
    else:
        sys.stderr.write("no mechanical changes needed\n")
    return 1 if issue_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
