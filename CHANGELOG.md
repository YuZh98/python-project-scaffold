# Changelog

Scaffold-repo evolution. The template's own CHANGELOG (`template/CHANGELOG.md`) is what new projects inherit; this file is for the scaffold itself.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · SemVer.

## [Unreleased]

## [v1.8.2] - 2026-05-15

Major version bumps in scaffolded repos arrive as individual Dependabot PRs again, not bundled with the weekly minor/patch roll-up.

### Fixed
- Template Dependabot groups now only roll up minor and patch updates; major bumps get individual PRs. (9f518aa)

## [v1.8.1] - 2026-05-15

Fixes the day-one bootstrap UX: scaffolded repos now install themselves via `pip install -e .` in CI and `make install` so pytest collection succeeds on first push, and Dependabot bumps are grouped per ecosystem with a `chore:` commit prefix to cut PR noise.

### Added
- Pinning test asserting the template's CI workflow and Makefile install the scaffolded package via `pip install -e .`, matching the editable-install requirement in ADR-0000 D1. (ba6b761)

### Changed
- Plugin-smoke CI step that normalize-checks the plugin CHANGELOG loosened from gating to informational, pending normalizer support for summary paragraphs and HTML comment blocks. (fff284e)

### Fixed
- Scaffolded projects now install the package via `pip install -e .` in CI and `make install`, fixing the `ModuleNotFoundError` that turned every freshly scaffolded repo's first push red — Dependabot PRs included. (ba6b761)
- Dependabot bumps now group per ecosystem and ship with a `chore:` commit prefix, cutting day-one PR noise on a fresh repo from ~7 individual PRs to ~2 grouped ones that pass the Conventional Commits hook. (aeff17e)

<!--
Keep-a-Changelog conventions:
  - Recommended (not enforced): lead each versioned section with a one-sentence
    summary of what the release is about, before any ### subsections. Helps
    readers scan the changelog top-down.
  - Group related changes into one bullet at the level of user impact — what
    changed and why it matters. Skip file paths, step numbers, and implementation
    details. Voice (imperative or descriptive) is your choice.
    Poor: "Step 5: replaced cd with git -C in the license-amend block."
    Good: "Fixed license rewrite silently failing when shell cwd doesn't persist."
  - Six legal section headings, in this order (Keep-a-Changelog 1.1.0 spec) — omit empty ones before releasing:
    Added · Changed · Deprecated · Removed · Fixed · Security.
  - Add the PR number or commit hash at the end of each entry.
  - On release: rotate this block to ## [vX.Y.Z] - YYYY-MM-DD, then re-add empty [Unreleased] above.
-->

## [v1.8.0] - 2026-05-15

Scaffold now ships as a Claude Code plugin bundling the new-project skill alongside release-helper, changelog-normalizer, and audit-runner. Template-side defaults also relax: coverage threshold drops from 95% to 80%, and the imperative-mood, ADR-for-decisions, and summary-paragraph rules are demoted from required to recommended.

### Added
- Claude Code plugin (`plugins/new-project/`) bundling the new-project skill alongside release-helper, changelog-normalizer, and audit-runner; distributed via a self-hosted marketplace. (64e6db5)

### Changed
- Template default coverage threshold lowered from 95% to 80% — conservative starting point with a comment suggesting projects raise it as they stabilize. (#22)
- Summary-paragraph-before-bullets rule in template CHANGELOG sections demoted from pinning test to recommendation in the comment block. (#22)
- Imperative-mood requirement on commit messages and changelog entries dropped as taste-pinning. (#22)
- Conventional Commits prefix list demoted from "must use these types" to "common examples". (#22)
- ADR-for-hard-to-reverse-decisions wording softened from "required" to "strongly recommended" across template docs. (#22)

### Security
- Internal-process docs (`docs/superpowers/`, `docs/dev-notes/`, session logs) added to `.gitignore` for both scaffold and template, closing a CLAUDE.md §8 violation that v0.1.0 inadvertently shipped. (#21)

## [v1.7.9] - 2026-05-14

Every project bootstrapped from this scaffold now enforces the changelog summary-sentence convention at CI level. Also fixes a long-standing bug where the scaffold's own developer docs were silently copied into bootstrapped projects.

### Added
- `template/tests/test_cohesion.py`: each `## [vX.Y.Z]` section must have a summary paragraph before its first `###` subsection — fails CI with a named violation if omitted. (#20)
- Template `CHANGELOG.md` comment block updated with poor/good bullet examples to make the expected style concrete. (#20)

### Fixed
- In-place bootstrap left `docs/superpowers/` (scaffold-internal test plans) inside the derived project; now removed alongside `tooling/` and `scripts/`. (3ada781)

## [v1.7.8] - 2026-05-14

Better experience for first-time users. The skill now shows concrete examples of what each step looks like, explains what `make test` does and why, and warns that Dependabot PRs on a new repo are expected — not failures. Pre-flight now catches a missing `make` before anything runs.

### Added
- Pre-flight check for `make`; missing installation now surfaces with an OS-specific hint before any work begins. (bcd58c4)
- Four examples in the skill showing what the flow actually looks like: name re-prompt, license re-prompt, filled-in pre-clone summary, and completion output. (bcd58c4)

### Changed
- Completion message expanded: explains what `make test` runs, notes Dependabot PRs are expected, and links `docs/concepts.md` for users new to the scaffold. (bcd58c4)
- Visibility and license questions both now have defined re-prompt messages on invalid input. (bcd58c4)
- Python floor labelled as a fixed default in the summary so users know it cannot be changed interactively. (bcd58c4)

## [v1.7.7] - 2026-05-14

Correctness fixes found by independent multi-agent audit. The most impactful: non-MIT license files were being generated with incorrect text (a condensed paraphrase of Apache-2.0 instead of the full SPDX text), and several shell-level guards that the skill described in prose weren't actually enforced.

### Fixed
- Apache-2.0 license text was a condensed paraphrase; replaced with the full canonical SPDX verbatim. (#18)
- Non-MIT license rewrite used `cd` to change directories, which doesn't persist across tool calls; now uses `git -C` to operate without changing cwd. (#18)
- Dry-run relied on Claude reading instructions to skip GitHub steps; now an explicit shell gate exits before any network operation. (#18)
- Bootstrapping into an existing directory produced undefined behaviour; skill now aborts with a clear message if the target path already exists. (#18)
- License script was sourced from a hardcoded install path, breaking for users who copied only SKILL.md; now tries the bundled path first and falls back to the cloned scaffold. (#18)

## [v1.7.6] - 2026-05-13

The skill can now be installed with a single command. CI automatically builds a `.skill` zip file and attaches it to every GitHub Release on tag push — no manual packaging step needed.

### Added
- CI workflow that builds and uploads `new-project.skill` to GitHub Releases on every version tag. (#15)

### Changed
- README install instructions updated to use `gh release download --latest`. (#15)

## [v1.7.5] - 2026-05-13

Skill cut from 452 to 212 lines. License texts moved to a bundled helper script that loads only when needed; several redundant sections removed.

### Changed
- Skill condensed 53%; license texts extracted to `scripts/write_license.py`. (#14)

## [v1.7.4] - 2026-05-13

Added license selection to the setup flow. New repos now default to private. Non-MIT licenses are written into the project with the correct full SPDX text from the start.

### Added
- License question in setup flow: MIT (default), Apache-2.0, BSD-3-Clause, or Unlicense. Non-MIT choices rewrite `LICENSE` and amend the first commit. (#13)

### Changed
- Visibility default changed from `public` to `private`. (#13)

## [v1.7.3] - 2026-05-13

Skill triggering improved. Claude now recognises natural variants like "create a new Python project" or "spin up a repo" without requiring the exact `/new-project` invocation.

### Changed
- Skill description rewritten with broader trigger phrases and clearer skip conditions. (#12)

## [v1.7.2] - 2026-05-13

Fixed three silent failures found during the first real-world use of the skill. Dry-run wrote files instead of previewing. Push failures left the user stranded. Pre-flight silently accepted empty git identity.

### Fixed
- `--dry-run` flag was silently ignored when bootstrapping to a target directory; it now prints a preview and exits without touching disk. (#11)
- Push failure after successful repo creation now prints copy-paste recovery commands. (#11)
- Pre-flight accepted empty `user.name` / `user.email` values; now verifies they are non-empty. (#11)
- Temp directory was leaked on early exit; cleaned up via trap on all exit paths. (#11)

## [v1.7.1] - 2026-05-13

Fixed three bugs found in the first live bootstrap (`lobster-imbalance`). All three were silent: ruff failed at first commit, SSH keys weren't set up so push failed, and bootstrap failure left no recovery path.

### Fixed
- `__init__.py` docstring overflowed ruff's line-length limit with realistic project descriptions. (#10)
- GitHub push defaulted to SSH and failed for users without SSH keys; now always pushes via HTTPS. (#10)
- Bootstrap failure left no instructions; skill now prints a recovery path. (#10)

## [v1.7.0] - 2026-05-13

Eliminated the double-prompt bug where the skill asked for project details and then `init-project.py` asked for them again. Added Conventional Commits enforcement and OSS hygiene files to the template.

### Fixed
- Skill now passes all values via `--values` in one shot; `init-project.py` no longer re-prompts. (#9)

### Added
- Conventional Commits hook on commit-msg stage in template. (#9)
- `SECURITY.md`, `CONTRIBUTING.md`, and PR template added to scaffold repo for OSS hygiene. (#9)

## [v1.6.0] - 2026-05-12

Skill moved into the scaffold repo and versioned alongside the engine. Previously distributed as a standalone file with no connection to a specific scaffold release.

### Added
- `tooling/claude-code/` directory with the skill as the canonical in-repo copy; users install by copying from a tagged release. (#8)

### Removed
- `tests/test_skill_flow.py` — obsolete test that parsed a key list that no longer exists in the skill after v1.4.0. (#8)

## [v1.5.0] - 2026-05-12

Added branch protection guidance, SQL injection enforcement, and Conventional Commits pre-commit hook to the template.

### Added
- `docs/setup-branch-protection.md` in template: how-to for enabling branch protection via CLI and UI. (#7)
- AST scan that catches string-concatenated SQL in `execute()` calls — promotes parameterised-SQL rule to a failing test. (#7)

### Changed
- Conventional Commits + 72-char subject now enforced by pre-commit hook, not just prose. (#7)

### Fixed
- README URLs in the template used the author's display name instead of GitHub username, producing 404s. (#7)

## [v1.4.0] - 2026-05-12

New Python bootstrap CLI replaces the shell-only approach. Supports atomic swap (stage to tmpdir, then rename), rollback on failure, and bootstrapping to a separate target directory without touching the scaffold checkout.

### Added
- `scripts/init-project.py`: interactive bootstrap with `--in-place` and `--target` modes, `--dry-run`, `--values`, `--keep-history`. (#6)
- Smoke test for `--in-place` mode. (#6)

## [v1.3.0] - 2026-05-12

Added learning docs and a deletable hello-world module so new projects start green at 100% coverage with something to read.

### Added
- `docs/concepts.md`: glossary for venv, src layout, type hints, ruff, pyright, pytest, and more. (#5)
- `docs/enforcement-model.md`: four-tier rule hierarchy with worked example for CI failure diagnosis. (#5)
- Deletable `example.py` + `test_example.py` pair so coverage gate passes from commit 1. (#5)

## [v1.2.0] - 2026-05-12

Template now ships with the OSS hygiene files a public project needs from day one.

### Added
- `SECURITY.md`, `CONTRIBUTING.md`, GitHub issue templates, PR template added to template tree. (#4)
- `make format`, `make typecheck`, `make coverage` targets added to template Makefile. (#4)

## [v1.1.0] - 2026-05-12

Added GitHub username as a required project value. Each bootstrapped project now records a provenance file (scaffold version, commit SHA, timestamp) at commit 1.

### Added
- `<<GITHUB_USERNAME>>` as 10th required placeholder; used in `pyproject.toml` project URLs. (#3)
- `.scaffold-version` provenance file written into every scaffolded project at commit 1. (#3)
- Weekly scheduled CI run on the scaffold repo to catch environmental drift. (#3)

### Fixed
- Interrupted bootstrap now cleans up the partial target directory. (#3)

## [v1.0.0] - 2026-05-12

Initial release. A 23-file template tree with placeholder substitution, a `scaffold.sh` orchestrator, 5 pinning tests, and self-test CI.

### Added
- 23-file template tree with `scripts/scaffold.sh` orchestrator and `scripts/substitute.py` atomic engine.
- 5 pinning tests: no print-debug, no secrets, type hints on public functions, no mutable defaults, import-contract placeholder.
- Self-test CI running end-to-end scaffold smoke test on every push.

### Security
- Branch protection on `main` requires 1 review + passing CI before merge.
- GitHub Actions pinned to SHAs; Dependabot tracks weekly.
