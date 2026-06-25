# Installation Guide

How to install rules and skills from this repo into your AI agent environment.

## Prerequisites

- An AI agent tool that supports the [agentskills.io](https://agentskills.io/) skill format (Cursor, Claude Code, Windsurf, and others)
- This repo cloned locally or accessible on GitHub

## Skills

Skills follow the [agentskills.io specification](https://agentskills.io/specification) and work with any compatible tool. Copy the skill directory to your tool's skills location:

| Tool | Skills location |
|------|----------------|
| Cursor | `~/.cursor/skills/` (user-level) or `.cursor/skills/` (project-level) |
| Claude Code | `~/.claude/skills/` (user-level) or `.claude/skills/` (project-level) |
| Codex | `~/.codex/skills/` (user-level) or `.codex/skills/` (project-level) |
| Any tool | `.agents/skills/` (project-level, cross-tool) |

```bash
# Example: install panel-review for Cursor
cp -r skills/panel-review ~/.cursor/skills/

# Example: install panel-review for Claude Code
cp -r skills/panel-review ~/.claude/skills/
```

After copying, restart or reload your tool. In Cursor, verify under Settings (Cmd+Shift+J) > Rules -- skills appear in the "Agent Decides" section. You can also invoke a skill manually by typing `/` and searching for the skill name.

## Rules

Rules are `.mdc` files with YAML frontmatter. The `.mdc` format is Cursor-specific. For other tools, the content can be adapted to the tool's rule format (e.g., CLAUDE.md sections, `.github/copilot-instructions.md`).

For Cursor, copy to `~/.cursor/rules/`:

```bash
cp rules/reasoning-discipline.mdc ~/.cursor/rules/
```

Rules with `alwaysApply: true` frontmatter activate on every conversation. Rules with `globs` activate only for matching files. Verify in Cursor Settings > Rules.

## Customization

Some artifacts have values you may want to adjust:

- **github-agent-disclaimer.mdc**: Replace `@{username}` with your GitHub login in the disclaimer template.
- **commit-message skill**: The skill encodes specific conventions (one commit per branch, NOJIRA prefix, Title Case subjects). Read the SKILL.md and decide which conventions match your workflow before installing.

## Uninstalling

Delete the file or directory from your tool's rules/skills location and restart.

## Troubleshooting

**Skill not discovered:**
- Check that the skill directory is directly inside the skills location (e.g., `~/.cursor/skills/panel-review/SKILL.md`, not nested deeper)
- Check that the `name` field in SKILL.md frontmatter matches the directory name exactly
- Restart your tool

**Rule not activating (Cursor):**
- Check that the file is in `~/.cursor/rules/` (not a subdirectory)
- Check that the file has YAML frontmatter with `alwaysApply: true` or a `description` field
- Restart Cursor
