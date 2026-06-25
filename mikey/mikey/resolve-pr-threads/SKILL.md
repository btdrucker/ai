---
name: resolve-pr-threads
description: Resolves GitHub PR review conversation threads via GraphQL. Only used for Copilot bot comment threads — never for human/engineer comments. Called by address-pr-comments after replying to Copilot comments.
---

# Resolve PR Threads

Resolves conversation threads for a given list of Copilot comment node IDs. This skill is only ever called for Copilot bot comments — human engineer comments are never resolved here.

**Always run gh commands with `required_permissions: ["all"]`.**

## Input

A list of pull request review thread node IDs to resolve. These come from the caller (e.g. `address-pr-comments`) — only Copilot comment thread node IDs should be passed in.

## Step 1: Get Thread Node IDs

Pull request review *thread* node IDs are different from comment node IDs. Fetch threads and match to the Copilot comment node IDs:

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

Filter for threads where `comments.nodes[0].author.login == "copilot-pull-request-reviewer"` and `isResolved == false`. Note: the Copilot bot login is `copilot-pull-request-reviewer`, not `Copilot`.

## Step 2: Resolve Each Thread

For each unresolved Copilot thread node ID, call:

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

## Step 3: Confirm

After resolving, log which thread IDs were resolved so the caller can confirm completion.
