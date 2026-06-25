---
name: respond-to-pr-comments
description: Reply to PR review comments after pushing changes. Marks addressed comments as fixed, explains unaddressed ones, and auto-resolves bot review threads. Run all gh commands with required_permissions ["all"].
---

# Respond to PR Comments

When the branch has an open PR and the user expects comment follow-up (e.g. addressing PR feedback, resolving review threads), reply to relevant review comments.

**Run all `gh` commands with `required_permissions: ["all"]`** — the sandbox blocks network access.

## List comments

```bash
gh pr view --json number -q '.number'
gh api repos/$(git remote get-url origin | sed -E 's/.*[:/]([^/]+)\/(.+)\.git/\1\/\2')/pulls/$(gh pr view --json number -q '.number')/comments | jq -r '.[] | "---\n\(.path) L\(.line // .original_line // "?") | @\(.user.login)\n\(.body[0:300])\n"'
```

## Decide per comment

| Action | When |
|--------|------|
| **Reply "Fixed"** | The pushed changes address the comment — reply briefly (e.g. "Fixed in &lt;short-sha&gt; — &lt;what changed&gt;") |
| **Reply "Not addressing"** | The comment is out of scope, incorrect, or intentionally declined — reply with a short reason (e.g. "Intentional — …", "Out of scope because …") |
| **Skip** | Already has a resolution reply, Deploy Complete, approval, or general noise |

Skip entirely if there is no open PR, `gh` is not available, or the user did not ask to address PR comments.

## Reply to a specific comment

Use the GitHub API with `in_reply_to` as an **integer** (not string). Put all fields in the JSON body and pipe via `printf` (not `echo`, which mangles backticks and special characters):

```bash
printf '{"body":"Fixed in <sha> — <brief description>.","in_reply_to":<comment_id>}' | gh api repos/<owner>/<repo>/pulls/<number>/comments -X POST --input - --jq '.id'
```

**Do NOT mix `--input -` with `-f` flags** — `-f` adds fields as strings and conflicts with the piped JSON body. `in_reply_to` must be an integer, which `-f` cannot produce.

Get comment IDs from the API response; use `jq '.[] | {id, path, line, user: .user.login}'` when listing.

## Auto-resolve bot review threads

After replying to comments, auto-resolve review threads authored by bots. **Only auto-resolve threads from these authors** — never human reviewers:

- `copilot-pull-request-reviewer` (GitHub Copilot)
- `github-actions[bot]`
- `cursor[bot]`

**Get unresolved bot threads:**
```bash
gh api graphql -f query='
  query {
    repository(owner: "{owner}", name: "{repo}") {
      pullRequest(number: {number}) {
        reviewThreads(first: 50) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes { author { login } }
            }
          }
        }
      }
    }
  }
' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false) | select(.comments.nodes[0].author.login == "copilot-pull-request-reviewer" or .comments.nodes[0].author.login == "github-actions[bot]" or .comments.nodes[0].author.login == "cursor[bot]") | .id'
```

**Resolve each thread:**
```bash
for thread_id in $BOT_THREAD_IDS; do
  gh api graphql -f query="mutation { resolveReviewThread(input: { threadId: \"$thread_id\" }) { thread { isResolved } } }" --jq '.data.resolveReviewThread.thread.isResolved'
done
```
