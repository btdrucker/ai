---
name: pr-create
description: Create a pull request for the current branch. Use when the user wants to create a PR, pull request, or merge request for any repo in the workspace.
---

# Create Pull Request

## Related skills

- **`github`** -- GitHub operations gateway (MCP first, built-in second, CLI third)

> **GitHub operations:** Follow the `github` skill's integration policy.

Creates a well-structured pull request for the current branch, automatically detecting the correct base branch and generating a detailed summary from the commits and diff.

## Workflow

### Step 1: Identify the repo and branch

Determine which repo the user is working in. If ambiguous (e.g. multiple repos have changes), ask.

```bash
git rev-parse --show-toplevel
git branch --show-current
```

### Step 2: Determine the base branch

If the user specified a target branch, use that as `BASE_BRANCH`. Otherwise, auto-detect:

- Check the workspace registry first: search the workspace for `*.code-workspace`, read its first folder entry (the workspace directory), look for `workspace-registry.json`. If the registry has a `defaultBranch` for the current repo, use it. If the registry is not found or the repo is not in it, fall back to:

```bash
git remote show origin | grep 'HEAD branch' | awk '{print $NF}'
```

Store the result as `BASE_BRANCH`. Tell the user what you detected and give them the option to override it with a different target branch before proceeding.

If the current branch IS the base branch, stop and tell the user -- there's nothing to PR.

### Step 3: Gather changes

**Always fetch the latest base branch first** to avoid comparing against a stale local ref. A stale local `main` (or `master`) will show commits that have already been released, producing a wildly inflated diff.

```bash
git fetch origin ${BASE_BRANCH}
```

Then run these in parallel, using `origin/${BASE_BRANCH}` (not the local ref):

```bash
# All commits on this branch since it diverged from base
git log origin/${BASE_BRANCH}..HEAD --oneline

# Full diff stat
git diff origin/${BASE_BRANCH}...HEAD --stat

# Full diff for content analysis
git diff origin/${BASE_BRANCH}...HEAD

# Check for uncommitted changes
git status --short
```

If there are uncommitted changes, ask the user if they want to commit first or proceed without them.

If there are zero commits ahead of base, stop and tell the user there's nothing to PR.

### Step 4: Push the branch

Check if the branch has an upstream set and is up to date:

```bash
git status -sb
```

If the branch needs to be pushed:

```bash
git push -u origin HEAD
```

### Step 5: Generate the PR body

Analyze all commits and the full diff to produce a PR body. Follow these rules strictly:

**Title**: If a Jira ticket ID is present in the branch name (e.g. `feature/SRPLT-1234-fix-rollups` -> `SRPLT-1234: Fix rollups processing`), include it. Otherwise derive a concise title from the changes.

**Jira link**: If a Jira ticket ID is detected, include a link at the top of the Summary section: `[SRPLT-1234](https://jira.nike.com/browse/SRPLT-1234)`

**Body format**:

```markdown
## Summary

<2-4 sentences explaining what this PR does and why. Written for a human reviewer who knows the codebase.>

## Changes

<Group changes by logical concern. For each group, describe WHAT changed and WHY. Reference specific files when helpful. Use bullet points.>

### <Group Name, e.g. "Thread processing fix">

- Description of change and its purpose
- Another change in this group

### <Another Group>

- ...
```

**Mandatory rules for the body**:

- **NEVER include checklists** (`- [ ]`), test plans, TODO sections, or any checkbox syntax in the PR body. The PR body describes what changed and why -- it is not a task tracker.
- NO generic sections like "## Test Plan", "## Screenshots", "## Checklist", "## How to test"
- NO AI slop: no "This PR introduces...", no "Key highlights:", no "This ensures...", no filler phrases
- Write like a senior engineer explaining their changes to a peer in a PR description
- Be specific and technical -- reference actual class names, methods, patterns

### Step 6: Create the PR

Use the `github` **quick reference** or **REFERENCE.md** S3 to create the PR (`gh pr create --base <BASE_BRANCH> --title "<title>" --body "..."`). Use the `$(cat <<'EOF' ... EOF)` pattern for multi-line bodies.

### Step 7: Report

Display:
- PR URL (clickable)
- Title
- Base branch
- Number of commits included
- Files changed count
