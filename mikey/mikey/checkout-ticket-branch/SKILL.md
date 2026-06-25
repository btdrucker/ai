---
name: checkout-ticket-branch
description: >-
  Syncs main, then creates mpinau/<TICKET-KEY> or mpinau/<TICKET-KEY>/<slug> from a Jira ticket key (always uppercase). Defaults to NIKEAPPUI tickets. Use when branching from main for Nike App UI work.
---

# Checkout Ticket Branch From Main

End state: **default branch is up to date** and a **new branch** exists as `mpinau/<TICKET-KEY>` or `mpinau/<TICKET-KEY>/<slug>`.

## Prerequisites

- **Ticket key** (e.g. `NIKEAPPUI-237`) — default project is NIKEAPPUI; accept any key the user provides
- Optional **kebab slug** from the ticket title

## Quick Start

Run the script from the target repo root:

```bash
bash ~/.cursor/skills/checkout-ticket-branch/checkout-ticket-branch.sh NIKEAPPUI-237
bash ~/.cursor/skills/checkout-ticket-branch/checkout-ticket-branch.sh NIKEAPPUI-237 product-wall-carousel
```

The script:
1. Uppercases the ticket key (always ALL CAPS)
2. Fetches and syncs the default branch (`main` or `master`)
3. Stashes dirty work if needed, then restores after branch creation
4. Creates `mpinau/<TICKET-KEY>` or `mpinau/<TICKET-KEY>/<slug>`

## Branch Naming

| Input | Branch |
|-------|--------|
| `NIKEAPPUI-237` | `mpinau/NIKEAPPUI-237` |
| `NIKEAPPUI-237` + slug `product-wall-carousel` | `mpinau/NIKEAPPUI-237/product-wall-carousel` |

- **Ticket key**: ALWAYS uppercase (`NIKEAPPUI-237`, not `nikeappui-237`)
- **Slug**: lowercase kebab-case, optional
- **Prefix**: `mpinau` (override with `BRANCH_PREFIX` env var)

## When NOT to use

- User wants a branch **from current HEAD** without syncing default branch → confirm first
- Not a git repo / no `origin` → abort clearly

## Confirm

Report:
- Default branch synced
- New branch name
- `git status` output
- Whether stash was used and restored
