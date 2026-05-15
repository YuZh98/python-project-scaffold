## Summary

<!-- WHAT changed (one or two bullets). No process narrative. -->

## Changes

<!-- Concrete file/behavior changes. -->

## Test plan

- [ ] CI `smoke` green on Linux runner.
- [ ] If a new rule is added: corresponding pinning test or pre-commit hook also added (or xfail bridge with linked follow-on).
- [ ] If a placeholder is added/renamed: `template.manifest.json` updated, both `tests/test_scaffold.py` `SAMPLE_VALUES` and `tests/test_init_project.py` `SAMPLE_VALUES` updated.
- [ ] CHANGELOG entry added under `[Unreleased]`.

## Architectural decisions

- [ ] If any decision is hard-to-reverse (cross-module impact + viable alternatives existed): new ADR added under `template/docs/adr/` referenced from this PR.

## Migration impact

<!-- For released-tag bumps only. Describe what existing skill / project users need to do to adopt this version. -->
