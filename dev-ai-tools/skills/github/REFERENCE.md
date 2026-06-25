# GitHub operations -- full reference

Companion to [`SKILL.md`](./SKILL.md). Use **SKILL.md** for day-to-day `gh` patterns and rules. **Read this file** when you need S1-S17 detail: PR review comments and threads (S4-S5), Actions (S8), Releases (S9), Discussions (S11), ProjectV2 (S12), secrets (S15), raw GraphQL (S17), and **Error handling** at the end.

**Section index:** S1 Authentication | S2 Repositories | S3 Pull Requests | S4 PR Comments | S5 PR Reviews & Threads | S6 Issues | S7 Labels & Assignees | S8 Actions | S9 Releases | S10 Search | S11 Discussions | S12 ProjectV2 | S13 Gists | S14 Organizations & Users | S15 Secrets & Variables | S16 Actions Cache & Rulesets | S17 Raw GraphQL | Error handling (end)

## 1. Authentication & Viewer

```bash
# Check authentication status
gh auth status

# Get the authenticated user's login
gh api user --jq .login
```

---

## 2. Repositories

```bash
# Get repo metadata (nameWithOwner, default branch, etc.)
gh repo view --json nameWithOwner -q .nameWithOwner
gh repo view --json nameWithOwner,defaultBranchRef

# Get repo details with specific fields
gh repo view <owner/repo> --json name,description,url,defaultBranchRef,isPrivate,isFork

# List repos in an org
gh repo list <org> --json name,url --limit 100

# Search repos by name in an org
gh search repos "<query>" --owner <org> --json name --limit 50

# Clone a repo
gh repo clone <owner/repo>

# Create a repo
gh repo create <name> --private --clone

# View repo topics
gh repo view --json repositoryTopics

# View repo languages
gh api repos/<owner>/<repo>/languages
```

---

## 3. Pull Requests

### Read operations

```bash
# View PR details
gh pr view <NUMBER> --json title,body,author,files,additions,deletions,headRefName,headRefOid,statusCheckRollup

# View PR diff
gh pr diff <NUMBER>

# List PRs (various filters)
gh pr list --json number,title,url,headRefName,state
gh pr list --head <branch> --json number,title,url
gh pr list --search "<query>" --state merged --json number,title
gh pr list --state open --json number,title,author,headRefName,baseRefName
gh pr list --label "<label>" --json number,title

# View PR body only
gh pr view <NUMBER> --json body -q .body

# View PR checks/CI status
gh pr view <NUMBER> --json statusCheckRollup

# List PR files
gh pr view <NUMBER> --json files
```

### Write operations

```bash
# Create a PR
gh pr create --base <BASE_BRANCH> --title "<title>" --body "$(cat <<'EOF'
<body content>
EOF
)"

# Update PR body
gh pr edit <NUMBER> --body "$(cat <<'EOF'
<updated body>
EOF
)"

# Update PR title
gh pr edit <NUMBER> --title "<new title>"

# Add labels
gh pr edit <NUMBER> --add-label "<label1>,<label2>"

# Add reviewers
gh pr edit <NUMBER> --add-reviewer "<user1>,<user2>"

# Add assignees
gh pr edit <NUMBER> --add-assignee "<user>"

# Merge a PR
gh pr merge <NUMBER> --merge
gh pr merge <NUMBER> --squash
gh pr merge <NUMBER> --rebase

# Close a PR
gh pr close <NUMBER>

# Reopen a PR
gh pr reopen <NUMBER>

# Mark as ready for review (from draft)
gh pr ready <NUMBER>

# Convert to draft
gh pr ready <NUMBER> --undo
```

---

## 4. PR Comments

GitHub has multiple comment types on PRs. Choosing the right one is critical.

### Comment type decision tree

1. **General PR comment** (timeline/conversation comment, not attached to a file):
   ```bash
   gh pr comment <NUMBER> --body "<text>"
   ```

2. **File-level review comment** (attached to a specific file and line in the diff):
   ```bash
   gh api --method POST "repos/<OWNER>/<REPO>/pulls/<NUMBER>/comments" \
     -f commit_id='<COMMIT_SHA>' \
     -f path='<FILE_PATH>' \
     -f body='<text>' \
     -F line=<LINE_NUMBER> \
     -f side='RIGHT'
   ```
   - `commit_id` -- the HEAD commit SHA of the PR (from `headRefOid`)
   - `line` -- the line number in the **diff**, not the absolute file line number
   - `side` -- use `RIGHT` for new/modified lines, `LEFT` for deleted lines

3. **Reply to an existing review comment thread** (REST API):
   ```bash
   gh api "repos/<OWNER>/<REPO>/pulls/<NUMBER>/comments" \
     -f body='<reply text>' \
     -F in_reply_to=<COMMENT_ID>
   ```
   - `in_reply_to` -- the numeric `id` of the top-level comment in the thread
   - This creates a reply within the existing thread, NOT a new top-level comment

4. **Reply to a review thread** (GraphQL -- preferred for precision):
   ```bash
   gh api graphql -f query='
   mutation {
     addPullRequestReviewThreadReply(input: {
       pullRequestReviewThreadId: "<THREAD_NODE_ID>"
       body: "<reply text>"
     }) {
       comment { id body }
     }
   }'
   ```
   - Uses the thread's GraphQL Node ID (from `reviewThreads` query) for precise targeting
   - Preferred over REST `in_reply_to` when you already have thread IDs from GraphQL

### Listing review comments

```bash
# List all review comments on a PR (paginated)
gh api repos/<OWNER>/<REPO>/pulls/<NUMBER>/comments --paginate
```

Each comment object contains:
- `id` -- numeric ID (used for `in_reply_to` in REST replies)
- `body` -- comment text
- `path` -- file path
- `line` / `original_line` -- line numbers
- `diff_hunk` -- surrounding diff context
- `user.login` -- author
- `in_reply_to_id` -- if set, this is a reply (not a top-level comment)

**Filtering**: Only process comments where `in_reply_to_id` is absent or null to get top-level review comments.

---

## 5. PR Reviews & Threads

### Fetching review thread status

```bash
gh api graphql -f query='
{
  repository(owner: "<OWNER>", name: "<REPO_NAME>") {
    pullRequest(number: <PR_NUMBER>) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes {
              databaseId
            }
          }
        }
      }
    }
  }
}'
```

- Match each thread's first comment `databaseId` to top-level comment IDs from the REST API
- Skip resolved threads (already addressed)
- The thread `id` is the GraphQL Node ID needed for mutations

### Resolving a review thread

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {
    threadId: "<THREAD_NODE_ID>"
  }) {
    thread { isResolved }
  }
}'
```

### Unresolving a review thread

```bash
gh api graphql -f query='
mutation {
  unresolveReviewThread(input: {
    threadId: "<THREAD_NODE_ID>"
  }) {
    thread { isResolved }
  }
}'
```

### Submitting a full review

```bash
gh api graphql -f query='
mutation {
  addPullRequestReview(input: {
    pullRequestId: "<PR_NODE_ID>"
    event: APPROVE
    body: "Looks good!"
  }) {
    pullRequestReview { id state }
  }
}'
```

Events: `APPROVE`, `REQUEST_CHANGES`, `COMMENT`

### Listing reviews on a PR

```bash
gh pr view <NUMBER> --json reviews
# or
gh api repos/<OWNER>/<REPO>/pulls/<NUMBER>/reviews
```

### Dismissing a review

```bash
gh api --method PUT repos/<OWNER>/<REPO>/pulls/<NUMBER>/reviews/<REVIEW_ID>/dismissals \
  -f message="<reason>"
```

---

## 6. Issues

```bash
# Create an issue
gh issue create --title "<title>" --body "<body>" --label "<label>"

# View an issue
gh issue view <NUMBER> --json title,body,state,labels,assignees

# List issues
gh issue list --json number,title,state,labels
gh issue list --label "<label>" --state open
gh issue list --assignee "<user>"

# Close an issue
gh issue close <NUMBER>

# Reopen an issue
gh issue reopen <NUMBER>

# Edit an issue
gh issue edit <NUMBER> --title "<new title>" --body "<new body>"
gh issue edit <NUMBER> --add-label "<label>"

# Add a comment to an issue
gh issue comment <NUMBER> --body "<text>"

# Transfer an issue
gh issue transfer <NUMBER> <destination-repo>

# Pin/unpin an issue
gh issue pin <NUMBER>
gh issue unpin <NUMBER>
```

---

## 7. Labels & Assignees

```bash
# List labels
gh label list --json name,description,color

# Create a label
gh label create "<name>" --color "<hex>" --description "<desc>"

# Delete a label
gh label delete "<name>" --yes

# Edit a label
gh label edit "<name>" --new-name "<new>" --color "<hex>"

# Assign users to an issue/PR
gh issue edit <NUMBER> --add-assignee "<user>"
gh pr edit <NUMBER> --add-assignee "<user>"
```

---

## 8. GitHub Actions

```bash
# List workflow runs
gh run list --json databaseId,status,conclusion,name,headBranch --limit 20

# View a specific run
gh run view <RUN_ID> --json status,conclusion,jobs

# View run logs
gh run view <RUN_ID> --log

# List workflows
gh workflow list --json id,name,state

# Trigger a workflow dispatch
gh workflow run <WORKFLOW_NAME_OR_ID> --ref <BRANCH>
gh workflow run <WORKFLOW_NAME_OR_ID> --ref <BRANCH> -f param1=value1

# Re-run a failed run
gh run rerun <RUN_ID>

# Re-run only failed jobs
gh run rerun <RUN_ID> --failed

# Cancel a run
gh run cancel <RUN_ID>

# Watch a run (blocks until complete)
gh run watch <RUN_ID>

# Download run artifacts
gh run download <RUN_ID>

# List run jobs
gh api repos/<OWNER>/<REPO>/actions/runs/<RUN_ID>/jobs --jq '.jobs[] | {name, status, conclusion}'

# Delete a workflow run
gh api --method DELETE repos/<OWNER>/<REPO>/actions/runs/<RUN_ID>
```

---

## 9. Releases

```bash
# List releases
gh release list --json tagName,name,isDraft,isPrerelease

# View a release
gh release view <TAG> --json tagName,name,body,assets

# Create a release
gh release create <TAG> --title "<title>" --notes "<body>"
gh release create <TAG> --generate-notes
gh release create <TAG> --draft

# Upload assets to a release
gh release upload <TAG> <file1> <file2>

# Delete a release
gh release delete <TAG> --yes

# Edit a release
gh release edit <TAG> --title "<new title>" --notes "<new body>"
```

---

## 10. Search

```bash
# Search repos
gh search repos "<query>" --owner <org> --json name,url --limit 50

# Search code
gh search code "<query>" --repo <owner/repo> --json path,repository

# Search issues/PRs
gh search issues "<query>" --repo <owner/repo> --json number,title,url
gh search prs "<query>" --repo <owner/repo> --state merged --json number,title

# Search commits
gh search commits "<query>" --repo <owner/repo> --json sha,message
```

---

## 11. Discussions

```bash
# List discussions
gh api graphql -f query='
{
  repository(owner: "<OWNER>", name: "<REPO>") {
    discussions(first: 20) {
      nodes { id number title author { login } }
    }
  }
}'

# Get a specific discussion
gh api graphql -f query='
{
  repository(owner: "<OWNER>", name: "<REPO>") {
    discussion(number: <NUMBER>) {
      id title body
      comments(first: 50) {
        nodes { id body author { login } }
      }
    }
  }
}'

# Add a discussion comment
gh api graphql -f query='
mutation {
  addDiscussionComment(input: {
    discussionId: "<DISCUSSION_NODE_ID>"
    body: "<text>"
  }) {
    comment { id body }
  }
}'
```

---

## 12. ProjectV2

```bash
# List org projects
gh api graphql -f query='
{
  organization(login: "<ORG>") {
    projectsV2(first: 20) {
      nodes { id title number }
    }
  }
}'

# Get project items
gh api graphql -f query='
{
  node(id: "<PROJECT_NODE_ID>") {
    ... on ProjectV2 {
      items(first: 50) {
        nodes {
          id
          content {
            ... on Issue { title number }
            ... on PullRequest { title number }
          }
        }
      }
    }
  }
}'

# Add an item to a project
gh api graphql -f query='
mutation {
  addProjectV2ItemById(input: {
    projectId: "<PROJECT_NODE_ID>"
    contentId: "<ISSUE_OR_PR_NODE_ID>"
  }) {
    item { id }
  }
}'
```

---

## 13. Gists

```bash
# List gists
gh gist list --json id,description,files,public

# View a gist
gh gist view <ID>

# Create a gist
gh gist create <file> --desc "<description>"
gh gist create <file> --public

# Edit a gist
gh gist edit <ID>

# Delete a gist
gh gist delete <ID>
```

---

## 14. Organizations & Users

```bash
# View org details
gh api orgs/<ORG> --jq '{login, description, repos_url}'

# List org members
gh api orgs/<ORG>/members --paginate --jq '.[].login'

# List org teams
gh api orgs/<ORG>/teams --paginate --jq '.[].slug'

# View user profile
gh api users/<USER> --jq '{login, name, email, bio}'
```

---

## 15. Secrets & Variables

```bash
# List repo secrets
gh secret list

# Set a repo secret
gh secret set <NAME> --body "<value>"
gh secret set <NAME> < secret-file.txt

# Delete a repo secret
gh secret delete <NAME>

# List repo variables
gh variable list

# Set a repo variable
gh variable set <NAME> --body "<value>"

# Delete a repo variable
gh variable delete <NAME>

# Environment secrets/variables
gh secret set <NAME> --env <ENVIRONMENT> --body "<value>"
gh variable set <NAME> --env <ENVIRONMENT> --body "<value>"
```

---

## 16. Actions Cache & Rulesets

### Actions Cache

```bash
# List caches
gh api repos/<OWNER>/<REPO>/actions/caches --jq '.actions_caches[] | {id, key, size_in_bytes}'

# Delete a cache by ID
gh api --method DELETE repos/<OWNER>/<REPO>/actions/caches/<CACHE_ID>

# Delete caches by key prefix
gh api --method DELETE "repos/<OWNER>/<REPO>/actions/caches?key=<PREFIX>"
```

### Rulesets

```bash
# List rulesets
gh api repos/<OWNER>/<REPO>/rulesets --jq '.[].name'

# Get a specific ruleset
gh api repos/<OWNER>/<REPO>/rulesets/<RULESET_ID>

# List org-level rulesets
gh api orgs/<ORG>/rulesets --jq '.[].name'
```

---

## 17. Raw GraphQL Passthrough

For any operation not covered above, use the raw GraphQL API:

```bash
# Query
gh api graphql -f query='
{
  <your GraphQL query here>
}'

# Mutation
gh api graphql -f query='
mutation {
  <your GraphQL mutation here>
}'

# With variables
gh api graphql \
  -f query='query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) { id nameWithOwner }
  }' \
  -f owner='<OWNER>' \
  -f name='<REPO>'
```

### Schema introspection

```bash
gh api graphql -f query='
{
  __schema {
    queryType { fields { name description } }
  }
}'
```

---

## Error Handling

When `gh` commands fail:

1. **Authentication errors** -- run `gh auth status` to check. If not authenticated, tell the user to run `gh auth login`
2. **404 Not Found** -- verify the repo name, owner, and that the user has access
3. **422 Unprocessable** -- check required fields; for PR comments, verify `commit_id`, `path`, and `line` are valid diff coordinates
4. **403 Forbidden** -- the user may lack permissions for the operation. Check repo access level
5. **Rate limiting** -- `gh` handles rate limiting automatically with retries, but for bulk operations consider pacing requests
6. **GraphQL errors** -- errors are returned in the `errors` array of the response. Check `errors[].message` for details. Common issues: invalid Node IDs, missing required fields, insufficient permissions

### Common pitfalls

- **PR comment line numbers** -- must be diff line numbers, not absolute file line numbers. Use `side='RIGHT'` for added/modified lines
- **GraphQL Node IDs** -- these are opaque base64 strings (e.g. `MDExOlB1bGxSZXF1ZXN0...`). They are NOT the same as numeric `databaseId` values. Use the correct ID type for each API
- **`--paginate`** -- REST list endpoints default to 30 results. Always use `--paginate` for endpoints that may return more than 30 items
- **Quoting** -- when passing complex bodies with special characters, use `"$(cat <<'EOF' ... EOF)"` syntax to avoid shell escaping issues
