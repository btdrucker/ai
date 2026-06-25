---
name: confluence
description: >
  Confluence operations via the Atlassian MCP server -- fetch pages by ID or
  title, search with CQL, retrieve space content. Use when any task needs
  live Confluence page lookups or documentation searches. Default spaces:
  SENG (Search Engineering), DEN (Product Feeds API).
---

# Confluence

Patterns for Confluence operations. Prefer `user-atlassian-mcp-server`; fall
back to `user-nike-dev-integration-system-mcp` (DIS) if the Atlassian server
is unavailable or lacks the needed functionality.

## MCP Prerequisite

Before any Confluence call, verify the preferred server is available:

```
CallMcpTool(server: "user-atlassian-mcp-server", toolName: "jira_get_all_projects")
```

If the call fails with an auth error, run `mcp_auth` for
`user-atlassian-mcp-server`, then retry.

If the server is not found or not configured, fall back to DIS:

```
CallMcpTool(server: "user-nike-dev-integration-system-mcp", toolName: "confluence_list_spaces", arguments: {})
```

If DIS also fails, tell the user to install one of:
- Atlassian MCP: https://pulse.nike.com/mcp-server-registry/nike.mcpregistry%2Fatlassian-mcp-server
- DIS: read and follow the `dis` skill

**STOP** until one is available.

Tool names are the same across both servers for Confluence (`confluence_get_page`,
`confluence_search`, etc.). DIS also provides `confluence_create_page`,
`confluence_update_page`, `confluence_format_content`, and
`confluence_get_space_pages` which the Atlassian server may not have.

---

## Fetch a page

By page ID:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "confluence_get_page",
  arguments: {
    "page_id": "<ID>",
    "convert_to_markdown": true
  }
)
```

By title + space:

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "confluence_get_page",
  arguments: {
    "title": "<Page Title>",
    "space_key": "SENG",
    "convert_to_markdown": true
  }
)
```

Default spaces: `SENG` (Search Engineering), `DEN` (Product Feeds API).

## Search pages

```
CallMcpTool(
  server: "user-atlassian-mcp-server",
  toolName: "confluence_search",
  arguments: {
    "query": "<search text or CQL>",
    "spaces_filter": "SENG,DEN",
    "limit": 10
  }
)
```

CQL examples:

| Intent | Query |
|--------|-------|
| Pages mentioning a topic | `text ~ "kingpin" AND space = SENG` |
| Recently updated in space | `space = SENG AND lastModified >= now("-7d")` |
| Pages with a label | `label = "architecture" AND space = SENG` |

---

## Error Handling

| Error | Action |
|-------|--------|
| Server not found / connection refused | Guide user to install MCP server (see prerequisite above) |
| 401 / 403 / auth error | Run `mcp_auth` for `user-atlassian-mcp-server`, retry |
| 404 on page | Confirm the page ID or title with the user |
| Rate limited | Wait 30s, retry once. If still failing, inform the user. |
| Empty search results | Broaden the CQL query or ask the user for alternative terms |
