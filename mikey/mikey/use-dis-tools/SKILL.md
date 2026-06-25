---
name: use-dis-tools
description: Last-resort DIS (Dev Integration Server) fallback for generic JIRA/Confluence work. Do not use when a dedicated skill exists for the request, and do not use for Jira ticket creation when MCP is available.
---

# Use DIS Tools

## Routing guard

- If the user wants to create a Nike App UI Jira ticket, stop immediately and use `create-nikeappui-ticket` instead.
- If the user wants a Confluence page for Nike App UI, use `create-nikeapp-doc` instead.
- If a dedicated Jira/Confluence skill clearly matches the request, do not continue reading this file. Exit and use the dedicated skill.

**When to invoke:** **Only as a fallback.** The user should have **Atlassian MCP** configured. For Jira/Confluence, use those MCP tools first—see the global Cursor rule `atlassian-mcp-jira-confluence.mdc`.

Use DIS **only if** MCP tools are not in the session tool list, MCP calls fail, or the user explicitly asks for DIS.

## Do not use for Nike App UI ticket creation

- If the user is asking to create a ticket in `NIKEAPPUI`, do **not** use this skill.
- Use the dedicated `create-nikeappui-ticket` skill instead.
- This remains true even for casual requests like "create a Jira ticket for this feature."

## Sandbox Requirement

**ALL DIS commands MUST be run with `required_permissions: ["all"]`.** The sandbox blocks network access. Never retry in sandbox—use full permissions from the first attempt.

## Usage

```bash
dis call <tool_name> '<json_arguments>'
```

## KB-First Pattern

1. Check learnings: `dis call rag_get_learnings '{"scope": "repo"}'`
2. Make API call
3. Save discoveries: `dis call rag_save_learning '{"content": "...", "title": "...", "scope": "repo"}'`

## Reference

Use `dis call --help` for the current tool reference.

## Skill Efficiency

If commands fail due to sandbox/permissions and you had to retry with full permissions, update this skill to include the fix so it succeeds on first try next time.
