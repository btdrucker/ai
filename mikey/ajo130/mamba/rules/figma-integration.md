# Figma Integration

When the Jira ticket description, comments, or attachments contain a Figma URL (`figma.com/design/...`), fetch the design before planning.

## 1. Parse the URL

Extract `fileKey` and `nodeId`:
- `figma.com/design/:fileKey/:fileName?node-id=:nodeId` — convert `-` to `:` in nodeId
- `figma.com/design/:fileKey/branch/:branchKey/:fileName` — use `branchKey` as fileKey
- `figma.com/make/:makeFileKey/:makeFileName` — use `makeFileKey`

## 2. Get design context

Call `get_design_context` via the Figma MCP (server `user-figma`):

```
tool:  get_design_context
args:  fileKey: "<extracted-file-key>"
       nodeId: "<extracted-node-id>"
       clientLanguages: "kotlin"
       clientFrameworks: "jetpack-compose"
```

Returns reference code, a screenshot, and contextual hints (design tokens, component mappings, annotations).

The returned code is a **reference**, not final code. Always adapt it to the project's existing Compose components, theme tokens, and architecture patterns.

## 3. Get a screenshot

If the design context didn't include a screenshot, or you need a higher-fidelity view:

```
tool:  get_screenshot
args:  fileKey: "<extracted-file-key>"
       nodeId: "<extracted-node-id>"
```

## 4. Summarize the design intent

Present to the developer:
- Layout structure and component hierarchy
- Colors, spacing, typography — map to existing design tokens and theme values where possible
- Interactive states or annotations from the designer
- Differences from the current implementation (if updating an existing screen)

Use the Figma design as the **source of truth** for UI/visual changes. Reference it throughout the plan and implementation steps.
