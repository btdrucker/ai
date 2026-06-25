---
name: openspec-archive-check
description: Check for completed OpenSpec changes and optionally archive them before committing. Use when an OpenSpec change may be complete and should be archived as part of the current commit.
---

# OpenSpec Archive Check

Check whether there is an active OpenSpec change that should be archived as part of a commit.

## Steps

### 1. Check if openspec CLI is available

```bash
openspec list --json 2>/dev/null
```

If `openspec` is not installed or there are no active changes, return immediately — nothing to do.

### 2. Check if any active changes are complete

```bash
openspec status --change "<name>" --json
```

A change is ready to archive when `"isComplete": true` and all tasks in `tasks.md` are checked (`- [x]`).

### 3. Ask before archiving

If a change is complete, use the **AskQuestion tool** to ask:

> "OpenSpec change `<name>` is complete. Archive it before committing?"

- **Yes** → run `openspec archive --yes "<name>"`, then return the list of files produced so they can be included in the upcoming commit (do NOT create a separate commit for the archive)
- **No** → skip and return

### 4. Never block the commit

Do not block the calling workflow if the user says no or if no changes are complete — return normally so the parent skill can proceed.
