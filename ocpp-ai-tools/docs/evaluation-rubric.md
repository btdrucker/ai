# Evaluation Rubric

A rubric for assessing the quality of agentic files -- rules, skills, AGENTS.md, and other agent configuration. Developed through scoring 83 files across 12 repositories during an internal audit.

This is a team-developed rubric, not an industry standard. Use it to evaluate your own artifacts before sharing and to provide structured feedback during reviews.

## Scoring Scale

| Score | Label | Criteria |
|-------|-------|----------|
| 5 | Gem | Minimal, focused, correctly placed. Does one thing well. Proper frontmatter or spec compliance. No unnecessary content. Would improve any agent's behavior if installed. |
| 4 | Solid | Good practices, minor issues. May be slightly verbose, have one unclear section, or miss an edge case. Works well in practice. |
| 3 | Functional | Works but has clear issues. May be too long, mix multiple concerns, use outdated conventions, or sit in a non-standard location. Needs editing before sharing. |
| 2 | Cruft | Outdated, misplaced, or violates current practices. Legacy format (bare .md instead of .mdc with frontmatter), superseded by a newer version, or unreferenced by anything. Candidates for deletion or migration. |
| 1 | Anti-pattern | Misleading or fundamentally wrong. Boilerplate with zero project context, duplicated content that will drift, or guidance that actively confuses agents. Delete or replace. |

## What Each Score Looks Like

### Score 5 -- Gem

- Single responsibility: the file addresses one concern
- Correct placement: `.cursor/rules/` for scoped rules, `~/.cursor/rules/` for global rules, skill directories matching the agentskills.io spec
- Proper metadata: YAML frontmatter with `description`, appropriate `alwaysApply`/`globs` for rules; `name` and `description` for skills
- Content passes the Gloaguen test: every line saves more agent inference cost than it adds (see [context-file-research.md](context-file-research.md))
- No content an agent could discover in three tool calls with unambiguous results

### Score 4 -- Solid

- Meets all Score 5 criteria with minor exceptions
- May have a section that could be tightened or an example that could be more concrete
- Works reliably in practice even if not perfectly minimal

### Score 3 -- Functional

- Works but would benefit from editing
- Common issues: over 500 lines, mixes behavioral rules with project context, uses an older format, has vague examples, or lacks frontmatter
- Worth keeping and improving, not worth sharing as-is

### Score 2 -- Cruft

- Superseded by a newer artifact or approach
- Uses a format agents cannot auto-discover (bare `.md` in `.cursor/` instead of `.mdc` with frontmatter)
- Duplicates content available elsewhere
- Confuses the question of "which guidance is authoritative?"

### Score 1 -- Anti-pattern

- Generic boilerplate with no project-specific value
- Identical content in multiple repos (will drift)
- Actively misleading (suggests agent support that does not exist, or encodes incorrect conventions)

## Using the Rubric

**Before adding to this repo:** Does the artifact score 4 or above? If not, improve it first.

**During review:** Score the artifact, cite which criteria it meets or misses, and suggest specific fixes for anything below 4.

**For your own repos:** Use this rubric to audit existing `.cursorrules`, `.cursor/rules/`, AGENTS.md, and skill files. The audit that produced this rubric found that 76% of mature artifacts scored 4-5, while legacy artifacts from the earliest adoption period (Oct-Nov 2025) clustered at 1-2.
