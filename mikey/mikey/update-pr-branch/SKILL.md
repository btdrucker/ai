---
name: update-pr-branch
description: Update the current feature branch by rebasing it onto its PR base branch. Detects the base branch from the open PR via gh-cli, fetches latest, auto-stashes uncommitted work, rebases, and force-pushes. Use when the user says the branch is behind, out of date, out of sync, needs updating, or asks to pull in latest changes from main/master/develop.
---

# Update PR Branch

Rebase the current branch onto the latest base branch detected from the open pull request.

## Workflow

### Step 1 — Identify the base branch

```bash
gh pr view --json baseRefName --jq '.baseRefName'
```

If no PR exists, abort and inform the user there is no open PR for the current branch.

### Step 2 — Check for uncommitted changes

```bash
git status --porcelain
```

If output is non-empty, stash everything (including untracked files):

```bash
git stash push -u -m "update-pr-branch: auto-stash before rebase"
```

Track that a stash was created so it can be restored later.

### Step 3 — Fetch and rebase

```bash
git fetch origin <base_branch>
git rebase origin/<base_branch>
```

Replace `<base_branch>` with the value from Step 1.

**If rebase conflicts occur:**
1. Stop and show the user the conflicting files (`git diff --name-only --diff-filter=U`).
2. Do NOT attempt to resolve conflicts automatically.
3. Remind the user they can run `git rebase --abort` to undo.
4. If changes were stashed, remind them the stash still needs to be popped after resolution.

### Step 4 — Force-push

After a clean rebase with no conflicts:

```bash
git push --force-with-lease
```

Use `--force-with-lease` (never bare `--force`) to protect against overwriting unexpected remote changes.

### Step 5 — Restore stashed changes

If changes were stashed in Step 2:

```bash
git stash pop
```

If the pop produces conflicts, inform the user and list the affected files.

### Step 6 — Confirm

Print a short summary:
- Base branch used
- Number of new commits pulled in (compare old and new HEAD)
- Whether stashed changes were restored
- Current `git status`
