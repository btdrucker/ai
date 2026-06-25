# ocpp-ai-tools

Curated collection of agent rules and skills used across the OCPP team. Browse, pick what fits, and copy it into your environment.

## Catalog

### Rules

Rules are `.mdc` files with YAML frontmatter. Install by copying to your agent tool's rules directory (e.g., `~/.cursor/rules/`).

| Name | Category | Description |
|------|----------|-------------|
| [reasoning-discipline](rules/reasoning-discipline.mdc) | Universal | Tradeoff disclosure, factual verification, scope discipline, earned confidence |
| [minimal-comments](rules/minimal-comments.mdc) | Convention | Self-documenting code over narrating comments; comment only non-obvious "why" |
| [github-agent-disclaimer](rules/github-agent-disclaimer.mdc) | Convention | Require AI attribution line on GitHub comments posted by agents |

### Skills

Skills are portable packages that teach agents domain-specific workflows. Each follows the [agentskills.io specification](https://agentskills.io/specification) and works with any compatible tool (Cursor, Claude Code, Windsurf, and others). Install by copying the skill directory to your tool's skills location (e.g., `~/.cursor/skills/`, `~/.claude/skills/`).

| Name | Description |
|------|-------------|
| [aws-asg-optimizer](skills/aws-asg-optimizer/) | Analyze AWS Auto Scaling Group metrics and recommend optimal min/max values; not for non-EC2 workloads |
| [commit-message](skills/commit-message/) | Ticket-prefixed, functional-area commit messages with a one-commit-per-branch discipline |
| [create-agents-md](skills/create-agents-md/) | Generate minimal, high-signal AGENTS.md files through deep discovery and quiz-based self-critique |
| [panel-review](skills/panel-review/) | Adversarial expert panel review that iterates critique rounds until quality converges |
| [solutions-options-doc](skills/solutions-options-doc/) | Structured decision documents with weighted comparison matrices and traffic-light scoring |
| [humanize-text](skills/humanize-text/) | Identify and remove AI-generated writing patterns from text |

## Categories

**Universal** rules improve agent reasoning regardless of your team's style preferences. They address how agents think and verify -- tradeoff disclosure, factual claims backed by inspection. Hard to argue against.

**Convention** rules encode specific style choices that reasonable engineers could disagree on. Adopt them if they match your team's preferences; skip them if they don't.

**Skills** are inherently opinionated -- they define a specific methodology for a specific task. Read the SKILL.md to decide if the methodology fits your workflow.

## Installation

See [docs/installation.md](docs/installation.md) for step-by-step instructions covering Cursor, Claude Code, and other tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for what belongs in this repo, how to add artifacts, and the quality bar.

## Documentation

| Document | Purpose |
|----------|---------|
| [Installation Guide](docs/installation.md) | How to install rules and skills from this repo |
| [Evaluation Rubric](docs/evaluation-rubric.md) | Team rubric for scoring agentic files (1-5 scale) |
| [Context File Research](docs/context-file-research.md) | What makes context files effective (Gloaguen et al. findings) |
