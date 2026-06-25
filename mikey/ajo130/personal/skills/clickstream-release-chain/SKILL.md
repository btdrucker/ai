---
name: clickstream-release-chain
description: Prepare, raise, or update the recurring Android clickstream release PR chain across foundation, capability, Mamba Android, and Nike App Android. Use when the user asks to release clickstream definitions, bump clickstream foundation/capability versions, integrate them into Mamba, or update Nike App with Mamba/clickstream versions.
---

# Clickstream Release Chain

Use the release-chain script and runbook from the personal tooling repo.

## Required First Steps

1. Read `~/code/cursor-personal-tooling/scripts/clickstream_release_chain.agent.md`.
2. Inspect script help:

```bash
~/code/cursor-personal-tooling/scripts/clickstream_release_chain.py --help
~/code/cursor-personal-tooling/scripts/clickstream_release_chain.py raise --help
```

3. Confirm current versions from the four repos before raising PRs:

- `~/code/mpe.foundation.clickstream`
- `~/code/mpe.capability.clickstream`
- `~/code/mpe.app.mamba-android`
- `~/code/mpe.app.nikeapp-android`

## Use The Script

Prefer the script over manual edits:

```bash
~/code/cursor-personal-tooling/scripts/clickstream_release_chain.py prepare
~/code/cursor-personal-tooling/scripts/clickstream_release_chain.py raise
~/code/cursor-personal-tooling/scripts/clickstream_release_chain.py update-artifacts
```

Pass explicit versions when known. Leave Mamba as the script's placeholder only when the Mamba Android integration artifact has not published yet.

## Guardrails

- Use git worktrees only; do not disturb active user branches.
- Use fresh date-stamped branch names.
- Prefer `gh` for PR creation and updates.
- Push release-chain branches with `--no-verify` unless the user explicitly asks for pre-push checks.
- Do not run full builds unless the user asks.
- After compile PRs merge, ensure the foundation release PR moves compile release notes out of `Unreleased` and into the version section while keeping scaffold headers.
- Report all PR URLs and any remaining placeholders.
