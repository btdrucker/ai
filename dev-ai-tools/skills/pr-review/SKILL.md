---
name: pr-review
description: Review a GitHub Pull Request with structured feedback. Use when the user wants to review a PR, do a code review, or validate a pull request.
---

# PR Review

## Related skills

- **`github`** -- GitHub operations gateway (MCP first, built-in second, CLI third)

Review code changes with structured feedback. Supports two modes:

- **PR mode** (default) -- reviews an existing GitHub Pull Request, posts file-level comments and a summary to the PR
- **Pre-review mode** -- reviews the local diff between the current working branch and its target branch *before* a PR is created, reports findings directly to the user in chat (no GitHub comments)

## Mode Detection

Ask the user which mode they want:

1. **PR mode** -- provide a PR number or link to review
2. **Pre-review mode** -- review the current branch diff locally before creating a PR

If the caller already specified a mode (e.g. "pre-review" or provided a PR number/link), skip the prompt and proceed directly.

---

## Pre-review Mode

Lightweight local review of the delta between the current branch and its target branch. Catches issues before the PR is created so they can be fixed first.

### Pre-review Step 1: Gather the diff

Determine the repo and branches:

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
CURRENT_BRANCH=$(git branch --show-current)
```

For `BASE_BRANCH`: first check the workspace registry -- search the workspace for `*.code-workspace`, read its first folder entry (the workspace directory), look for `workspace-registry.json`. If the registry has a `defaultBranch` for this repo, use it. If the registry is not found or the repo is not in it, fall back to:

```bash
BASE_BRANCH=$(git remote show origin | grep 'HEAD branch' | awk '{print $NF}')
```

If the caller provides a target branch, use that instead of the detected default.

Fetch the base branch so the diff is against current upstream:

```bash
git fetch origin ${BASE_BRANCH}
```

Get the diff (use `origin/` prefix to ensure freshness):

```bash
git diff origin/${BASE_BRANCH}...HEAD
git diff origin/${BASE_BRANCH}...HEAD --stat
git log origin/${BASE_BRANCH}..HEAD --oneline
```

### Pre-review Step 2: Analyze the diff

Review all changed files for bugs, correctness issues, and anything that stands out. Use the same approach as PR mode Step 2.

### Pre-review Step 3: Report findings to the user

Present findings directly in chat (do NOT post to GitHub). Format as:

1. A list of actionable findings grouped by file, with line numbers and recommendations
2. A summary section with positives, and overall assessment
3. If there are critical issues, clearly state they should be fixed before creating the PR

Do NOT post any GitHub comments, do NOT create a PR, do NOT modify code.

---

## GitHub Operations

> **GitHub operations:** Follow the `github` skill's integration policy.

## PR Mode

Full review of an existing GitHub Pull Request with file-level comments posted to GitHub.

### Step 0: Check Out the PR Branch

Always ask the user whether they want to check out the PR branch locally. Checking out provides more accurate reviews because the agent can read full file context (imports, surrounding functions, how changed code is called) rather than relying solely on the diff. Without checkout, the local files may be on a completely different branch and not reflect the PR's code at all.

If the user declines, set `CHECKED_OUT=false` and proceed with diff-only review. If the user accepts (or already requested it, e.g. "check out the branch", "review locally"), perform the checkout:

**0a. Record the current branch**

```bash
ORIGINAL_BRANCH=$(git branch --show-current)
```

**0b. Stash uncommitted changes if present**

```bash
if [ -n "$(git status --porcelain)" ]; then
  git stash push -m "pr-review-auto-stash"
  STASHED=true
else
  STASHED=false
fi
```

**0c. Fetch the base branch so local diffs are accurate**

The PR targets a base branch (e.g. `master`, `main`). Fetch and fast-forward it so the agent can run local diffs against current upstream code:

```bash
BASE_BRANCH=<baseRefName from PR metadata>
git fetch origin ${BASE_BRANCH}
git branch -f ${BASE_BRANCH} origin/${BASE_BRANCH}
```

**0d. Check out the PR branch**

```bash
gh pr checkout <N>
```

Set `CHECKED_OUT=true` so Step 7 knows to restore.

### Step 1: Gather PR Information

Ask the user for the PR link if not provided. Extract the PR number and determine the repo.

Use the `github` skill **quick reference** (or **REFERENCE.md** S2-S3) for `gh repo view --json nameWithOwner`, `gh pr view` with `--json title,body,author,files,additions,deletions,headRefName,headRefOid,statusCheckRollup`, and `gh pr diff`.

Store the commit SHA from `headRefOid` -- needed for posting file-level comments. Note the CI status from `statusCheckRollup` -- if checks are failing, mention it in the final summary.

### Step 2: Analyze the PR -- Code Review

Review all changed files for bugs, correctness issues, and anything that stands out. Use your judgment -- do not follow a prescriptive checklist. Focus on things that matter: actual bugs, security issues, logic errors, missing edge cases, SOLID/DRY/KISS violations, and patterns that will cause problems down the road. Do NOT flag code style, formatting, or linting issues -- those are handled by tooling, not reviews.

### Step 3: Categorize Findings

Use these emoji indicators consistently:

- **Critical**: Must be fixed -- security issues, bugs, breaking changes
- **Discussion**: Worth discussing -- refactoring, patterns, architecture
- **Question**: Clarifications needed -- intent, design decisions, requirements
- **Nitpick**: Minor suggestions -- naming, minor structural improvements (not formatting/style)
- **Action item**: Recommended improvement the PR author can resolve independently. Use this in the final summary only when a concrete follow-up is warranted but doesn't need a line-specific GitHub comment
- **Positive**: Good practices -- only in summary body, NOT as file comments

### Step 4: Present Findings for User Approval

Before posting anything to GitHub, present ALL findings to the user in chat for review. Format as a numbered list grouped by file, showing the category, title, target line, and a one-sentence description for each finding. Also include the positives and overall assessment.

Wait for the user to:
- **Approve all** -- proceed to post everything
- **Remove specific items** -- drop those findings before posting
- **Edit specific items** -- adjust wording/severity before posting
- **Add items** -- include additional findings the user wants raised

Do NOT post any GitHub comments until the user explicitly approves. This checkpoint ensures the review reflects the reviewer's judgment, not just the AI's analysis.

### Step 5: Post File-Level Comments

For each approved actionable finding, post a file-level review comment using the `github` **quick reference** (PR comments -- file-level pattern). Use the commit SHA from `headRefOid`, the file path, diff line number, and `side='RIGHT'`.

Format the comment body as:
```
**<CATEGORY>: <TITLE>**

<DESCRIPTION>

**Recommendation:**
<BULLETED_LIST>
```

**Rules for file comments:**
- Only post actionable items (Critical, Discussion, Question, Nitpick)
- Do NOT post Positive items as file comments
- Each comment should be self-contained
- Include code examples when relevant
- Use diff line numbers, not absolute line numbers
- One issue per comment

### Step 6: Post Final Summary Comment

After all file comments, post a comprehensive summary using the `github` **quick reference** (PR comments -- general timeline comment: `gh pr comment <N> --body "..."`).

**Summary format:**

```markdown
> [!WARNING]
> This PR review has been generated using GenAI and should be reviewed by a human before taking action.

# PR Review Summary

Reviewed PR #<NUMBER> - <TITLE>. I've left **N file-level comments** on specific files that need attention.

---

## Positives

### <Category>
- <Observation>

---

## File-Level Comments Summary

### Critical (N)
1. **`<file>:<line>`** - <Brief description>

### Discussion (N)
2. **`<file>:<line>`** - <Brief description>

### Questions (N)
3. **`<file>:<line>`** - <Brief description>

### Nitpicks (N)
4. **`<file>:<line>`** - <Brief description>

---

## Summary

<Overall assessment -- code quality verdict + key takeaways>
```

### Step 7: Cleanup

- Do NOT create temporary files
- Do NOT leave draft reviews unsubmitted
- Confirm all comments were posted successfully

**Restore original branch (if Step 0 was used)**

If `CHECKED_OUT=true`, switch back to the original branch and pop any stashed changes:

```bash
git checkout ${ORIGINAL_BRANCH}
```

```bash
if [ "$STASHED" = "true" ]; then
  git stash pop
fi
```

If the checkout or stash pop fails, warn the user but do not abort -- the review itself is complete.

## Guidelines

**DO:**
- Post file-level comments for actionable items
- Include positive feedback in the summary body only
- Provide specific line numbers and file paths
- Include code examples for clarity
- Be constructive and respectful
- Prioritize critical issues first

**DON'T:**
- Post positive items as file-level comments
- Combine multiple issues in one comment
- Use absolute line numbers (use diff line numbers)
- Forget the GenAI disclaimer
- Skip the summary comment
- Modify any code in the repository
- Make assumptions without asking questions
