# Context File Research

What makes AGENTS.md, CLAUDE.md, .cursorrules, and .mdc files effective -- and what makes them counterproductive. Based on Gloaguen et al. (2026) and practical findings from auditing 83 agentic files across 12 repositories.

## The Core Finding

Gloaguen et al. found that context files (AGENTS.md, CLAUDE.md, .cursorrules) can **reduce** agent task success rates when they restate information the agent could discover on its own. The mechanism: unnecessary requirements increase inference cost by ~20% while adding marginal benefit. Worse, they can introduce conflicting guidance that the agent must reconcile mid-task.

The practical implication: every line in a context file should save more agent inference cost than it adds. If the agent can find the answer in three tool calls with unambiguous results, the context file line is a net cost.

## What Belongs in Context Files

**High-value content** (saves significant inference, hard to discover):

- Cross-repo context: what systems are upstream/downstream, what shared infrastructure exists, how this repo fits into a larger architecture
- Institutional judgment: when two valid approaches exist, which one this project prefers and why
- Domain terminology: enterprise acronyms and project-specific jargon that an agent cannot resolve from code alone
- Gotchas that are invisible in any single file but obvious across 5-10: the conventions an agent will violate without guidance

**Medium-value content** (saves some inference, somewhat discoverable):

- Directory maps with architectural annotations (not just `ls` output, but what each area is for and how they relate)
- Build/test/deploy commands that have non-obvious prerequisites or ordering
- Navigation shortcuts: "the entry point for X is in Y" when X is not named obviously

**Low-value content** (the agent can discover this cheaply):

- Tech stack declarations (visible in package.json, pom.xml, build.gradle)
- File structure listings (one `ls -R` or glob search away)
- Standard commands (npm install, mvn test) without project-specific nuance
- Content that duplicates README.md

## What Hurts

- **Restating discoverable information:** The biggest offender. Listing every file in the repo, declaring the tech stack, or restating what README.md already says. These lines inflate the context window and provide no value over what the agent's tools can find.
- **Stale state information:** Specific values, current bugs, behaviors that could change. If it needs updating when the code changes and nobody will remember to update it, it will mislead.
- **Negative instructions without structural fixes:** "Don't do X" places X in the agent's attention (the Pink Elephant Problem). Prefer positive framing or, better, fix the codebase so X is not possible (rename the confusing thing, delete the legacy code, add a linter rule).
- **Monolithic files mixing concerns:** A 260-line file containing project context, coding style, commit conventions, architecture principles, and development methodology forces every agent interaction to load all of it. Modular files with appropriate scoping (alwaysApply, globs) let the agent load only what is relevant.

## Practical Guidelines

1. **Write only what the agent cannot discover on its own.** The golden rule from [reizam/claude-md-templates](https://github.com/reizam/claude-md-templates). If it is in package.json, the agent can read package.json.
2. **Target 60-100 lines for AGENTS.md.** This covers repo identity, directory map, toolchain commands, navigation shortcuts, and gotchas. Earn additional lines through genuine complexity (domain terminology, cross-repo context, non-obvious conventions). Hard ceiling: 150 lines.
3. **Use the 6-month test.** For each line: will this still be true in 6 months without anyone updating it? If not, remove it, generalize it, or point to a file that stays current.
4. **Prefer pointers over content.** "See `docs/adr/` for architecture decisions" is better than summarizing every ADR in the context file.
5. **Test with quiz agents.** The create-agents-md skill uses readonly subagents that answer questions using only the AGENTS.md. If they cannot answer navigation and domain questions, the file has gaps. If they can answer questions about things that are easily grep-able, the file has excess.

## Sources

- Gloaguen, R. et al. (2026). "[Evaluating the Impact of Repository-Level Context Files on AI Agent Performance](https://arxiv.org/abs/2602.11988)." arXiv:2602.11988.
- [reizam/claude-md-templates](https://github.com/reizam/claude-md-templates): Global vs project scope separation for CLAUDE.md files
- [mgechev/skills-best-practices](https://github.com/mgechev/skills-best-practices): Progressive disclosure and context efficiency for agent skills
- Internal audit of 83 agentic files across 12 Nike repositories (March 2026)

