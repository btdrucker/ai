---
name: address-pr-comments
description: Uses gh-cli to list PR comments, decide which need addressing, and propose specific changes. Use when addressing PR feedback, resolving review comments, or when the user asks to handle comments on a pull request.
---

# Address PR Comments

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Run from a git repo with a PR (current branch), or pass `gh pr view <number>` / `gh pr view -R owner/repo`

## Agent Requirements

**Always run gh commands with `required_permissions: ["all"]`.** The sandbox blocks network access; corporate proxies and TLS certificates cause gh to fail with `x509: OSStatus -26276` or connection errors. Do not retry in sandbox—use full permissions from the first attempt.

## Workflow Overview

1. **List all PR comments**
2. **Triage each comment** — address or skip
3. **Present assessment and stop** — wait for user approval ("apply all", "apply 1 and 3", etc.)
4. **Apply changes** — make code edits only (no commit yet)
5. **Ask to test locally** — stop if YES, continue if NO
6. **Stage, commit, push** — amend into original commit and force-push
7. **React to every comment** — thumbs up (👍) if addressed or valid, thumbs down (👎) if skipped as irrelevant/wrong
8. **Reply to every comment** — confirm fix or explain why skipped

Steps 7 and 8 are **mandatory** and always happen automatically after pushing. Never skip them.

---

## Step 1: Gather PR Context

Use `required_permissions: ["all"]` for all gh commands in this skill.

**owner/repo**: Prefer `git remote get-url origin` — `headRepository.owner.login` is often null on enterprise GitHub. Parse with:
```bash
git remote get-url origin | sed -E 's/.*[:/]([^/]+)\/(.+)\.git/\1\/\2/'
```

**PR number**:
```bash
gh pr view --json number -q '.number'
```

---

## Step 2: List All Comments

Run both APIs with `required_permissions: ["all"]`. Substitute `{owner}`, `{repo}`, `{number}` from Step 1.

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments
gh api repos/{owner}/{repo}/issues/{number}/comments
```

**Parse inline comments** (raw JSON is large) with jq — capture `id` for later reactions/replies:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments | jq -r '.[] | "---\nid:\(.id) | \(.path) L\(.line // .original_line // "file") | @\(.user.login)\n\(.body[0:300])\n"'
```

---

## Step 3: Triage Each Comment

**Skip if already resolved**: A reply from the PR author with "Fixed", "done", "addressed", or a reviewer closure ("not needed", "intentional") — skip and thumbs up.

**Skip general noise**: "Deploy Complete", "No issues found", approvals, CI status messages.

For each remaining comment, decide:

| Decision | Examples | Reaction |
|----------|----------|----------|
| **Address** | Actionable feedback, bug, missing docs, inconsistency, clarification needed | 👍 thumbs up |
| **Skip — irrelevant/wrong** | Out of scope, factually incorrect suggestion, already handled elsewhere | 👎 thumbs down |
| **Skip — noise** | Deploy complete, approval, no-op bot message | No reaction |

When in doubt, include it for user review.

---

## Step 4: Present Assessment and Stop

Produce the assessment table and detailed rundown, then **stop and wait for the user to respond**.

**Assessment table**:

| # | File | Comment excerpt | Decision | Reaction |
|---|------|-----------------|----------|----------|
| 1 | `README.md` | "..." | Address | 👍 |
| 2 | `.nvmrc` | "..." | Skip (irrelevant) | 👎 |

**Detailed rundown** — for each comment to address:
1. Full comment text (or key excerpt)
2. Why it should be addressed
3. Exact location (file path, line numbers)
4. Concrete implementation — what to add, remove, or replace
5. Edge cases to preserve
6. Impact

**Summary**: Total N | To address M | Skipped N−M

**Stop here.** Wait for the user's next message. Their reply — whatever it says — is the signal to proceed with Steps 5, 6, and 7. Do not proceed until they respond.

---

## Step 5: Apply Changes

Once the user responds with their instruction, apply the agreed code edits to the relevant files.

---

## Step 5.5: Confirm Before Push (Mandatory Stop)

After applying all code changes — but **before** staging, committing, or pushing — ask the user:

> **Would you like to test locally first?**
> - **YES** → Stop here. Wait for the user's next message before proceeding.
> - **NO** → Continue immediately to Step 6 (stage, commit, push).

Do not proceed past this point until the user responds.

---

## Step 6: Stage, Commit, Push

Once the user confirms to proceed, **amend into the original commit** and force-push:

```bash
git add <changed files>
git commit --amend --no-edit
git push --force-with-lease origin HEAD
```

**CRITICAL:** Never create a new commit after PR comments. Always amend into the original commit to maintain a single clean commit history.

Use `required_permissions: ["all"]` for push.

---

## Step 7: React to Every Comment (Mandatory)

After pushing, react to **every triaged comment** using the GitHub reactions API.

**Thumbs up** (👍) — comment was addressed OR was a valid suggestion already handled:
```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions \
  --method POST \
  -f content="+1"
```

**Thumbs down** (👎) — comment was skipped as irrelevant, factually wrong, or out of scope:
```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/reactions \
  --method POST \
  -f content="-1"
```

Use `required_permissions: ["all"]` for all reaction calls.

---

## Step 8: Reply to Every Comment (Mandatory)

After reacting, post a reply to **every triaged comment**.

**For addressed comments** — confirm what was fixed:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  --method POST \
  -f body="Fixed — <one sentence describing what changed and where>"
```

**For skipped comments (irrelevant/wrong)** — explain why:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  --method POST \
  -f body="Not addressed — <one sentence explaining why this change isn't applicable or correct>"
```

Use `required_permissions: ["all"]` for all reply calls.

Do **not** mention that responses were AI-generated in replies.

---

## Step 9: Resolve Copilot Threads (Mandatory for All Copilot Comments)

After replying to all comments, resolve **all Copilot bot review threads** — whether they were addressed or skipped as intentional design.

- **If any Copilot comments exist** → execute the resolve-threads mutation to close all unresolved Copilot threads
- **If all comments were from human engineers only** → skip entirely

This closes Copilot feedback loops while keeping human review threads open for engineers to close themselves. Once you've replied with an explanation (whether the issue was addressed or is intentional design), always resolve the Copilot thread.

Query for unresolved Copilot threads:

```bash
gh api graphql -f query='
{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {number}) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes {
              databaseId
              author { login }
            }
          }
        }
      }
    }
  }
}'
```

For each unresolved thread where `author.login == "copilot-pull-request-reviewer"`, resolve it:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: { threadId: "{thread_node_id}" }) {
    thread {
      id
      isResolved
    }
  }
}'
```

Use `required_permissions: ["all"]` for all GraphQL calls.

---

## Skill Efficiency

If commands fail due to sandbox/permissions and you had to retry with full permissions, update this skill to include the fix so it succeeds on first try next time.
