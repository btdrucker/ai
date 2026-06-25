---
name: git
description: >
  Git operations for Search Engineering workspace repos. Use when the user
  wants to commit and push, reset workspace, pull latest, create branches,
  check status, resolve merge conflicts, or manage workspace repo git state.
  Trigger phrases: "commit and push", "reset workspace", "pull latest",
  "switch branch", "clean up branches".
---

# Git Operations

Provides two workflows for managing git repos in the workspace.

## Workflow 1: Commit & Push

Stage all changes, generate a descriptive commit message, and push to the remote.

### Steps

1. **Identify the repo.** Determine which repo has uncommitted changes. If multiple repos have changes, process each one separately and confirm with the user before proceeding to the next.

2. **Gather context.** Run these in parallel:
   - `git status` to see all untracked and modified files
   - `git diff --staged` and `git diff` to see the actual changes
   - `git log --oneline -5` to see recent commit message style for this repo

3. **Draft the commit message.** Analyze all changes and write a commit message:
   - **First line**: imperative mood, concise summary of the "why" (not the "what"), no period at the end, under 72 characters. Match the style of recent commits in the repo.
   - **Body** (if needed): 1-3 lines explaining context that the diff alone doesn't convey. Separate from the first line with a blank line. Wrap at 72 characters.
   - Do NOT list files changed.
   - Use the correct category: "Add" for new features, "Update" for enhancements, "Fix" for bugs, "Remove" for deletions, "Refactor" for restructuring.

4. **Stage and commit.**
   ```bash
   git add -A
   git commit -m "$(cat <<'EOF'
   <commit message here>
   EOF
   )"
   ```

5. **Push.** Push to the remote. If the branch has no upstream, use `git push -u origin HEAD`.

6. **Report.** Show the commit hash and confirm the push succeeded.

### Guardrails

- Never force push
- Never amend commits that have been pushed
- If there are no changes to commit, say so and stop
- If push fails, report the error -- do not retry with force

---

## Workflow 2: Reset Workspace

Resets git repositories in the workspace to their default remote branches and pulls latest. By default operates on every repo in the workspace; optionally the user can choose specific ones.

### Step 1: Discover workspace repos

Read the `.code-workspace` JSON file to get the list of folders. Each folder entry has a `name` and `path`. Find the workspace file by searching for `*.code-workspace` in the workspace root.

Filter out any entry whose path is the workspace root itself (the meta-project that holds the workspace file) -- it is not a project repo. Also filter out any folder that is not a git repo (no `.git` directory) -- skip silently.

If the workspace registry (`workspace-registry.json` in the workspace directory) is available, only include repos with `role: "project"` by default. Tooling repos are read-only and should not be reset. Misc repos are personal/unmanaged and should not be touched by skills.

### Step 2: Let the user choose scope

If the user specified which repos to reset (by name, path, or partial match), use only those.

Otherwise, present the full list of discovered repos and confirm: "I'll reset all of these to their default branches and pull latest. Want to proceed, or pick specific ones?"

If the user picks specific repos, only operate on those.

### Step 3: Check for uncommitted changes

For each selected repo, run in parallel:

```bash
git -C <repo_path> status --porcelain
```

If any repo has uncommitted changes (tracked or untracked staged files), **stop before doing anything** and report:
- Which repos have issues
- What the changes are (modified files, untracked files)

Then ask the user how to handle each affected repo:
- **Stash** -- stash the changes and continue with reset
- **Skip** -- leave that repo alone entirely
- **Discard** -- throw away the changes
- **Commit** -- commit the changes using Workflow 1, then continue with reset

### Step 4: Determine default branch

For each selected repo, determine the default remote branch. First check the workspace registry: search the workspace for `*.code-workspace`, read its first folder entry (the workspace directory), and look for `workspace-registry.json` there. If the registry exists and has a `defaultBranch` entry for the repo, use it.

If the registry is not found or the repo is not in it, fall back to:

```bash
git -C <repo_path> remote show origin | grep 'HEAD branch' | awk '{print $NF}'
```

### Step 5: Reset and pull

For each selected repo, run in parallel:

```bash
git -C <repo_path> fetch origin
git -C <repo_path> checkout <default_branch>
git -C <repo_path> pull --ff-only
```

Run all repos in parallel for speed. Use `--ff-only` to avoid unexpected merge commits on diverged locals.

### Step 6: Report

Summarize results:
- Which repos were reset and to which branch
- Which repos were skipped and why
- Any errors encountered
