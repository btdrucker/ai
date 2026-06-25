---
name: create-or-update-pr
description: Create or update a PR after pushing. Uses TICKET-KEY title format (uppercase), repo-specific PR templates for mamba and productwall. Run all gh commands with required_permissions ["all"].
---

# Create or Update PR

After pushing, create a pull request if one doesn't exist, or update an existing one if scope changed.

**Run all `gh` commands with `required_permissions: ["all"]`**.

## PR Title Format

Nike App Android repos use ticket-prefixed titles (ticket key ALWAYS uppercase):

```
NIKEAPPUI-237: Align product wall carousel thumbnails
```

Derive title:

```bash
bash ~/.cursor/skills/create-or-update-pr/derive-pr-title.sh
```

Or from branch `mpinau/NIKEAPPUI-237/product-wall-carousel` + latest commit message.

## Repo-Specific PR Templates

Detect repo and fill the matching template:

### Mamba (`mpe.app.mamba-android`)

Template: `.github/pull_request_template.md`

```markdown
### Jira Link(s)
https://jira.nike.com/browse/NIKEAPPUI-XXX

### Description
...

### Testing Instructions
...

### Notes (Optional)

### Screenshots / Videos (UI Changes Only)
```

### Product Wall (`mpe.feature.productwall`)

Template: `.github/pull_request_template.md`

```markdown
**Jira issue:** https://jira.nike.com/browse/NIKEAPPUI-XXX

**Description of changes:**
...

**Tasks:**
- [ ] Demo App is working
- [ ] QE validation
- [ ] Update CHANGELOG.md
```

### Nike App (`mpe.app.nikeapp-android`)

No PR template. Use:

```markdown
## Summary
...

## Jira
https://jira.nike.com/browse/NIKEAPPUI-XXX

## Test Plan
...
```

## Check for project-specific PR commands

Before default flow, check:
1. `.cursor/commands/create-pr.md`
2. `.cursor/rules/*pr*.mdc`
3. `CONTRIBUTING.md`, `.github/pull_request_template.md`

If project-specific rules exist, follow them (but keep TICKET-KEY title format).

## Flow

### 1. Check if PR exists

```bash
gh pr view --json url,title,body -q '.url' 2>/dev/null
```

- Exists → step 5
- Not exists → step 2

### 2. Load PR template

```bash
cat .github/pull_request_template.md 2>/dev/null
```

Fill Jira link with uppercase ticket key from branch/commits.

### 3. Derive PR title

```bash
bash ~/.cursor/skills/create-or-update-pr/derive-pr-title.sh
```

### 4. Create PR

```bash
gh pr create --title "NIKEAPPUI-237: Description" --body "$(cat <<'EOF'
...
EOF
)"
```

Display PR URL.

### 5. Update existing PR if scope changed

```bash
gh pr view --json title,body,url
git log origin/main..HEAD --oneline
git diff origin/main...HEAD --stat
```

Update title/body if scope expanded. Keep `TICKET-KEY:` title format.

## Base Branch

Use PR base from `gh pr view --json baseRefName` when updating diffs. Default is `main`.
