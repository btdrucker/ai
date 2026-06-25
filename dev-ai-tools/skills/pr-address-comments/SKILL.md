---
name: pr-address-comments
description: Fetch, analyze, and address PR review comments. Use when the user wants to review PR comments, respond to feedback, address review comments, or handle PR review threads.
---

# Address PR Comments

## Related skills

- **`github`** -- GitHub operations gateway (MCP first, built-in second, CLI third)

> **GitHub operations:** Follow the `github` skill's integration policy.

Fetches review comments from a pull request, analyzes each for validity, presents recommendations, implements accepted changes, and replies directly to each comment thread.

## Workflow

### Step 1: Identify the PR

Determine which repo and PR to work with. If the user provides a PR number or URL, use that. Otherwise detect from the current branch:

```bash
git rev-parse --show-toplevel
```

Use the `github` **quick reference** in `SKILL.md` or **REFERENCE.md** S2-S3 for `gh repo view --json nameWithOwner` and `gh pr list --head <branch>`.

If no PR is found for the current branch, stop and tell the user.

### Step 2: Fetch review comments and thread status

Fetch all review comments using the `github` **quick reference** (`gh api repos/.../pulls/<N>/comments --paginate`).

Each comment object contains:
- `id` -- numeric ID used for `in_reply_to` when replying
- `body` -- the comment text
- `path` -- file path the comment is on
- `line` / `original_line` -- line number
- `diff_hunk` -- surrounding diff context
- `user.login` -- who left the comment (may be a bot like `Copilot`)
- `in_reply_to_id` -- if set, this comment is already a reply (skip it, it's not a top-level review comment)

**Filter out replies**: Only process comments where `in_reply_to_id` is absent or null. These are the original review comments. Comments with `in_reply_to_id` are responses already posted in the thread.

**Filter out resolved threads**: Fetch the review thread resolution status using **`github` REFERENCE.md S5** (GraphQL `reviewThreads` query).

Match each thread's first comment `databaseId` to the top-level comment IDs. **Skip any comment whose thread is already resolved** -- it has already been addressed in a prior run. Only process unresolved threads.

**Filter out already-replied threads**: Among the unresolved threads, check whether the authenticated user (from `gh api user --jq .login`) has already posted a reply. Scan the full comment list for replies (`in_reply_to_id` matching the top-level comment `id`) whose `user.login` matches the authenticated user. **Skip any unresolved thread that already has a reply from you** -- it was addressed in a prior run but left unresolved (typically because the thread author is a human reviewer). This prevents duplicate replies on subsequent runs.

### Step 3: Analyze each comment

For each top-level review comment:

1. Read the referenced file at the relevant lines to understand the current code
2. Understand what the reviewer is asking for
3. Assess validity:
   - **Already fixed** -- the issue was addressed in a subsequent commit
   - **Valid** -- the suggestion improves the code (correctness, performance, readability, style)
   - **Not applicable** -- the suggestion misunderstands the context, is out of scope, or would introduce regressions
   - **Nitpick** -- minor style preference with no functional impact

4. Formulate a recommended action:
   - **Fix** -- implement the change (or a variation of it)
   - **Dismiss** -- explain why it doesn't apply
   - **Defer** -- valid but out of scope for this PR

### Step 4: Present recommendations

Present ALL comments to the user in a numbered list with:
- The file and line reference
- A brief summary of what the reviewer asked for
- Your verdict (already fixed / valid / not applicable / nitpick)
- Your recommended action (fix / dismiss / defer)

Wait for the user to approve, modify, or reject recommendations before proceeding.

### Step 5: Implement accepted changes

For each comment the user accepts:

1. Make the code change
2. Run the appropriate linter/formatter if available (e.g. `./gradlew spotlessApply` or the project's format task)

Do NOT commit yet -- batch all changes into a single commit at the end.

### Step 6: Test and verify

After all code changes are made, run the project's test suite if available (e.g. `./gradlew test` for Gradle, `mvn test` for Maven). All tests must pass before committing. If anything fails, fix it before proceeding.

### Step 7: Commit and push

**This step MUST happen before replying to comments** so replies can reference the actual commit. If no code changes were made in Step 5, skip to Step 8.

If any code changes were made:

```bash
git add -A
git commit -m "<descriptive message about what the review feedback addressed>"
git push
```

Capture the commit hash from the push output -- use it when replying to fixed comments.

### Step 8: Reply to each unresolved comment thread

Reply to every **actionable** comment from Step 2 (not just the ones with code changes). Do NOT reply to:
- Threads that were already **resolved** -- they were handled in a prior run
- Threads where **you already posted a reply** -- they were addressed in a prior run but left unresolved (e.g. human reviewer threads)

Use the `github` **quick reference** (PR comments -- reply to an existing thread with `in_reply_to`).

**Reply guidelines**:
- **Fixed comments**: State what was changed and reference the commit hash (e.g. "Fixed in `abc1234` -- added null check in `processThread`")
- **Dismissed comments**: Explain why concisely -- don't be defensive, just factual
- **Already fixed comments**: Reference the commit that already addressed it
- **Deferred comments**: Acknowledge validity, state it's out of scope for this PR
- Keep replies under 2-3 sentences
- Don't use AI filler ("Great catch!", "Thanks for the feedback!")

**Important**: Reply to the specific comment thread using `in_reply_to`, do NOT create new top-level review comments or PR discussion comments.

### Step 9: Resolve comment threads

After replying, resolve addressed threads. Use the `user.login` and `user.type` fields from Step 2 to classify each comment author as **bot** or **human**.

A comment is from a bot if `user.type === "Bot"` or the login is a known bot (e.g. `Copilot`, `github-actions[bot]`).

**Bot threads**: Auto-resolve all unresolved bot threads that were addressed (fixed, dismissed, or already fixed) -- no user prompt needed.

**Human threads**: Collect the distinct human reviewer logins that have unresolved addressed threads. Present them to the user and ask which authors' threads should be auto-resolved. For example:

> The following non-bot reviewers have unresolved threads that were addressed:
> - `reviewer1_nike` (3 threads)
> - `reviewer2_nike` (1 thread)
>
> Should I auto-resolve threads from any of these reviewers, or leave them for the reviewer to resolve?

Wait for the user to respond. Only resolve threads from authors the user explicitly approves.

Use the thread resolution data already fetched in Step 2. For each approved thread, resolve it using **`github` REFERENCE.md S5** (GraphQL `resolveReviewThread` mutation with the thread Node ID).

Do **not** resolve:
- Threads from human reviewers the user did not approve
- Threads that were deferred (the reviewer may want to track those)

### Step 10: Offer to update the PR summary

If any code changes were made in Step 5, ask the user whether they'd like to update the PR description to reflect the new changes.

If yes:

1. Fetch the current PR body using the `github` **quick reference** or **REFERENCE.md** S3 (`gh pr view <N> --json body -q .body`)

2. Read the existing body carefully. **Preserve** any content that can't be regenerated:
   - Screenshots and screen recordings
   - Manually added notes, links, or context
   - Image/video markdown (`![...](...)`), HTML `<img>` / `<video>` tags, or GitHub asset URLs

3. Update the **Changes** section to incorporate what was done in response to review feedback. Do not remove or rewrite existing change entries -- append or amend them.

4. Push the update using the `github` **quick reference** (`gh pr edit <N> --body "..."`). Use the `$(cat <<'EOF' ... EOF)` pattern for multi-line bodies.

### Step 11: Report

Summarize what was done:
- How many comments were addressed
- How many resulted in code changes
- How many were dismissed/deferred and why
- Whether the PR summary was updated
- Link to the PR
