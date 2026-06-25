---
name: create-nikeapp-doc
description: Create a Confluence page in the NDEE space for Nike App UI documentation. Search NDEE for related pages or parents before creating. Use when creating Nike App UI documentation.
---

# Create Nike App UI Confluence Doc

Create a Confluence page in the **NDEE** space for Nike App UI / Android engineering documentation.

## Tool preference

- Use the Atlassian MCP Confluence tools directly.
- Do not use `dis` unless MCP is unavailable.

## Defaults (discovered via MCP)

Load from script:

```bash
bash ~/.cursor/skills/create-nikeapp-doc/discover-nikeapp-confluence-space.sh
```

| Setting | Value |
|---------|-------|
| **Space key** | `NDEE` |
| **Default parent page** | `1760200073` — [Nike app overall flow](https://confluence.nike.com/pages/viewpage.action?pageId=1760200073) |
| **Alternate space** | `MOBILEC` — use `431703022` (Nike App Squad) for broader squad/release docs |

Only use personal space (`~mpinau`) if the user explicitly asks.

## Instructions

1. **Parse the user's request** for page title, content, parent override, child pages.

2. **Search NDEE before creating**:
   ```text
   confluence_search query="type=page AND space=NDEE AND text~\"<topic>\"" limit=10
   ```
   - Resolve parent from search when user references an existing doc loosely
   - Prefer updating or nesting under an existing page over duplicating

3. **Create the page** via `confluence_create_page`:
   - `spaceKey`: `NDEE` (or `MOBILEC` for squad-wide release/onboarding docs)
   - Parent: `1760200073` unless a better match was found

4. **Confirm** with page title and URL.

## Related NDEE pages

- [Slack Channels: Nike App](https://confluence.nike.com/pages/viewpage.action?pageId=1727442312) — `#nikeapp-ui-team` and support channels
- [Team Structure | Nike App + SNKRS](https://confluence.nike.com/pages/viewpage.action?pageId=1727435797) — Nike App UI (Mamba + Discover) squad info
- [Nike app overall flow](https://confluence.nike.com/pages/viewpage.action?pageId=1760200073) — Android/Mamba architecture overview

## Examples

User: "Create a doc about product wall carousel alignment"

→ Create in `NDEE` under Nike app overall flow or best matching parent.

User: "Document the 26.31 release"

→ Consider `MOBILEC` space under Nike App Squad or release pages.

User: "Put this doc in my personal space"

→ Create in `~mpinau` instead.
