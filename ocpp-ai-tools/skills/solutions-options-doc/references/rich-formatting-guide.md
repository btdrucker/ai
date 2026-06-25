# Rich Formatting Guide for Decision Documents

This reference covers formatting beyond vanilla markdown for rendering decision documents in Confluence or similar rich-text platforms. It addresses two scenarios: tool-assisted upload and manual editing.

## Traffic-Light Cell Colors

The options assessment matrix uses background colors on table cells to signal positive, neutral, and negative scoring. These are the standard Confluence color tokens observed across mature decision logs:

| Score | Hex Code | Confluence Name | Markdown Indicator |
|-------|----------|-----------------|-------------------|
| Positive (green) | `#e3fcef` | Light green 35% | `[+]` |
| Neutral (yellow) | `#fffae6` | Light yellow 35% | `[~]` |
| Negative (red) | `#ffebe6` | Light red 35% | `[-]` |
| Strong negative | `#ffbdad` | Light red 100% | `[-]` (bold) |
| Neutral (grey) | `#f4f5f7` | Light grey 100% | (no indicator) |

In Confluence storage format, a colored cell looks like:

```html
<td class="highlight-#e3fcef" data-highlight-colour="#e3fcef">Cell content here</td>
```

## Status Header Colors

The status metadata table at the top of the document uses colored backgrounds to indicate decision state:

| Status | Background | Text Color |
|--------|-----------|------------|
| Draft | `#ff8b00` (orange) | White |
| In Review | `#fffae6` (light yellow) | Default |
| Approved | `#36b37e` (medium green) | White |
| Accepted | `#57d9a3` (medium green 65%) | Default |
| Closed | `#b3d4ff` (light blue) | Orange accent |
| Final | `#36b37e` (medium green) | White |

## Confluence Panel Macros

Panels are colored callout boxes used for orientation, warnings, and context.

| Panel Type | Color | When to Use |
|-----------|-------|-------------|
| Info | Blue | Context or background the reader may need |
| Tip | Green | Best practices or recommended approaches |
| Note | Yellow | Caveats, expected behaviors, things to keep in mind |
| Warning | Red | Blockers, critical issues, things requiring immediate action |

### Tool-Assisted Syntax

If the upload tool supports blockquote-to-panel conversion:

```markdown
> **Info:** This creates a blue info panel with the given content.

> **Warning:** This creates a red warning panel.
```

If the upload tool supports wiki macro syntax:

```markdown
{info:title=Context}
Panel content here.
{info}
```

### Manual Confluence Formatting

In the Confluence editor:

1. Type `/info` (or `/note`, `/warning`, `/tip`) and press Enter.
2. A colored panel macro appears. Type your content inside it.
3. To change the panel type, click the macro and select from the dropdown.

## Status Lozenges

Colored badges for inline status indicators (project state, task completion, etc.).

### Tool-Assisted Syntax

```markdown
{status:colour=Green|title=On Track}
{status:colour=Yellow|title=In Progress}
{status:colour=Red|title=Blocked}
{status:colour=Blue|title=In Review}
{status:colour=Grey|title=Not Started}
```

Supported colors: Green, Red, Yellow, Blue, Grey. The `subtle=true` parameter produces an outline style instead of a filled badge.

### Manual Confluence Formatting

1. Type `/status` and press Enter.
2. Select a color and type the label text.
3. Click outside the lozenge to place it.

## Expand/Collapse Sections

Collapsible sections keep the document scannable by hiding extended analysis, supplemental data, and historical context behind a click.

Common uses in decision docs:

- Option detail deep-dives
- Scratch/brainstorming areas
- Chat transcripts and supplemental conversations
- Historical code traces

### Tool-Assisted Syntax

Using HTML5 details tags (works in GitHub and converts to Confluence expand macros):

```markdown
<details>
<summary>Click to expand: Implementation Details</summary>

Full markdown content here, including lists, tables, code blocks.

</details>
```

Using wiki macro syntax:

```markdown
{expand:title=Click to expand: Implementation Details}
Content here.
{expand}
```

### Manual Confluence Formatting

1. Type `/expand` and press Enter.
2. Set the title text (what appears when collapsed).
3. Type content inside the expand region.

## Emoticon-Style Indicators

Confluence documents frequently use inline emoticons for pros/cons lists and callout markers. In plain markdown, use text equivalents:

| Confluence Emoticon | Plain Markdown | Usage |
|----|----|----|
| `(+)` (green plus) | **[+]** or **(+)** | Pro / positive point |
| `(-)` (red minus) | **[-]** or **(-)** | Con / negative point |
| `(i)` (blue info) | **(i)** | Informational note |
| `(?)` (yellow question) | **(?)** | Open question or uncertainty |
| `(!)` (orange warning) | **(!)** | Warning or caution |
| `(/)` (green check) | **(check)** | Confirmed / verified |
| `(x)` (red cross) | **(x)** | Rejected / declined |

Example in a pros/cons list within a table cell:

```markdown
- **(+)** Deploy to commerce is straightforward
- **(+)** No consideration needed for keeping old code working
- **(-)** Two repos per project could be confusing
```

### Tool-Assisted Syntax

If the upload tool preserves Confluence emoticon macros, these render as colored icons:

```html
<ac:emoticon ac:name="plus" />
<ac:emoticon ac:name="minus" />
<ac:emoticon ac:name="information" />
```

### Manual Confluence Formatting

In the Confluence editor, type the emoticon shortcut (e.g., `(+)`, `(-)`, `(i)`, `(?)`, `(!)`) and it will auto-convert to the colored icon.

## Colored Table Cell Backgrounds

For the options assessment matrix, each criteria cell should have a background color matching its traffic-light score.

### Manual Confluence Formatting

1. Click inside the table cell.
2. Open the cell properties (right-click > Cell properties, or use the toolbar).
3. Set the "Cell background color" using one of the standard hex codes listed above.
4. Repeat for each scored cell.

**Tip**: Use the Confluence color picker's "recently used" section after setting the first few cells to speed up the process.

### Tool-Assisted Approach

Most markdown-to-Confluence converters do NOT support cell background colors from plain markdown. If your tool does not, the traffic-light colors must be applied manually after upload. The `[+]`, `[~]`, `[-]` text indicators serve as a guide for which color to apply to each cell.

If the tool supports raw Confluence storage format passthrough, cells can be written as:

```html
<td class="highlight-#e3fcef" data-highlight-colour="#e3fcef">
  <p>Cell content here</p>
</td>
```

## Mermaid Diagrams as LucidChart Replacements

Decision documents in Confluence commonly use embedded LucidChart diagrams for data flow, architecture comparison, and status workflows. When producing documents outside of Confluence (or without a LucidChart license), use mermaid diagrams instead.

Common diagram types for decision docs:

| Confluence Pattern | Mermaid Equivalent |
|---|---|
| System data flow diagram | `graph LR` or `graph TD` flowchart |
| Service interaction sequence | `sequenceDiagram` |
| Status/state workflow | `stateDiagram-v2` |
| Architecture overview (C4-style) | `graph TD` with subgraphs for containers |

### Manual Confluence Formatting

Confluence does not natively render mermaid. Options:

1. **Render locally and attach as image**: Use a local mermaid renderer (mermaid CLI, VS Code preview, or mermaid.live) to generate a PNG/SVG. Attach to the Confluence page and insert as an image.
2. **Mermaid macro plugin**: Some Confluence instances have a mermaid macro plugin installed. Check by typing `/mermaid` in the editor.
3. **Paste as code block**: If no renderer is available, paste the mermaid source in a code block labeled "mermaid" so a future reader or tool can render it.

## Styled Div Callouts

Some decision documents use colored background divs for important callout blocks (distinct from panels).

### Manual Confluence Formatting

1. Type `/panel` or use the macro browser to insert a "Panel" macro.
2. Set the background color in the macro parameters.
3. Common patterns: `background:beige` for worksheet notices, `background:azure` for explanatory blocks.

## Code Blocks

Technical decision docs often include JSON schema examples, API shapes, or configuration snippets.

### Tool-Assisted Syntax

Standard fenced code blocks with language tags:

````markdown
```json
{
  "status": "ACTIVE",
  "statusModifier": "CLOSEOUT"
}
```
````

### Manual Confluence Formatting

1. Type `/code` or `{code}` and press Enter.
2. Select the language from the dropdown.
3. Paste code content.
4. Optionally set a title and collapse behavior in the macro parameters.

## Task Lists / Action Items

Decision documents often close with action items assigned to specific people.

In markdown:

```markdown
- [ ] Action: @person will investigate Option 2 feasibility by Friday
- [x] Action: @person confirmed API parity requirements
```

### Manual Confluence Formatting

1. Type `[]` at the start of a line to create a task checkbox.
2. Use `@mention` to assign the task to a person.
