# Security Policy

## Supported versions

The latest minor release (`v1.x.0`) of `python-project-scaffold` receives security fixes. Older releases do not.

## Reporting a vulnerability

Use [GitHub security advisories](https://github.com/YuZh98/python-project-scaffold/security/advisories/new) (private). Do not file public issues for vulnerabilities.

In scope:
- The scaffold engine: `scripts/init-project.py`, `scripts/scaffold.sh`, `scripts/substitute.py`.
- Path-traversal or command-injection in placeholder substitution.
- Vulnerabilities in the GitHub Actions workflows that ship in `template/.github/workflows/`.

Out of scope:
- Vulnerabilities in the user's own scaffolded project after they have added their own code.
- Issues in upstream dependencies (`ruff`, `pyright`, `pytest`, `pre-commit`, `conventional-pre-commit`). Report those to the upstream project.

Best-effort response within 7 days. No bug bounty — this is a personal project.
