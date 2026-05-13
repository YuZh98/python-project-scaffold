# Examples

Sample values.json for non-interactive bootstrap.

## How to use

```bash
cp examples/values.example.json values.json
# edit values.json with your project details
python3 scripts/init-project.py --values values.json
```

Pass `--keep-history` to preserve the scaffold's commit history (default: reset to a clean slate).
Pass `--no-install` to skip the automatic `make install` step.
Pass `--dry-run` to preview without writing.

## Placeholder reference

| Placeholder | Validation | Auto-derived? |
|-------------|------------|----------------|
| `<<PROJECT_NAME>>` | lowercase letters / digits / hyphens, e.g. `my-cool-tool` | no |
| `<<PROJECT_TITLE>>` | display name, e.g. `My Cool Tool` | from project name (Title Case) by `init-project.py` |
| `<<PACKAGE_NAME>>` | snake_case Python package, e.g. `my_cool_tool` | from project name (replace `-` with `_`) by `init-project.py` |
| `<<DESCRIPTION>>` | no `"` or backslash (substituted into TOML) | no |
| `<<AUTHOR_NAME>>` | any non-empty | from `git config user.name` |
| `<<AUTHOR_EMAIL>>` | valid email pattern | from `git config user.email` |
| `<<YEAR>>` | 4-digit year | from `datetime.date.today().year` |
| `<<LICENSE_ID>>` | `MIT` / `Apache-2.0` / `BSD-3-Clause` / `Unlicense` | no |
| `<<PYTHON_FLOOR>>` | `3.11` or later (e.g. `3.12`, `3.13`) | no |
| `<<GITHUB_USERNAME>>` | GitHub login | from `gh api user --jq .login` if installed |

If you fill in all fields in `values.json`, the auto-derived columns are ignored — your values take precedence.
