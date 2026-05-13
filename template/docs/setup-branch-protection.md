# Set up branch protection on `main`

GitHub Free supports basic branch protection on public repos. This guide enables the minimum recommended ruleset: no force-push, no deletion, and (after first CI run) required status checks.

## Why

Branch protection prevents accidental destructive operations. Without it, anyone with write access (including you, in a confused moment) can `git push --force` to main, rewriting history. Required status checks ensure CI must be green before merge.

## Quick setup (via `gh` CLI)

After the project has at least one push to `main` and the first CI run has completed:

```bash
PROTECTION_BODY='{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'

echo "$PROTECTION_BODY" | gh api \
  "repos/<your-github-username>/<your-repo>/branches/main/protection" \
  --method PUT --input -
```

Replace `<your-github-username>` and `<your-repo>` with your values.

## Quick setup (via GitHub UI)

1. Go to your repository on github.com.
2. Settings → Branches → Add branch protection rule.
3. Branch name pattern: `main`.
4. Recommended checkboxes:
   - [x] Require a pull request before merging
   - [ ] Require approvals (skip for solo projects; enable for team projects with 1)
   - [x] Require status checks to pass before merging
     - Add: `smoke` (or your CI job name) once it has run at least once
   - [x] Restrict who can push to matching branches → uncheck "Allow force pushes" and "Allow deletions"
5. Save changes.

## Verify

```bash
gh api "repos/<your-github-username>/<your-repo>/branches/main/protection"
```

Returns the protection settings (or `Branch not protected` if not configured).

## Common gotchas

- **Status checks must run at least once** before you can require them by name. Push a trivial commit if your CI hasn't fired yet.
- **Private repos** on GitHub Free have no branch protection. Upgrade to GitHub Pro / Team, or use a public repo.
- **Admin bypass**: by default branch protection rules do not apply to admins (`enforce_admins: false`). Set to `true` only when your CI is rock-solid; otherwise a transient failure locks you out of merging your own fixes.

See also: [`docs/enforcement-model.md`](enforcement-model.md) for how branch protection fits into the four-tier enforcement model.
