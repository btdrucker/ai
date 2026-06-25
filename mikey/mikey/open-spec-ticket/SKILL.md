---
name: open-spec-ticket
description: Start OpenSpec proposal workflow from a NIKEAPPUI (or other) Jira ticket. Fetches ticket details, validates against codebase, checks out mpinau/<TICKET-KEY>/<slug>, then runs OpenSpec propose. Use when the user provides a Jira ticket for Nike App UI implementation planning.
---

# Open Spec Ticket

Kick off an OpenSpec change scoped to a Jira ticket: fetch the ticket, validate it against the codebase, branch, then propose.

## Tool preference

- Use the Atlassian MCP server JIRA tools directly for ticket reads and updates.
- Do not use `dis` for this skill.

## Steps

### 1. Fetch ticket info

Use Atlassian MCP `jira_get_issue` (e.g. `NIKEAPPUI-237`).

Extract: title, description, acceptance criteria. Ticket key must be **uppercase**.

### 2. Validate ticket against the codebase

Before proceeding, cross-reference the ticket with the actual codebase. This step **must** complete before branching or proposing.

**What to check:**

- **Referenced code exists:** Search for files, modules, functions, classes, or config referenced in the ticket.
- **Scope alignment:** Confirm described areas match where logic actually lives.
- **Missing acceptance criteria:** Flag vague or missing criteria.
- **Missing context or ambiguity:** Flag references to missing integrations, feature flags, or config.
- **Downstream impact:** Identify consumers, tests, or dependents not mentioned in the ticket.

**If gaps are found, STOP and report them to the user before continuing.**

Wait for user confirmation before moving to step 3.

### 2b. Update the Jira ticket (if scope changed)

If the user confirms scope differs from the ticket, update via `jira_update_issue` **before** branching or proposing.

If the user chose to proceed as-is, skip this step.

### 3. Checkout branch

Use the checkout script (syncs main and creates branch):

```bash
bash ~/.cursor/skills/checkout-ticket-branch/checkout-ticket-branch.sh NIKEAPPUI-237 scope-from-ticket-title
```

Branch naming:
- `mpinau/<TICKET-KEY>` or `mpinau/<TICKET-KEY>/<slug>`
- Ticket key: **ALWAYS uppercase**
- Slug: lowercase kebab-case from ticket title (3–5 words)

Example: `mpinau/NIKEAPPUI-237/product-wall-carousel`

### 4. Run OpenSpec propose

Follow the `openspec-propose` skill exactly:

1. Derive kebab-case change name from ticket title
2. `openspec new change "<name>"`
3. `openspec status --change "<name>" --json`
4. Loop: `openspec instructions <artifact-id> --change "<name>" --json` → write artifact → repeat until all `applyRequires` artifacts are done
5. `openspec status --change "<name>"`

Use ticket title, description, acceptance criteria, and codebase validation findings as sources.

## Stop After Propose

**ALWAYS stop after the propose step is complete and wait for user confirmation before proceeding to implement.**

Summarize:
- Ticket fetched
- Codebase validation completed
- Branch checked out (`mpinau/<TICKET-KEY>/...`)
- Change name and artifacts created
- Ask: "Does this proposal look aligned? Confirm to proceed to implementation."
