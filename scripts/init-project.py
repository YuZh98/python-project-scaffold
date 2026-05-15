"""Interactive bootstrap CLI for python-project-scaffold.

Two modes:

- ``--in-place`` (default if no flag) — operates on the CURRENT directory.
  Use after ``git clone`` of the scaffold repo OR after GitHub's "Use this
  template" button created a new repo from this one. Substitutes placeholders
  in ``./template/``, atomically swaps the substituted tree to the repo root,
  removes scaffold-only files, optionally resets git history, makes the first
  commit.

- ``--target <dir>`` — copies ``./template/`` into ``<dir>``, substitutes
  there, leaves source untouched. Equivalent to ``scripts/scaffold.sh
  <target> <values.json>``.

Both modes support ``--values <path>`` for non-interactive use.

Linux / macOS only. Windows users: WSL or a Mac.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# Allow `import substitute` from same scripts/ dir.
sys.path.insert(0, str(Path(__file__).parent))
import substitute  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent.resolve()

# Files to remove during in-place mode (paths relative to repo root).
# Order matters for the .github/workflows/ci.yml swap.
SCAFFOLD_ONLY_FILES: list[str] = [
    "scripts/scaffold.sh",
    "scripts/substitute.py",
    "scripts/refresh_dev_deps.py",
    "scripts/init-project.py",  # self-delete LAST
    "template.manifest.json",
    "tests/test_scaffold.py",
    "tests/test_skill_flow.py",
    "tests/test_init_project.py",  # if present
    "tests/test_refresh_dev_deps.py",  # if present
    "README.md",  # scaffold-repo README, NOT template
    "CHANGELOG.md",  # scaffold-repo CHANGELOG, NOT template
    ".github/workflows/ci.yml",  # scaffold-repo CI; template's takes its place
]

# Scaffold-only directories to remove (after files cleared).
SCAFFOLD_ONLY_DIRS: list[str] = [
    "examples",  # if it exists at scaffold-repo level (added in same PR)
    "tooling",  # opt-in editor / AI integrations layer; not for derived projects
    "docs/superpowers",  # scaffold-internal dev docs (test plans, specs); not for derived projects
    "template",  # always last — entire template/ subdir after move
    "scripts",  # cleared after self-delete
]

# License hints for prompt UX.
LICENSE_HINTS = {
    "MIT": "simplest, most permissive; choose this if unsure",
    "Apache-2.0": "permissive with explicit patent grant; preferred by larger orgs",
    "BSD-3-Clause": "similar to MIT with attribution requirement",
    "Unlicense": "public domain dedication; no attribution required",
}


def _abort(msg: str, code: int = 1) -> None:
    print(f"✗ {msg}", file=sys.stderr)
    sys.exit(code)


def _platform_guard() -> None:
    if sys.platform.startswith("win"):
        _abort("Windows is not supported. Use WSL2 or a Linux/macOS host.", 2)


def _live_source_guard() -> None:
    """In-place mode runs ONCE per scaffold checkout. Refuse if already run."""
    if not (REPO_ROOT / "template").exists():
        _abort(
            "No `template/` directory found. This script can only run once "
            "on a fresh scaffold checkout. If you intended to scaffold into "
            "a different directory, use `--target <dir>` instead.",
            3,
        )


# ---------------------------------------------------------------------------
# Prompt collection
# ---------------------------------------------------------------------------


def _prompt(text: str, default: str | None = None, validator=None) -> str:
    """Prompt the user with optional default and validator.

    `validator` is a callable taking the string and returning either the
    accepted value (possibly transformed) or raising ValueError with a
    human-readable message.
    """
    while True:
        suffix = f" [{default}]" if default is not None else ""
        try:
            raw = input(f"  {text}{suffix}: ").strip()
        except EOFError:
            _abort(
                "Interactive mode requires a TTY for stdin. "
                "Use --values <path.json> for non-interactive bootstrap.",
                4,
            )
        if not raw and default is not None:
            raw = default
        if not raw:
            print("    ✗ Value cannot be empty.")
            continue
        if validator is None:
            return raw
        try:
            return validator(raw)
        except ValueError as e:
            print(f"    ✗ {e}")


def _validate_project_name(value: str) -> str:
    import re

    if not re.fullmatch(r"[a-z][a-z0-9-]*[a-z0-9]", value):
        raise ValueError(
            f"Project name must be lowercase letters / digits / hyphens, "
            f"start and end with a letter or digit. Got: '{value}'. "
            f"Try: my-cool-tool"
        )
    return value


def _validate_description(value: str) -> str:
    if any(c in value for c in '"\\'):
        raise ValueError(
            "Description cannot contain double-quote or backslash "
            "(substituted into TOML strings). Try plain prose."
        )
    return value


def _validate_python_floor(value: str) -> str:
    import re

    if not re.fullmatch(r"3\.(1[1-9]|[2-9][0-9])", value):
        raise ValueError(f"Python floor must be 3.11 or later (e.g. 3.11, 3.12). Got: '{value}'")
    return value


def _validate_license(value: str) -> str:
    if value not in LICENSE_HINTS:
        opts = " / ".join(LICENSE_HINTS.keys())
        raise ValueError(f"Unknown license. Pick one of: {opts}")
    return value


def _collect_interactive() -> dict[str, str]:
    print("\nProject details — press Enter to accept defaults in [brackets].\n")
    name = _prompt("Project name (kebab-case)", validator=_validate_project_name)
    description = _prompt("One-line description", validator=_validate_description)
    python_floor = _prompt("Python floor (3.11+)", default="3.11", validator=_validate_python_floor)

    print("\n  License options:")
    for k, hint in LICENSE_HINTS.items():
        print(f"    - {k} ({hint})")
    license_id = _prompt("License", default="MIT", validator=_validate_license)

    return {
        "<<PROJECT_NAME>>": name,
        "<<DESCRIPTION>>": description,
        "<<PYTHON_FLOOR>>": python_floor,
        "<<LICENSE_ID>>": license_id,
    }


def _git_config(key: str) -> str | None:
    try:
        out = subprocess.check_output(["git", "config", "--get", key], stderr=subprocess.DEVNULL)
        return out.decode().strip() or None
    except subprocess.CalledProcessError:
        return None


def _gh_login() -> str | None:
    try:
        out = subprocess.check_output(
            ["gh", "api", "user", "--jq", ".login"], stderr=subprocess.DEVNULL
        )
        return out.decode().strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _derive_silent(values: dict[str, str]) -> dict[str, str]:
    """Add silent defaults for placeholders not collected interactively."""
    name = values["<<PROJECT_NAME>>"]
    values.setdefault("<<PACKAGE_NAME>>", name.replace("-", "_"))
    values.setdefault("<<PROJECT_TITLE>>", " ".join(w.capitalize() for w in name.split("-")))
    values.setdefault("<<YEAR>>", str(date.today().year))
    if "<<AUTHOR_NAME>>" not in values:
        author = _git_config("user.name")
        if not author:
            author = _prompt("Author name (from git config; required)")
        values["<<AUTHOR_NAME>>"] = author
        print(
            f"  ℹ <<AUTHOR_NAME>> not supplied — resolved as {author!r} (from git config / prompt)"
        )
    if "<<AUTHOR_EMAIL>>" not in values:
        email = _git_config("user.email")
        if not email:
            email = _prompt("Author email (from git config; required)")
        values["<<AUTHOR_EMAIL>>"] = email
        print(
            f"  ℹ <<AUTHOR_EMAIL>> not supplied — resolved as {email!r} (from git config / prompt)"
        )
    if "<<GITHUB_USERNAME>>" not in values:
        gh = _gh_login()
        if not gh:
            print("    ℹ `gh` not configured. You'll need a GitHub login for project URLs.")
            gh = _prompt("GitHub username")
        values["<<GITHUB_USERNAME>>"] = gh
        print(f"  ℹ <<GITHUB_USERNAME>> not supplied — resolved as {gh!r} (from gh api / prompt)")
    return values


def _confirm(values: dict[str, str], reset_history: bool, no_install: bool) -> None:
    print("\n" + "─" * 60)
    print("Summary — please review:\n")
    for k in sorted(values):
        print(f"  {k:<22} {values[k]}")
    print(
        f"\n  Git history          "
        f"{'will be RESET (clean slate)' if reset_history else 'will be preserved'}"
    )
    print(
        f"  make install         "
        f"{'will run automatically' if not no_install else 'will be skipped'}"
    )
    print("─" * 60 + "\n")


def _gate(skip: bool) -> None:
    if skip:
        return
    try:
        confirm = input("Proceed with these settings? [Y/n] ").strip().lower()
    except EOFError:
        _abort(
            "Confirmation prompt requires a TTY for stdin. "
            "Use --yes to skip the confirmation, or --values <path.json> for fully non-interactive.",
            4,
        )
    if confirm and confirm not in {"y", "yes"}:
        _abort("Aborted by user.", 0)


# ---------------------------------------------------------------------------
# Staging + atomic swap
# ---------------------------------------------------------------------------


def _stage(values: dict[str, str], dry_run: bool) -> Path:
    """Copy `template/` to a tmpdir and substitute placeholders there."""
    template_src = REPO_ROOT / "template"
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=str(REPO_ROOT)))
    if dry_run:
        print(f"  [DRY-RUN] would stage to {staging.relative_to(REPO_ROOT)}")
        shutil.rmtree(staging, ignore_errors=True)
        return staging
    # Copy template content (NOT the directory itself) into staging root
    for item in template_src.iterdir():
        dest = staging / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    print(f"  ✓ Staged template → {staging.relative_to(REPO_ROOT)}/")

    # Run substitute.py against the staged tree.
    manifest = substitute.load_manifest(REPO_ROOT / "template.manifest.json")

    # Auto-derive RUFF_TARGET (matches substitute.py main() logic)
    if "<<RUFF_TARGET>>" not in values and "<<PYTHON_FLOOR>>" in values:
        floor = values["<<PYTHON_FLOOR>>"]
        major, minor = floor.split(".")
        values["<<RUFF_TARGET>>"] = f"py{major}{minor}"

    substitute.validate_values(manifest, values)
    hit_map = substitute.scan_tree(staging, set(manifest.placeholders.keys()))
    if hit_map:
        substitute.apply_substitutions(hit_map, values)
    substitute.apply_directory_renames(staging, manifest, values)
    substitute.apply_license_override(staging, values)
    substitute.final_check(staging)
    print("  ✓ Substituted placeholders in staged tree")
    return staging


def _refresh_dev_deps(target_file: Path, dry_run: bool) -> None:
    """Refresh dev-dep lower bounds to current upstream minors at bootstrap time.

    Best-effort: network failures or unparseable lines leave the file unchanged
    and emit a warning. Bootstrap continues regardless — a stale floor is a UX
    nit, not a correctness defect, and the routine `chore` Dependabot PR would
    eventually catch it.
    """
    if dry_run:
        print(f"  [DRY-RUN] would refresh dev-dep floors in {target_file}")
        return
    if not target_file.is_file():
        return
    script = REPO_ROOT / "scripts" / "refresh_dev_deps.py"
    if not script.is_file():
        print("  ⚠ refresh_dev_deps.py missing; skipping floor refresh")
        return
    try:
        result = subprocess.run(
            ["python3", str(script), str(target_file)],
            check=False,
            timeout=60,
        )
        if result.returncode == 0:
            print("  ✓ Dev-dep floors refreshed (best-effort)")
        else:
            print(f"  ⚠ refresh_dev_deps.py exited {result.returncode}; floors left as-is")
    except subprocess.TimeoutExpired:
        print("  ⚠ Dev-dep floor refresh timed out; floors left as-is")


def _atomic_swap(staging: Path, dry_run: bool) -> None:
    """Replace scaffold-only files at root with the staged tree.

    Uses in-memory backup of any scaffold-only file so on rollback we can
    restore the pre-swap state.
    """
    if dry_run:
        print("  [DRY-RUN] would atomic-swap staged → repo root")
        return

    # Phase 1: snapshot scaffold-only file contents for rollback.
    backups: dict[Path, bytes] = {}
    for rel in SCAFFOLD_ONLY_FILES:
        path = REPO_ROOT / rel
        if path.is_file():
            backups[path] = path.read_bytes()

    # Phase 2: delete scaffold-only files at root.
    try:
        for rel in SCAFFOLD_ONLY_FILES:
            path = REPO_ROOT / rel
            if path.is_file():
                path.unlink()

        # Phase 3: move every item from staging up to repo root.
        # Handle collisions: dirs merged, files overwritten.
        for item in list(staging.iterdir()):
            dest = REPO_ROOT / item.name
            if item.is_dir() and dest.exists() and dest.is_dir():
                # Merge directory by moving each child individually.
                for child in list(item.iterdir()):
                    child_dest = dest / child.name
                    if child_dest.exists():
                        if child_dest.is_dir():
                            shutil.rmtree(child_dest)
                        else:
                            child_dest.unlink()
                    shutil.move(str(child), str(child_dest))
                item.rmdir()
            else:
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dest))

        # Phase 4: remove scaffold-only directories that remain.
        for rel in SCAFFOLD_ONLY_DIRS:
            path = REPO_ROOT / rel
            if path.is_dir():
                shutil.rmtree(path)

    except Exception as exc:
        # Rollback: restore deleted scaffold files.
        for path, contents in backups.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        _abort(
            f"Atomic swap failed: {exc}. Scaffold files restored from backup. "
            f"The staged tree remains at {staging.relative_to(REPO_ROOT)} for inspection.",
            10,
        )

    # Clean up staging dir (it should be empty / nearly empty now).
    shutil.rmtree(staging, ignore_errors=True)
    print("  ✓ Atomic swap complete")


def _git_env(values: dict[str, str]) -> dict[str, str]:
    """Author + committer env so `git commit` works without global git config.

    Real users almost always have `git config --global user.name`/`user.email`
    set; CI runners + ephemeral containers do not. Forwarding the values dict's
    author fields makes both paths robust without mutating global state.
    """
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": values["<<AUTHOR_NAME>>"],
            "GIT_AUTHOR_EMAIL": values["<<AUTHOR_EMAIL>>"],
            "GIT_COMMITTER_NAME": values["<<AUTHOR_NAME>>"],
            "GIT_COMMITTER_EMAIL": values["<<AUTHOR_EMAIL>>"],
        }
    )
    return env


def _reset_git_history(values: dict[str, str], dry_run: bool) -> None:
    if dry_run:
        print("  [DRY-RUN] would reset git history (rm -rf .git && git init && commit)")
        return
    git_dir = REPO_ROOT / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
    env = _git_env(values)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(["git", "add", "."], cwd=REPO_ROOT, check=True, env=env)
    msg = "feat: initial scaffold from python-project-scaffold (manifest v1)"
    subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        env=env,
    )
    print("  ✓ Git history reset; first commit created")


def _commit_only(values: dict[str, str], dry_run: bool) -> None:
    if dry_run:
        print("  [DRY-RUN] would `git add . && git commit -m 'feat: ...'`")
        return
    env = _git_env(values)
    subprocess.run(["git", "add", "."], cwd=REPO_ROOT, check=True, env=env)
    subprocess.run(
        ["git", "commit", "-m", "feat: bootstrap from python-project-scaffold"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        env=env,
    )
    print("  ✓ Bootstrap commit created on top of existing history")


def _install(dry_run: bool) -> None:
    if dry_run:
        print("  [DRY-RUN] would run `make install`")
        return
    print("\nRunning `make install`…")
    subprocess.run(["make", "install"], cwd=REPO_ROOT, check=False)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def _mode_in_place(args: argparse.Namespace) -> None:
    _platform_guard()
    _live_source_guard()

    # Phase preamble.
    print("\nPython Project Scaffold — interactive bootstrap")
    print("─" * 60)
    print("Phases:")
    print("  [1] Collect project details")
    print("  [2] Derive silent defaults")
    print("  [3] Confirm")
    print("  [4] Stage substituted tree to a tmpdir (live repo untouched)")
    print("  [5] Verify no stray placeholders")
    print("  [5.5] Refresh dev-dep floors to current upstream minors (best-effort)")
    print("  [6] Atomic swap (with rollback on failure)")
    print("  [7] Reset git history" + (" (skipped)" if args.keep_history else ""))
    print("  [8] Run `make install`" + (" (skipped)" if args.no_install else ""))
    print("─" * 60)

    # [1] [2]
    if args.values:
        values = json.loads(Path(args.values).read_text())
    else:
        values = _collect_interactive()
    values = _derive_silent(values)

    # [3]
    reset_history = not args.keep_history
    _confirm(values, reset_history, args.no_install)
    _gate(args.yes or args.dry_run)

    # [4] [5]
    staging = _stage(values, args.dry_run)

    # Refresh dev-dep floors on the staged file before the swap. The script
    # lives at REPO_ROOT/scripts/ during this phase; after _atomic_swap it
    # gets cleared as part of SCAFFOLD_ONLY_DIRS, so this has to happen now.
    _refresh_dev_deps(staging / "requirements-dev.txt", args.dry_run)

    # [6]
    _atomic_swap(staging, args.dry_run)

    # [7]
    if reset_history:
        _reset_git_history(values, args.dry_run)
    else:
        _commit_only(values, args.dry_run)

    # [8]
    if not args.no_install:
        _install(args.dry_run)

    print("\n" + "─" * 60)
    print("✓ Bootstrap complete." + ("  [DRY-RUN — no changes written]" if args.dry_run else ""))
    print(f"  Project: {values['<<PROJECT_NAME>>']}")
    print("  Next:    make test")
    print("─" * 60 + "\n")


def _mode_target(args: argparse.Namespace) -> None:
    """Delegate to existing scaffold.sh for target-dir mode."""
    tmp_dir_to_clean: Path | None = None
    if not args.values:
        # In target mode we still need values; collect interactively then write JSON.
        values = _collect_interactive()
        values = _derive_silent(values)
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_dir_to_clean = tmp_dir
        tmp_values = tmp_dir / "values.json"
        tmp_values.write_text(json.dumps(values))
        args.values = str(tmp_values)
    try:
        target = Path(args.target).resolve()
        if args.dry_run:
            import json as _json
            with open(args.values) as _f:
                _vals = _json.load(_f)
            print("[DRY-RUN] --target mode: would bootstrap project at", target)
            print("[DRY-RUN] Values that would be substituted:")
            for _k, _v in _vals.items():
                print(f"  {_k}: {_v}")
            print("[DRY-RUN] No files written, no git history created.")
            return
        if target.exists() and any(target.iterdir()):
            _abort(f"Target {target} exists and is non-empty.", 3)
        target.mkdir(parents=True, exist_ok=True)
        cmd = ["bash", str(REPO_ROOT / "scripts" / "scaffold.sh"), str(target), args.values]
        result = subprocess.run(cmd)
        if result.returncode == 0:
            # scaffold.sh uses substitute.py and doesn't go through _mode_in_place;
            # apply the same dev-dep floor refresh on the target's requirements-dev.txt.
            _refresh_dev_deps(target / "requirements-dev.txt", dry_run=False)
        sys.exit(result.returncode)
    finally:
        if tmp_dir_to_clean is not None:
            shutil.rmtree(tmp_dir_to_clean, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", help="Target directory (instead of in-place)")
    parser.add_argument("--values", help="Non-interactive values.json path")
    parser.add_argument("--dry-run", action="store_true", help="Print phases, no writes")
    parser.add_argument("--keep-history", action="store_true", help="Don't reset .git/")
    parser.add_argument(
        "--reset-history",
        action="store_true",
        help="Explicit reset (default in interactive in-place mode)",
    )
    parser.add_argument("--no-install", action="store_true", help="Skip `make install`")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    # Non-interactive default: keep history if not explicitly reset.
    if args.values and not args.reset_history:
        args.keep_history = True

    if args.target:
        _mode_target(args)
    else:
        _mode_in_place(args)


if __name__ == "__main__":
    main()
