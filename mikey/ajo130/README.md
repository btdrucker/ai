# ajo130 — Cursor skills, rules, and scripts snapshot

Immutable snapshot of custom Cursor agent tooling, collected 2026-05-29 (updated 2026-06-11 with Mamba Nike App integration skills).

## Sources scanned

| Location | Contents |
|----------|----------|
| `~/.cursor/skills` | Personal skills (2) |
| `~/.cursor/rules` | Personal rules (1) |
| `mpe.app.mamba-android/.cursor/skills` | Project skills (7; no `bmad-*`) |
| `mpe.app.mamba-android/.cursor/rules` | Project rules (10) |
| `mpe.app.mamba-android/scripts/` | Agent PR + worktree scripts (4) |
| `mpe.app.mamba-android/` (root) | `local-checks.sh`, `pre-validation.sh` |

Excluded: `~/.cursor/skills-cursor` (Cursor built-ins), all `bmad-*` skills.

## Layout

```
raw/ajo130/
├── personal/
│   ├── skills/          # 2 Cursor skills
│   └── rules/           # 1 global rule
├── mamba/
│   ├── skills/          # 7 Cursor skills
│   ├── rules/           # 10 project rules
│   └── scripts/         # 6 automation files
└── README.md
```

## Skills (9)

| Skill | Path |
|-------|------|
| clickstream-release-chain | `personal/skills/` |
| git-worktree-issue | `personal/skills/` |
| build-install-mamba | `mamba/skills/` |
| enforce-compose-state-callback-contract | `mamba/skills/` (+ `examples.md`) |
| push-mamba-pr | `mamba/skills/` |
| test-in-nikeapp | `mamba/skills/` |
| mamba-qa-ready | `mamba/skills/` |
| release-mamba | `mamba/skills/` |
| credentials-doctor | `mamba/skills/` |

## Rules (11)

| Rule | Path | alwaysApply |
|------|------|-------------|
| shell-command-playbook | `personal/rules/` | true |
| mamba-release-skills | `mamba/rules/` | true |
| gradle-agent-cache | `mamba/rules/` | true |
| pra-fix | `mamba/rules/` | false |
| fix-jira-ticket | `mamba/rules/` | false |
| build-quality | `mamba/rules/` | globs `*.kt` |
| architecture-guide | `mamba/rules/` | — |
| development-patterns | `mamba/rules/` | — |
| product-requirements | `mamba/rules/` | — |
| figma-integration | `mamba/rules/` | — |
| debug-shop-content | `mamba/rules/` | false |

## Scripts (6)

| Script | Used by |
|--------|---------|
| `setup-worktree.sh` | fix-jira-ticket rule |
| `local-checks.sh` | pra-fix, gradle-agent-cache rules |
| `pre-validation.sh` | build-quality rule (git hook) |
| `agent-pr-push.py` | push-mamba-pr skill |
| `agent-rerun-failed-task.py` | push-mamba-pr retry flow |
| `agent_pr_common.py` | shared by agent PR scripts |
