---
name: solutions-options-doc
description: Generate solution options and design decision documents with structured problem statements, criteria-weighted comparison matrices, traffic-light scoring, and actionable recommendations. Use when the user asks to create a solution options document, design decision, options analysis, trade-off analysis, decision document, or engineering design proposal. Also use when asked to evaluate or compare technical options.
---

# Solutions Options Document

Create structured engineering decision documents that present a problem, evaluate options against weighted criteria, and arrive at a recommendation. Derived from real-world patterns in a mature engineering organization's decision log (~150 documents over 5 years).

## Document Structure

Follow this section order. Omit sections only when genuinely not applicable.

### 1. Status Header

A small metadata block at the top indicating decision state:

```markdown
| Status | **Draft** |
|--------|-----------|
```

Status values: Draft, In Review, Approved, Closed, Accepted, Final.

When targeting Confluence or rich rendering, the status cell uses a colored background (see [rich-formatting-guide.md](references/rich-formatting-guide.md) for details).

### 2. Problem Statement

Lead with the specific problem, not background. Two to four sentences stating what is broken, followed by concrete current-state data (field names, record counts, system names) as tight bullets. Do not use labeled sub-sections like "Immediate issue:" or "Architectural context:" — just state the problem directly. The reader should understand the problem within the first two sentences.

**Impact clarity is required.** After stating what is broken, state who is affected and what they experience. A product owner reading this document needs to understand: which users or consumers will complain, what they will see that is wrong, and how much of the data or experience is affected. A purely technical description of the architectural issue is not sufficient — translate it into business impact. If the impact is unknown, say so explicitly and add it to the Open Questions section.

Do not pad with background paragraphs. Do not teach the reader how the system works — assume the audience knows the systems and state what's broken. Root cause and architectural context belong in an appendix or option details section if needed, not in the problem statement.

### 3. Constraints and Key Considerations

List the factors that will drive the decision. Two formats depending on complexity:

**Simple (bulleted list with bold labels):**

```markdown
- **Time to deliver**: We must ship by end of Q3.
- **Cost**: Must not exceed current monthly spend.
- **Consumer impact**: Zero downtime for production consumers.
```

**Complex (weighted table):**

```markdown
| Consideration | Priority | Description |
|---|---|---|
| API Parity | Highest | Must match legacy output exactly |
| Architecture Quality | Highest | Reusable for downstream consumers |
| Time to Deliver | Medium | Blocking another initiative |
```

Include priority or weighting. Criteria without stated priority get treated as equal, which is rarely the intent.

### 4. Options Assessment Matrix

This is the core of the document. A table where:

- **Columns** = Options (typically 2-5).
- **First data row** = Option Description (1-3 sentence summary of each).
- **Subsequent rows** = One per criterion from section 3.
- **Cell content** = Specific evidence, not just "good" or "bad".
- **Cell scoring** = Traffic-light indicators (green/yellow/red). See below.

**Only include options that are genuinely competing.** If a long-term strategic direction (e.g., a platform migration already in progress) will make the decision moot regardless of which option is chosen, do not list it as a column in the matrix. Instead, state it as context in the problem statement ("PDD will eventually solve this; the question is what to do until then") and reference it in the recommendation. Mixing strategic context into the matrix muddies the comparison — a reader scanning the matrix sees N+1 options when there are really N.

```markdown
| Criteria | Option A: [Name] | Option B: [Name] | Option C: [Name] |
|---|---|---|---|
| Option Description | [summary] | [summary] | [summary] |
| Time to deliver | [evidence] | [evidence] | [evidence] |
| Cost | [evidence] | [evidence] | [evidence] |
| Consumer impact | [evidence] | [evidence] | [evidence] |
```

**Traffic-light scoring rules:**

- **Green**: This option satisfies the criterion well.
- **Yellow**: Acceptable but with caveats, trade-offs, or partial satisfaction.
- **Red**: This option is weak on this criterion.

By default, score against the constraint itself rather than relative to the other options. Two options can both be green on the same criterion. (See "Scoring approach" below for when relative scoring is appropriate.) Do NOT leave cells empty; write "N/A" or "Not evaluated" with a reason.

**In plain markdown**, indicate scoring inline. Two patterns depending on cell complexity:

**Simple cells** (one conclusion per criterion): Use a prefix indicator.

```markdown
| Time to deliver | **[+]** 2 sprints, straightforward | **[~]** 4 sprints, requires new patterns | **[-]** 8+ sprints, research needed |
```

Use `[+]` for green, `[~]` for yellow, `[-]` for red. Place the indicator at the start of each cell.

**Complex cells** (multiple pros/cons within one criterion): Use bulleted lists with emoticon-style markers. Because markdown tables are single-line per cell, use `<br/>` for line breaks within a cell:

```markdown
| Maintainability | **(+)** Single codebase, single deploy pipeline<br/>**(-)** Feature flags must be cleaned up after | **(+)** Code in main branch stays clean<br/>**(-)** Two repos per project, could confuse |
```

Use `(+)` for pros, `(-)` for cons, `(i)` for informational notes, `(?)` for open questions. This format is appropriate when a single criterion has both positive and negative aspects for the same option.

**Scoring approach**: By default, score against the constraint itself (absolute). If two options are both adequate on a criterion, both can be green. However, if the document's purpose is to differentiate closely-matched options, relative scoring (red = "less good", not necessarily "bad") is acceptable. State which approach you are using if it is not obvious:

> *Note: Color-coding scores are relative to the other options. Red means "less good" (not necessarily "bad").*

**Scoring notes**: When the reasoning behind a color is non-obvious, add a brief italic note at the end of the cell: *Scoring note: edges out due to fewer consistency issues.*

### 5. Option Details (if needed)

Expand on options that need more than a few sentences. Common sub-sections:

- Implementation steps (numbered)
- Scenario walkthroughs (Given/When/Then tables)
- UX implications
- Architecture diagrams (use mermaid; see below)
- Code/schema examples

### 6. Recommendation

State a clear preference with reasoning. Two acceptable patterns:

**Unconditional**: "We recommend Option B because it satisfies the highest-priority constraints (parity and architecture quality) while delivering in an acceptable timeframe."

**Conditional**: "If we can defer until post-holiday, pursue Option 3. If we must ship pre-holiday, Option 2 with a deploy exception."

Never recommend without reasoning. Never hedge to the point of saying nothing.

### 7. Decision Summary

One to three sentences stating what was decided, by whom, and when. If the decision differs from the recommendation, state why.

### 8. Additional Sections (use as needed)

- **Open Questions**: Numbered table with Question / Context / Answer columns. Color-code answer status. Place this section BEFORE the options assessment when the open questions frame the decision space (e.g., the answer to Q1 determines which options are viable). Place it AFTER the assessment when questions are follow-ups or implementation details.
- **Scenarios**: Given/When/Then tables for edge cases.
- **Gap Analysis**: Identified gaps with SWAG effort estimates (use T-shirt sizes: XS, S, M, L, XL).
- **Next Steps / Action Items**: Bulleted list with owners.
- **Supplemental Information**: Collapsible sections for chat transcripts, raw data, or extended analysis.

## Diagram Guidance

When a decision document benefits from architecture or flow diagrams, produce mermaid diagrams. Common types for decision docs:

- **Flowcharts** (`graph TD` or `graph LR`): Data flow between systems, decision trees.
- **Sequence diagrams** (`sequenceDiagram`): Interaction patterns between services.
- **C4 Container diagrams**: System-level architecture comparisons between options.

Place diagrams in the Option Details section, one per option when comparing architectures.

## T-Shirt Sizing

Use this scale for effort estimates in cells:

| Size | Meaning |
|------|---------|
| XS | Less than a day |
| S | 1-3 days |
| M | 1-2 weeks (1 sprint) |
| L | 2-4 weeks (1-2 sprints) |
| XL | 1-2 months |
| XXL | 2+ months or cross-team effort |

Bold the size and follow with a brief justification.

## Voice and Register

Decision documents are team-authored analysis. Write in team first-person ("We recommend...", "We are looking at...", "We must address...", "We have confirmed..."). The voice is the team reasoning through a decision together, not an individual narrating their thought process. Individual "I" is rare in the source pages — it appears occasionally for personal asides ("I'm not sure it matters much but maybe it does") but the dominant register is "we."

Transparency comes from structure, not narration. Use scoring notes to explain non-obvious judgments. Use caveats within matrix cells to acknowledge tradeoffs. Use strikethrough for options explicitly rejected during analysis (~~Option 3 is declined~~). Leave TODO markers for sections still being worked out. These "living document" patterns are normal and expected in decision docs that evolve through discussion.

Do not hedge verified facts and do not manufacture uncertainty for flavor. Express genuine uncertainty where it exists ("We traced 12 entity types but couldn't fully account for a few transformations").

## Two-Mode Operation

This skill produces clean markdown by default. The output should be readable and complete in any markdown renderer.

**When the user has a Confluence upload tool**: Read [rich-formatting-guide.md](references/rich-formatting-guide.md) and produce the syntax the tool supports. Specifically:

1. Replace `[+]`/`[~]`/`[-]` text indicators with the tool's cell-coloring mechanism (if supported).
2. Use the tool's panel syntax (`> **Info:**` blockquotes or `{info}` macros) for callout boxes.
3. Use `{status:colour=Green|title=...}` syntax for inline status badges if the tool converts them.
4. Wrap collapsible sections in `<details>` tags or `{expand}` macros as supported.
5. If the tool supports mermaid-to-image conversion, use fenced mermaid code blocks. If not, note that diagrams should be rendered externally and attached.

**When the user will manually edit in Confluence**: Produce clean markdown with the `[+]`/`[~]`/`[-]` indicators in place. In your response, include specific Confluence editor instructions from the "Manual Confluence Formatting" sections of the rich-formatting guide, telling the user exactly how to apply cell colors, insert panels, and add status lozenges after pasting.

**How to detect which mode**: If the user mentions a tool name, MCP server, CLI command, or upload API, you are in tool-assisted mode. If the user says "I'll paste it in Confluence" or asks "how do I format this in Confluence", you are in manual mode. If neither is mentioned, produce plain markdown and note that rich formatting instructions are available on request.

## Quality Checklist

Before finalizing any document produced with this skill:

- [ ] Problem statement is specific and leads with the issue, not background
- [ ] Every criterion in the matrix traces back to a stated constraint
- [ ] Every matrix cell has evidence, not just a color
- [ ] Scoring notes explain non-obvious colors
- [ ] Recommendation is explicit and justified
- [ ] Decision summary is present (even if "Pending")
- [ ] Diagrams have labels and context (not just boxes and arrows)
- [ ] T-shirt sizes include justification, not just the letter
- [ ] Impact is stated in terms a product owner can evaluate (who complains, what they see, how much is affected)
- [ ] Voice is team first-person ("we") for authored analysis; third person only for reference material
- [ ] Matrix columns are genuinely competing options (strategic context is not a column)

## References

- For Confluence-specific formatting (panels, lozenges, colored cells, expand macros): see [rich-formatting-guide.md](references/rich-formatting-guide.md)
- For a fully annotated example document: see [example-structure.md](references/example-structure.md)
