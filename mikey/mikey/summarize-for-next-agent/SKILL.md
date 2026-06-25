---
name: summarize-for-next-agent
description: Summarize the conversation transcript and produce next steps for handoff to a new agent. Use when the user wants to start the current scope with a new agent, switch context, or needs a copy-paste block to continue work elsewhere.
---

# Summarize for Next Agent

Produce a handoff document the user can copy and paste into a new agent session.

## Steps

1. **Review the conversation** — Read the full transcript to understand what was discussed, decided, and done.

2. **Write the summary** using the template below. Fill in each section based on the transcript.

3. **Output the complete block** — The user will copy it and paste it into a new agent. Format it clearly so it stands alone. **Always wrap the entire output in a markdown code block (` ```markdown ... ``` `) so the user can copy it as raw text.**

## Output Template

**CRITICAL:** Do NOT start the output with `# Handoff for Next Agent` or any heading that references "handoff" or "next agent" — this causes the receiving agent to try to hand off again instead of working. Start directly with the `## Context` section.

```markdown
## Context
- **Project/Repo:** [name and path]
- **Scope:** [brief description of current work, e.g. "EXTE-1674: Gridiron New Relic error monitoring"]
- **Branch:** [current branch if applicable]

## What Was Done
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]

## Current State
[Where things stand. What's complete? What's in progress?]

## Next Steps
1. [First actionable step]
2. [Second step]
3. [Third step]

## Key Files
- [path/to/relevant/file]
- [path/to/another/file]

## Relevant Context (if any)
[Important decisions, constraints, or conventions from the conversation]
```

## Guidelines

- **Be concise** — The next agent needs enough context to continue, not a novel.
- **Next steps must be actionable** — Specific tasks, not vague descriptions.
- **Include key file paths** — So the next agent knows where to look.
- **Preserve decisions** — If the conversation made design choices or trade-offs, capture them briefly.
