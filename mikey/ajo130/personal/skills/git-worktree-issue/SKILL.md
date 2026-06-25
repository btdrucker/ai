---
name: git-worktree-issue
description: >-
  Creates or reuses a git worktree for a branch, associates work with a ticket/issue id,
  opens that folder in Cursor, and follows up with commit/PR-oriented reminders. Use when
  the user gives a branch name plus an issue (e.g. MMBA-1763), asks for a parallel checkout,
  or says worktree / second clone / open branch in new window.
---

# Git worktree + issue workflow

## What this skill does (for the user)

1. **Ensures** a second directory exists with the **right branch** checked out (or creates it from `origin`).
2. **Opens** that directory in Cursor so work happens in isolation from other branches.
3. **Keeps** the issue id handy for branch names, commits, and PR titles—without requiring repo file changes unless the user asks.

The remote does not see “worktrees”; **pushing from that folder is the same** as pushing from the main clone.

---

## Optional: set your defaults (edit this skill)

If the user’s layout is stable, fill these once so the agent stops asking:

| Placeholder | Example |
|---------------|---------|
| `CODE_ROOT` | `/Users/ajo130/code` |
| Default remote | `origin` |
| Default base for **new** branches | `origin/main` (or `origin/master` if that is default) |

If unset, infer from the current workspace path.

---

## How worktrees work (minimal)

- One `.git` database, **many** working directories; each directory = one checked-out branch.
- **List / remove** from any linked clone: `git worktree list`, `git worktree remove <path>` (run from primary clone is clearest).

---

## Inputs

| Input | Agent uses it for |
|-------|-------------------|
| **Branch** | Checkout target; may be `ajo/TICKET-foo` or `feature/x`. |
| **Issue id** | Commit prefixes (`TICKET-123: …`), PR title, chat context; optional folder suffix for uniqueness. |

**Folder naming** (pick one pattern and stick to it):

- `{repo-dir}--{sanitized-branch}` e.g. `mpe.app.mamba-android--ajo-MMBA-1763`
- Or include issue: `{repo-dir}--{issue}` when branch name is long or ambiguous.

Sanitize branch for paths: replace `/` with `-`, drop characters unsafe in paths.

---

## Branch resolution (decision order)

Run from **primary clone** path `<repo>` (not inside another worktree unless intentional).

1. `git -C <repo> fetch <remote>` (default `origin`).

2. **Does local branch exist?**  
   `git -C <repo> show-ref --verify --quiet refs/heads/<branch>`  
   - Yes → go to “Create or reuse worktree” with `<branch>`.

3. **Does `origin/<branch>` exist?**  
   `git -C <repo> show-ref --verify --quiet refs/remotes/origin/<branch>`  
   - Yes → add worktree with tracking:  
     `git -C <repo> worktree add --track -b <branch> <path> origin/<branch>`  
     (Or create local branch first—both are fine; `worktree add --track -b` is one step.)

4. **User wants a brand-new branch** (not on remote yet):  
   `git -C <repo> worktree add -b <branch> <path> <base>`  
   Default `<base>`: `origin/main`; if missing, try `origin/master` or ask.

5. **If `git worktree add` fails** with *branch already checked out*:  
   Another worktree (or the main clone) already has that branch. **Do not force.**  
   - `git -C <repo> worktree list` → tell user the path already using that branch, or  
   - Use a different branch name, or remove the other worktree if obsolete (`git worktree remove`).

---

## Create or reuse worktree

1. Compute `<path>` (sibling to `<repo>`, never nested inside another worktree).

2. **If `<path>` exists:**  
   - `git -C <path> rev-parse --is-inside-work-tree` and `git -C <path> branch --show-current`  
   - Same repo + same branch → **reuse**, open Cursor, done.  
   - Same repo + different branch → **do not overwrite**; new path suffix (e.g. `-2`) or ask.  
   - Not a git worktree / wrong repo → **pick new path**, do not delete without confirmation.

3. **If `<path>` does not exist:** use “Branch resolution” above, then `git worktree add …`.

---

## Open in Cursor

1. `cursor <path>` if CLI is available; else macOS: `open -a "Cursor" <path>`.  
2. If neither works: instruct **File → Open Folder** to `<path>`.  
3. Tell the user to start a **new chat** in that window with branch + issue so context is clean.

---

## After the folder is open (remind the user)

- **First commit**: include issue id in message if team convention requires it.  
- **Push**: `git push -u origin <branch>` from the worktree (same as normal clone).  
- **PR**: title often `TICKET-123: short description`; base branch per team (`main` / `develop`).

---

## Commands reference

```bash
git -C <repo> fetch origin
git -C <repo> worktree list

# Local branch already exists
git -C <repo> worktree add <path> <branch>

# Branch only on remote (common)
git -C <repo> worktree add --track -b <branch> <path> origin/<branch>

# New branch from base
git -C <repo> worktree add -b <branch> <path> origin/main

# Done with this checkout
git -C <repo> worktree remove <path>
```

---

## Optional local issue marker

Only if the user explicitly wants a file in the worktree:

```bash
echo "MMBA-1763" > <path>/.worktree-issue
```

Prefer **gitignored** local notes; avoid committing noise unless the team wants it.

---

## Anti-patterns

- No worktrees **inside** another worktree’s tree.  
- No `rm -rf` on a worktree path without `git worktree remove` (or `prune` after cleanup).  
- No duplicate add of the same branch without resolving “already checked out” first.
