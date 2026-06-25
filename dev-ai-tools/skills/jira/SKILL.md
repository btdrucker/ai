---
name: jira
description: >
  Jira operations via the Atlassian MCP server -- fetch issues, search with
  JQL, get sprint boards and issues, transition tickets, add comments. Use
  when any task needs live Jira data, story lookups, ticket transitions, or
  sprint planning. Default project: SRPLT.
---

# Jira

Patterns for Jira operations. Prefer `user-atlassian-mcp-server`; fall back
to `user-nike-dev-integration-system-mcp` (DIS) if the Atlassian server is
unavailable or lacks the needed functionality.

## MCP Prerequisite

Before any Jira call, verify the preferred server is available:

```
CallMcpTool(server: "user-atlassian-mcp-server", toolName: "jira_get_all_projects")
```

If the call fails with an auth error, run `mcp_auth` for
`user-atlassian-mcp-server`, then retry.

If the server is not found or not configured, fall back to DIS:

```
CallMcpTool(server: "user-nike-dev-integration-system-mcp", toolName: "jira_list_projects", arguments: {})
```

If DIS also fails, tell the user to install one of:
- Atlassian MCP: https://pulse.nike.com/mcp-server-registry/nike.mcpregistry%2Fatlassian-mcp-server
- DIS: read and follow the `dis` skill

**STOP** until one is available.

### Tool name mapping

When using DIS instead of the Atlassian server, tool names differ:

| Atlassian MCP | DIS |
|---------------|-----|
| `jira_get_issue` | `jira_get_ticket` |
| `jira_create_issue` | `jira_create_ticket` |
| `jira_transition_issue` | `jira_transition_ticket` |
| `jira_get_all_projects` | `jira_list_projects` |
| `jira_get_agile_boards` | `jira_list_boards` |
| `jira_get_sprints_from_board` | `jira_get_sprints` |
| `jira_get_sprint_issues` | `jira_search` (use JQL with sprint filter) |

DIS also provides tools not in the Atlassian server: `jira_clone_ticket`,
`jira_link_tickets`, `jira_get_velocity`, `jira_get_editable_fields`,
`jira_add_attachment`.

---

## Fetch a story

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_get_issue",
  arguments: { "issue_key": "<KEY>" }
)
```

Key fields to extract:

| Field | Path | Notes |
|-------|------|-------|
| Summary | `summary` | Short title |
| Description | `description` | Full body (may contain AC) |
| Status | `status.name` | Current workflow state |
| Assignee | `assignee.displayName` | |
| Labels | `labels` | Array of strings |
| Epic link | `customfield_10008` or `epic` | Varies by Jira instance |
| Story points | `customfield_10004` or `story_points` | Varies by Jira instance |
| Sprint | `sprint.name` | Active sprint if any |

## Search stories (JQL)

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_search",
  arguments: {
    "jql": "<JQL>",
    "fields": "summary,status,assignee,labels",
    "limit": 20
  }
)
```

Useful JQL patterns (default project: `SRPLT`):

| Intent | JQL |
|--------|-----|
| Open stories in current sprint | `project = SRPLT AND sprint in openSprints() AND issuetype = Story AND status != Done` |
| Stories in an epic | `project = SRPLT AND "Epic Link" = <EPIC-KEY>` |
| Recently updated | `project = SRPLT AND updated >= -7d ORDER BY updated DESC` |
| By assignee | `project = SRPLT AND assignee = "<name>" AND status != Done` |
| By label | `project = SRPLT AND labels = "<label>"` |
| Text search | `project = SRPLT AND text ~ "<search term>"` |

## Get sprint issues

First find the board and active sprint:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_get_agile_boards",
  arguments: { "project_key": "SRPLT" }
)
```

Then get the active sprint:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_get_sprints_from_board",
  arguments: { "board_id": <board_id>, "state": "active" }
)
```

Then fetch issues:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_get_sprint_issues",
  arguments: { "sprint_id": <sprint_id> }
)
```

## Add a comment

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_add_comment",
  arguments: {
    "issue_key": "<KEY>",
    "comment": "<comment body>"
  }
)
```

## Transition a ticket

First get available transitions for the issue:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_get_transitions",
  arguments: { "issue_key": "<KEY>" }
)
```

Then transition using the target transition ID:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "jira_transition_issue",
  arguments: {
    "issue_key": "<KEY>",
    "transition_id": "<ID>"
  }
)
```

Common transitions for SRPLT stories: "In Progress", "In Review", "Done".
Always fetch transitions first -- IDs vary by project and workflow.

---

## Error Handling

| Error | Action |
|-------|--------|
| Server not found / connection refused | Guide user to install MCP server (see prerequisite above) |
| 401 / 403 / auth error | Run `mcp_auth` for `user-atlassian-mcp-server`, retry |
| 404 on issue | Confirm the issue key with the user |
| Rate limited | Wait 30s, retry once. If still failing, inform the user. |
| Empty search results | Broaden the JQL query or ask the user for alternative terms |
