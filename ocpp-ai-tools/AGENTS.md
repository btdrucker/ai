# AGENTS.md

## Purpose

This repo is a **source catalog** of agent rules and skills for Nike's OCPP team. Teammates browse artifacts here and copy them into their own environment (`~/.cursor/`, `~/.claude/`, etc.). Nothing in `rules/` or `skills/` auto-loads into any agent -- those directories are for browsing.

The `.cursor/` directory at the repo root IS project-level config for agents working on this repo itself.

See [README.md](README.md) for the catalog and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution mechanics.

## How Artifacts Relate

- `README.md` is the catalog -- every artifact needs a row in the appropriate table.
- `CONTRIBUTING.md` defines what belongs (cross-project, zero-modification) and what does not (personal, credential-dependent, project-specific).
- `docs/evaluation-rubric.md` is the quality gate -- artifacts must score 4+ before merging.
- `docs/context-file-research.md` explains the Gloaguen principle that governs content density.

When you add or rename an artifact, update the README catalog table. When you change quality criteria, update both CONTRIBUTING.md and the rubric.

## Quality Standards

All artifacts in this repo must:

1. Score 4+ on the [evaluation rubric](docs/evaluation-rubric.md)
2. Be self-contained -- an agent must be able to follow the artifact without external context
3. Include when NOT to use (skills) or clear scope (rules)
4. Contain no secrets, credential paths, or environment-specific assumptions beyond "you work at Nike"

Skills must follow the [agentskills.io specification](https://agentskills.io/specification). Rules must have YAML frontmatter with `description` and either `alwaysApply: true` or `globs`.

## What Not To Do

- Do not restate discoverable information in any artifact.
- Do not add project-specific rules to `rules/` -- those belong in the project's own config.
- Do not add boilerplate comments. The minimal-comments rule in this repo applies to the repo's own prose.
- Do not bulk-list files in AGENTS.md, README, or skills. Agents can `ls`.

## Editing Conventions

- Rule filenames: lowercase-hyphenated, `.mdc` extension.
- Skill directory names: lowercase-hyphenated, 1-64 chars, letters/numbers/hyphens only.
- Prose and examples should be concrete, not generic placeholders.
- When editing a SKILL.md, preserve the YAML frontmatter. The `name` field is load-bearing.
