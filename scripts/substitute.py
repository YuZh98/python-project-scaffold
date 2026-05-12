"""
Placeholder substitution engine for python-project-scaffold.

Usage:
    python scripts/substitute.py --target <path-to-new-repo> --values <path-to-values-json>

Exit codes:
    0  — success
    2  — validation failure (missing required placeholder or regex mismatch)
    3  — orphan placeholder found in target tree (not in registry)
    4  — file write failure (rollback performed)
    5  — post-substitution orphan placeholder remains
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MANIFEST_PATH = Path(__file__).parent.parent / "template.manifest.json"
PLACEHOLDER_RE = re.compile(r"<<[A-Z0-9_]+>>")

# License text stubs for non-MIT SPDX IDs (v2: fetch full text from SPDX).
LICENSE_STUBS: dict[str, str] = {
    "Apache-2.0": (
        "# License: Apache-2.0\n"
        "# TODO(v2): fetch full text from "
        "https://www.apache.org/licenses/LICENSE-2.0.txt\n"
    ),
    "BSD-3-Clause": (
        "# License: BSD-3-Clause\n"
        "# TODO(v2): fetch full text from "
        "https://spdx.org/licenses/BSD-3-Clause.html\n"
    ),
    "Unlicense": (
        "# License: Unlicense\n"
        "# TODO(v2): fetch full text from "
        "https://unlicense.org/\n"
    ),
}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class PlaceholderSpec(NamedTuple):
    key: str
    required: bool
    validate: str | None
    description: str


class Manifest(NamedTuple):
    placeholders: dict[str, PlaceholderSpec]
    directory_renames: list[dict[str, str]]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_manifest(manifest_path: Path) -> Manifest:
    """Parse template.manifest.json and return a Manifest."""
    with manifest_path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    placeholders: dict[str, PlaceholderSpec] = {}
    for key, spec in raw["placeholders"].items():
        placeholders[key] = PlaceholderSpec(
            key=key,
            required=spec["required"],
            validate=spec.get("validate"),
            description=spec.get("description", ""),
        )

    return Manifest(
        placeholders=placeholders,
        directory_renames=raw.get("directory_renames", []),
    )


def load_values(values_path: Path) -> dict[str, str]:
    """Load substitution values from a JSON file."""
    with values_path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        print(f"ERROR: {values_path} must contain a JSON object.", file=sys.stderr)
        sys.exit(2)
    return {str(k): str(v) for k, v in data.items()}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_values(manifest: Manifest, values: dict[str, str]) -> None:
    """Validate that all required placeholders are present and match their regex.

    Prints all errors before exiting so the user can fix in one pass.
    Exits with code 2 on failure.
    """
    errors: list[str] = []

    for key, spec in manifest.placeholders.items():
        if spec.required and key not in values:
            errors.append(f"  Missing required placeholder: {key} — {spec.description}")
            continue

        value = values.get(key)
        if value is None:
            continue

        if spec.validate is not None:
            if not re.fullmatch(spec.validate, value):
                errors.append(
                    f"  Validation failed for {key}: value {value!r} "
                    f"does not match /{spec.validate}/ — {spec.description}"
                )

    if errors:
        print("Validation errors:", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def is_binary_file(path: Path) -> bool:
    """Heuristic: read first 8 KB; if a null byte is present, treat as binary."""
    try:
        chunk = path.read_bytes()[:8192]
        return b"\x00" in chunk
    except OSError:
        return True


def scan_tree(target: Path, registered_keys: set[str]) -> dict[Path, list[tuple[str, int]]]:
    """Walk target, find files containing registered placeholders.

    Also checks for orphan placeholders (present in file but not in registry).
    Exits with code 3 if any orphan is found.

    Returns:
        Mapping from file path to list of (placeholder, occurrence_count).
    """
    hit_map: dict[Path, list[tuple[str, int]]] = {}
    orphans: list[str] = []

    for file_path in sorted(target.rglob("*")):
        if not file_path.is_file():
            continue
        if is_binary_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        found = PLACEHOLDER_RE.findall(content)
        if not found:
            continue

        # Check for orphans
        for ph in set(found):
            if ph not in registered_keys:
                orphans.append(f"  {file_path}: unknown placeholder {ph}")

        # Build hit list for registered placeholders
        registered_hits = [
            (ph, found.count(ph))
            for ph in sorted(set(found))
            if ph in registered_keys
        ]
        if registered_hits:
            hit_map[file_path] = registered_hits

    if orphans:
        print("Orphan placeholder(s) found — aborting:", file=sys.stderr)
        for msg in orphans:
            print(msg, file=sys.stderr)
        sys.exit(3)

    return hit_map


# ---------------------------------------------------------------------------
# Substitution
# ---------------------------------------------------------------------------

def apply_substitutions(
    hit_map: dict[Path, list[tuple[str, int]]],
    values: dict[str, str],
) -> list[Path]:
    """Atomically replace all registered placeholders in each affected file.

    Uses a temp-file-then-rename strategy so partial writes never corrupt the
    original.  Returns a list of tmp paths created (for rollback if needed).

    Exits with code 4 on I/O failure after rolling back all tmp files.
    """
    tmp_paths: list[Path] = []

    try:
        for file_path, hits in hit_map.items():
            content = file_path.read_text(encoding="utf-8")

            for placeholder, _ in hits:
                replacement = values[placeholder]
                content = content.replace(placeholder, replacement)

            tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
            tmp_paths.append(tmp_path)
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(file_path)
            tmp_paths.remove(tmp_path)  # committed — no longer needs rollback

    except OSError as exc:
        print(f"File write failure: {exc}", file=sys.stderr)
        print("Rolling back tmp files…", file=sys.stderr)
        for tmp in tmp_paths:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
        sys.exit(4)

    return []


# ---------------------------------------------------------------------------
# Directory renames
# ---------------------------------------------------------------------------

def apply_directory_renames(target: Path, manifest: Manifest, values: dict[str, str]) -> None:
    """Rename placeholder directories as specified in directory_renames."""
    for entry in manifest.directory_renames:
        from_rel = entry["from"]
        placeholder = entry["placeholder"]
        actual_name = values.get(placeholder, "")

        # Substitute the placeholder within the path segment
        actual_rel = from_rel.replace(placeholder, actual_name)

        from_path = target / from_rel
        to_path = target / actual_rel

        if from_path.exists() and from_path != to_path:
            from_path.rename(to_path)
            print(f"  Renamed {from_rel} → {actual_rel}")
        elif not from_path.exists() and to_path.exists():
            print(f"  Directory {actual_rel} already in place (skipped rename).")
        elif not from_path.exists():
            # Companion agent may have pre-named the directory — not fatal.
            print(f"  Note: {from_rel} not found in target (may already be renamed).")


# ---------------------------------------------------------------------------
# License override
# ---------------------------------------------------------------------------

def apply_license_override(target: Path, values: dict[str, str]) -> None:
    """Replace LICENSE file content for non-MIT SPDX IDs.

    MIT: leave the file produced by substitution as-is.
    Others: write a stub with a TODO to fetch the full SPDX text (v2 feature).
    """
    license_id = values.get("<<LICENSE_ID>>", "MIT")
    if license_id == "MIT":
        return

    license_path = target / "LICENSE"
    stub = LICENSE_STUBS.get(license_id)
    if stub is None:
        print(f"  Warning: no license stub for {license_id}; LICENSE file unchanged.")
        return

    try:
        license_path.write_text(stub, encoding="utf-8")
        print(f"  LICENSE updated with stub for {license_id} (v2 will fetch full SPDX text).")
    except OSError as exc:
        print(f"  Warning: could not write LICENSE: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Post-substitution check
# ---------------------------------------------------------------------------

def final_check(target: Path) -> None:
    """Re-scan the target tree; abort if any <<...>> patterns remain.

    Exits with code 5 if stray placeholders are found.
    """
    remaining: list[str] = []

    for file_path in sorted(target.rglob("*")):
        if not file_path.is_file():
            continue
        if is_binary_file(file_path):
            continue
        # Skip venv and generated caches
        parts = set(file_path.parts)
        if parts & {".venv", ".git", "__pycache__", ".pytest_cache"}:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        found = PLACEHOLDER_RE.findall(content)
        for ph in set(found):
            remaining.append(f"  {file_path}: {ph}")

    if remaining:
        print("Post-substitution orphan(s) found:", file=sys.stderr)
        for msg in remaining:
            print(msg, file=sys.stderr)
        sys.exit(5)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply placeholder substitutions to a scaffolded project tree.",
    )
    parser.add_argument(
        "--target",
        required=True,
        type=Path,
        help="Path to the new project directory.",
    )
    parser.add_argument(
        "--values",
        required=True,
        type=Path,
        help="Path to a JSON file mapping placeholders to their values.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target: Path = args.target.resolve()
    values_path: Path = args.values.resolve()

    if not target.is_dir():
        print(f"ERROR: target directory does not exist: {target}", file=sys.stderr)
        sys.exit(2)

    if not values_path.is_file():
        print(f"ERROR: values file does not exist: {values_path}", file=sys.stderr)
        sys.exit(2)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(2)

    print(f"Loading manifest from {MANIFEST_PATH}")
    manifest = load_manifest(MANIFEST_PATH)

    print(f"Loading values from {values_path}")
    values = load_values(values_path)

    # Auto-derive <<RUFF_TARGET>> from <<PYTHON_FLOOR>> if not supplied.
    # Example: "3.11" -> "py311", "3.12" -> "py312".
    if "<<RUFF_TARGET>>" not in values and "<<PYTHON_FLOOR>>" in values:
        floor = values["<<PYTHON_FLOOR>>"]
        major, minor = floor.split(".")
        values["<<RUFF_TARGET>>"] = f"py{major}{minor}"
        print(f"  Auto-derived <<RUFF_TARGET>> = {values['<<RUFF_TARGET>>']!r} from <<PYTHON_FLOOR>>={floor!r}")

    print("Validating values…")
    validate_values(manifest, values)

    print(f"Scanning {target} for placeholders…")
    hit_map = scan_tree(target, set(manifest.placeholders.keys()))
    total_files = len(hit_map)
    print(f"  Found {total_files} file(s) with registered placeholders.")

    if total_files:
        print("Applying substitutions…")
        apply_substitutions(hit_map, values)

    print("Applying directory renames…")
    apply_directory_renames(target, manifest, values)

    print("Applying license override (if needed)…")
    apply_license_override(target, values)

    print("Running final check for stray placeholders…")
    final_check(target)

    print("Substitution complete.")


if __name__ == "__main__":
    main()
