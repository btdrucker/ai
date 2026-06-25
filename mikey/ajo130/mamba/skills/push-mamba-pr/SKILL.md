---
name: push-mamba-pr
description: Runs Mamba Android pre-push checks, then pushes and opens a PR only when green. Use when the user asks to push, open, prepare, or fix a Mamba Android PR.
---

# Push Mamba PR

From the Mamba Android repo or worktree root:

```bash
python3 scripts/agent-pr-push.py --create-pr
```

Read the JSON printed on stdout:

- `overall_success: true` -> report `pr_url`.
- `failed_tasks` non-empty -> run the first task's `rerun_command` verbatim, then rerun the push script. Repeat until green or until `next_action` says source edits are needed.
- `dirty_files` non-empty -> commit or discard them, then rerun.

Use `--full-pra` instead of the default flags when the user explicitly asks for a CI-equivalent run before pushing.

All script calls require `required_permissions: ["all"]`. The scripts set `GRADLE_USER_HOME` themselves.

## Safety

- Never run `./gradlew detektBaseline` or modify detekt baseline files.
- Do not add `@Suppress` annotations to silence detekt or lint failures.
- Do not pass `--no-verify` unless the user explicitly asks.
