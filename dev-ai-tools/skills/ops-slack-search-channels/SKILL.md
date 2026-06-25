---
name: ops-slack-search-channels
description: >
  Search and browse Search Engineering Slack channels using the DIS MCP server.
  Use when the user wants to search Slack messages, read channel history, check
  deployments, review onboarding threads, or look up conversations in Search
  team channels. Trigger phrases: "search Slack", "check Slack", "Slack messages",
  "what's in #channel", "latest in Slack", "search channels".
---

# Search Engineering Slack Channels

Uses the `user-nike-dev-integration-system-mcp` MCP server (DIS).

## Related skills

- `dis` -- installation and configuration of the DIS MCP server (prerequisite)

## Prerequisites

The DIS MCP server must be running and Slack credentials must be configured.
If not, read and follow the `dis` skill first, specifically:
- `dis auth slack` to extract Chrome credentials
- `dis serve restart` to pick up new credentials

Verify by calling `slack_channels` with `{"query": "search"}` via the
`user-nike-dev-integration-system-mcp` MCP server. If it returns an error,
Slack is not configured.

---

## Channels

| Channel | Type |
|---------|------|
| `#core-search-onboarding` | Private |
| `#discover-search-support` | Public |
| `#hager-fte-all-new` | Private |
| `#nde-search-platform` | Private |
| `#search-platform-deployments` | Public |
| `#search-platform-squad` | Public |
| `#aiml-consumer-team` | Private |
| `#nde-search-monitoring` | Public |

---

## Workflow: Channel selection

If the user didn't name a channel, prompt them to select using `AskQuestion`:

```
AskQuestion:
  title: "Select Slack channels"
  questions:
    - id: channels
      prompt: "Which channel(s) do you want to search?"
      allow_multiple: true
      options:
        - id: core-search-onboarding
          label: "#core-search-onboarding"
        - id: discover-search-support
          label: "#discover-search-support"
        - id: hager-fte-all-new
          label: "#hager-fte-all-new"
        - id: nde-search-platform
          label: "#nde-search-platform"
        - id: search-platform-deployments
          label: "#search-platform-deployments"
        - id: search-platform-squad
          label: "#search-platform-squad"
        - id: aiml-consumer-team
          label: "#aiml-consumer-team"
        - id: nde-search-monitoring
          label: "#nde-search-monitoring"
```

If the user already named a channel in their request, skip the prompt and use
that channel directly.

---

## Workflow: Browse recent messages

Use `slack_history` to get recent messages from the selected channel(s).

```
CallMcpTool: server=user-nike-dev-integration-system-mcp, toolName=slack_history
arguments: {"channel": "#channel-name", "count": 20}
```

For a quick overview, use `summary: true` to show only the first line of each
message:

```
arguments: {"channel": "#channel-name", "count": 30, "summary": true}
```

For longer messages or threads, use `verbose: true` to double truncation limits.

If searching multiple channels, call `slack_history` for each in parallel.

---

## Workflow: Search messages by keyword

Use `slack_search` to find messages matching a keyword across channels.
This requires browser-session Slack credentials (`dis auth slack`).

```
CallMcpTool: server=user-nike-dev-integration-system-mcp, toolName=slack_search
arguments: {"query": "keyword in:#channel-name", "count": 10}
```

Slack search operators:
- `in:#channel-name` -- restrict to a specific channel
- `from:displayname` -- messages from a specific user
- `before:2026-06-01` / `after:2026-05-01` -- date range

Combine operators: `"deploy error in:#search-platform-deployments after:2026-06-01"`

---

## Workflow: Read a thread

When a message has replies (`thread_reply_count > 0`), use `slack_thread` to
get the full thread:

```
CallMcpTool: server=user-nike-dev-integration-system-mcp, toolName=slack_thread
arguments: {"channelId": "C0B3YRSH52P", "threadTs": "1780074180.198819"}
```

`channelId` is the channel ID (from the `slack_history` response) and
`threadTs` is the parent message timestamp.

---

## Workflow: Look up users

When messages show user IDs like `<@WE81N0GAV>`, resolve them to names:

```
CallMcpTool: server=user-nike-dev-integration-system-mcp, toolName=slack_user_info
arguments: {"userId": "WE81N0GAV"}
```

---

## Output

Resolve `<@USER_ID>` references to names via `slack_user_info`. Note threads
with reply counts so the user can ask to expand them.
