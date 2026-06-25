---
name: mamba-qa-ready
description: Move a Nike App UI or Mamba ticket to QA with TestFairy link. Adds "Test ready!" comment, transitions to QA, and unassigns. Accepts NIKEAPPUI, MMBA, and other ticket keys (always uppercase). Use when Jenkins build is complete and ticket is ready for QA.
---

# Mamba QA Ready

Move a ticket to QA by adding a "Test ready!" comment with build links, transitioning to QA status, and unassigning.

## Tool preference

1. **Atlassian MCP** for `jira_get_transitions` (discover QA transition ID)
2. **Script** for comment + transition + unassign execution

## Quick Start

### Step 1 — Discover QA transition (MCP)

```text
jira_get_transitions issue_key=NIKEAPPUI-237
```

Find transition named `QA` (or closest match). Note the transition `id`.

For **NIKEAPPUI** tickets, QA transition is typically **id 61** (`QA`) — confirmed via MCP on `NIKEAPPUI-127`. Still verify with `jira_get_transitions` before transitioning.

```bash
bash ~/.cursor/skills/mamba-qa-ready/discover-qa-transition.sh NIKEAPPUI-237
```

### Step 2 — Run script

```bash
bash ~/.cursor/skills/mamba-qa-ready/mamba-qa-ready.sh NIKEAPPUI-237 "https://nike.testfairy.com/join/..." [TRANSITION_ID] [MAMBA_PR_URL] [NIKEAPP_BRANCH_URL]
```

Examples:

```bash
bash ~/.cursor/skills/mamba-qa-ready/mamba-qa-ready.sh NIKEAPPUI-237 "https://nike.testfairy.com/join/NikeApp-Android-Feature-World?id=51863" 61
bash ~/.cursor/skills/mamba-qa-ready/mamba-qa-ready.sh NIKEAPPUI-237 "https://nike.testfairy.com/join/NikeApp-Android-Feature-World?id=51863" 61 "https://github.com/nike-internal/mpe.app.mamba-android/pull/456" "https://github.com/nike-internal/mpe.app.nikeapp-android/tree/feature/mamba-snapshot-NIKEAPPUI-237"
```

If script exits with `TRANSITION_REQUIRED` (exit code 2), complete Step 1 and re-run with transition ID.

## Parameters

| Parameter | Required | Default | Example |
|-----------|----------|---------|---------|
| TICKET_KEY | Yes | — | `NIKEAPPUI-237` (always uppercased) |
| TESTFAIRY_LINK | Yes | — | `https://nike.testfairy.com/join/...` |
| TRANSITION_ID | No* | Discover via MCP | `61` |
| MAMBA_PR_URL | No | omitted from comment | `https://github.com/.../pull/456` |
| NIKEAPP_BRANCH_URL | No | omitted from comment | `https://github.com/.../tree/feature/...` |

*Required for transition; script adds comment first even without it.

## Comment Format

```
Test ready!

build here ->
NikeApp-Android-Feature-World
<TESTFAIRY_LINK>

PR -> <MAMBA_PR_URL>

nike app branch used for testing -> <NIKEAPP_BRANCH_URL>
```

The PR and branch lines are only included if provided. No one is tagged — QA picks up tickets by checking the QA column.

## Workflow

1. Add "Test ready!" comment with TestFairy link (and optional PR/branch links)
2. Transition ticket to QA
3. Unassign ticket (so QA can self-assign)

## Requirements

- `bash`, `jq`, `dis` CLI (Jira API fallback)
- Atlassian MCP for transition discovery

## Notes

- Accepts any ticket project (`NIKEAPPUI`, `MMBA`, etc.)
- Ticket key is always uppercased by the script
- Do not hardcode transition ID 61 — discover per ticket/workflow
- No one is tagged in the comment — QA team picks up from QA column
- TestFairy link is provided by the user or extracted from Jenkins build
