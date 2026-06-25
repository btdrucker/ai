---
name: github
description: Perform GitHub operations via gh CLI and GraphQL API. Use when the user wants to interact with GitHub repos, PRs, issues, actions, releases, discussions, projects, or any GitHub data. Consult this skill for correct command syntax whenever any other skill needs to perform a GitHub operation.
---

# GitHub Operations

Authoritative entry point for GitHub work. Other skills MUST consult this skill for correct patterns. Referenced by: `pr-create`, `pr-review`, `pr-address-comments`, `dev-create-new-java-ec2-service`, `dev-update-popular-search-terms`, `search-sdlc`.

## GitHub integration policy

Use the best available GitHub integration for the current environment:

1. **GitHub MCP server** (`user-github-mcp-server`): Preferred when available.
   Freestyling with MCP tools is fine -- no rigid patterns needed.
2. **Built-in GitHub integration**: In VS Code / Copilot, the GitHub Pull
   Requests and Issues extension provides PR review, issue management, and
   in-editor commenting. Use it when MCP is not configured.
3. **CLI fallback**: When neither MCP nor built-in integration covers the
   operation, use the `gh` CLI and GraphQL patterns below.

To detect: attempt an MCP call first. If the MCP server is not configured
or errors, check for built-in capabilities. If neither is available, use CLI.

### MCP coverage

| Operation | MCP tool |
|-----------|----------|
| Create PR | `create_pull_request` |
| List/view PRs | `list_pull_requests`, `pull_request_read` |
| Update/merge PR | `update_pull_request`, `merge_pull_request` |
| Search PRs | `search_pull_requests` |
| PR reviews | `pull_request_review_write` |
| Issues | `issue_read`, `issue_write`, `list_issues`, `search_issues` |
| Code/repo search | `search_code`, `search_repositories` |
| File contents | `get_file_contents` |
| Branches | `create_branch`, `list_branches` |
| Releases | `list_releases`, `get_latest_release` |

### MCP gaps -- use CLI below

| Operation | Why CLI needed |
|-----------|---------------|
| PR diff-line comments with line/side/commit_id | MCP may not support precise diff-line targeting |
| PR review thread resolution | Requires GraphQL `resolveReviewThread` mutation |
| PR review thread fetch with resolution status | Requires GraphQL `reviewThreads` query |
| Full diff output | No MCP equivalent for `gh pr diff` |
| CI check status rollup | No MCP equivalent for `gh pr checks` |
| Arbitrary GraphQL mutations | MCP is REST-focused |

**Full detail (S1-S17, error handling, pitfalls):** read **[`REFERENCE.md`](./REFERENCE.md)** in this folder only when the quick reference below is not enough (e.g. PR review threads, GraphQL mutations, Actions, ProjectV2, secrets).

## Quick reference

```bash
# Auth & identity
gh auth status
gh api user --jq .login

# Repos
gh repo view [<owner/repo>] --json nameWithOwner,defaultBranchRef
gh repo list <org> --json name,url --limit 100
gh search repos "<query>" --owner <org> --json name --limit 50
gh repo clone <owner/repo>

# Pull requests -- read
gh pr list [--head <branch>] [--state open|merged] --json number,title,url,headRefName,baseRefName
gh pr list --search "<query>" --state merged --json number,title,url
gh pr view <N> --json title,body,author,files,headRefOid,statusCheckRollup
gh pr view <N> --json body -q .body
gh pr diff <N>

# Pull requests -- write
gh pr create --base <branch> --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
gh pr edit <N> --body "$(cat <<'EOF'
<updated body>
EOF
)"
gh pr edit <N> --title "<new title>"
gh pr edit <N> --add-label "<label>" --add-reviewer "<user>"
gh pr merge <N> --merge
gh pr merge <N> --squash

# PR comments -- general (timeline)
gh pr comment <N> --body "<text>"

# PR comments -- file-level (diff-attached); see REFERENCE.md S4 for field details
gh api --method POST "repos/<owner>/<repo>/pulls/<N>/comments" \
  -f commit_id='<HEAD_SHA>' -f path='<file>' -f body='<text>' \
  -F line=<DIFF_LINE> -f side='RIGHT'

# PR comments -- list all review comments
gh api "repos/<owner>/<repo>/pulls/<N>/comments" --paginate

# PR comments -- reply to an existing thread (REST)
gh api "repos/<owner>/<repo>/pulls/<N>/comments" \
  -f body='<reply>' -F in_reply_to=<COMMENT_ID>

# PR threads -- fetch thread IDs and resolution status (GraphQL)
gh api graphql -f query='{ repository(owner: "<owner>", name: "<repo>") { pullRequest(number: <N>) { reviewThreads(first: 100) { nodes { id isResolved comments(first: 1) { nodes { databaseId } } } } } } }'

# PR threads -- resolve a thread (GraphQL; use thread id from above)
gh api graphql -f query='mutation { resolveReviewThread(input: { threadId: "<THREAD_NODE_ID>" }) { thread { isResolved } } }'

# Issues
gh issue list --json number,title,state --limit 50
gh issue view <N>

# Search
gh search prs "<query>" --json number,title,repository
gh search issues "<query>" --json number,title,repository

# Generic REST (prefer --jq for small payloads)
gh api repos/<owner>/<repo>/... --jq '.field'
```

**When to open `REFERENCE.md`:** full PR review thread details (S5), Actions runs (S8), releases (S9), discussions (S11), projects (S12), gists (S13), orgs (S14), secrets/variables (S15), rulesets (S16), raw GraphQL (S17), error handling -- see section index there.

**Prerequisites:**

| Tool | Purpose | Install | Verify |
|------|---------|---------|--------|
| `gh` | GitHub CLI -- all GitHub operations | `brew install gh` | `gh --version` |
| `git` | Version control -- branch, commit, push | `brew install git` (or Xcode CLT) | `git --version` |
| `jq` | JSON processing -- complex filtering beyond `gh --jq` | `brew install jq` | `jq --version` |

**Configuration required:**
- `gh auth login` -- authenticate with GitHub (use SSO/OAuth for enterprise orgs like `nike-internal`)
- `ssh-keygen` + add to GitHub -- SSH key for `git clone`/`git push` over SSH (`ssh -T git@github.com` to verify)

> **Note**: `gh` has a built-in `--jq` flag for simple field extraction (e.g. `gh api user --jq .login`). Standalone `jq` is only needed for complex multi-step JSON pipelines outside of `gh` commands.

**Rules:**
- Always use `required_permissions: ["full_network"]` for `gh` commands
- All `gh` commands return JSON by default when using `--json` flags
- Use `--paginate` for any list endpoint that may return more than 100 results
- Use `--jq` or `-q` for field extraction from JSON responses
