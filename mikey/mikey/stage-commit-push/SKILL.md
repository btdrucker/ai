---
name: stage-commit-push
description: Runs Android/Gradle checks, stages, commits with TICKET-KEY format, background-pushes with hook monitoring, and conditionally creates PRs. Use when staging, committing, and pushing Nike App Android work. Never uses --no-verify.
---

# Stage, Commit, Push

## Rules

- **Never use `--no-verify`** — fix hook failures via `pre-push-fix.sh` and retry
- **Ticket key in commits**: ALWAYS uppercase (`NIKEAPPUI-237: Description`)
- **Commit scope only** — never reference PR comments in commit messages
- **Pre-push hooks are slow** — background the push and wait for completion notification

## Scripts

| Script | Purpose |
|--------|---------|
| `discover-commit-style.sh` | Infer commit format from repo history |
| `pre-push-fix.sh` | Auto-fix spotless / dependency sort failures |
| `push-with-hooks.sh` | Push with logged output for monitoring |

All scripts live in `~/.cursor/skills/stage-commit-push/`.

---

## Stage 1: Pre-commit (repo-aware)

Detect repo type from directory name or `./gradlew` / `./local-checks.sh`:

### Nike App Android (`mpe.app.nikeapp-android`)

```bash
./gradlew test --daemon
./gradlew detekt --daemon
./gradlew spotlessCheck --daemon
```

Run module-scoped tests when changes are limited to one module.

### Mamba Android (`mpe.app.mamba-android`)

Prefer fast local checks before full PRA:

```bash
./local-checks.sh --prepush    # ~30s: spotless, detekt, apiCheck
```

For broader validation when requested:

```bash
./local-checks.sh --pra        # full PRA simulation (~15min)
```

### Product Wall (`mpe.feature.productwall`)

```bash
cd Android && ./gradlew test detekt spotlessCheck --daemon
```

Adjust path if working from repo root.

If any step fails, fix and re-run. Do not proceed until green.

---

## Stage 2: OpenSpec Archive Check (conditional)

Run `openspec list --json 2>/dev/null`. If active changes exist → follow `openspec-archive-check` skill.

---

## Stage 3: Stage

```bash
git add <paths>
git status
```

Stage only what belongs in this commit.

---

## Stage 4: Commit Message Format

Run:

```bash
bash ~/.cursor/skills/stage-commit-push/discover-commit-style.sh [TICKET-KEY]
```

For Nike App repos the dominant format is **ticket**:

```
NIKEAPPUI-237: Align product wall carousel thumbnails
```

- Ticket key: **ALWAYS uppercase**
- Derive ticket key from branch name (`mpinau/NIKEAPPUI-237/...`) if not provided
- Describe only what staged files change

After commit, check `git status`. If hooks modified files:

```bash
git add -u
git commit --amend --no-edit
```

Repeat until clean.

---

## Stage 5: Push (background + notify)

Pre-push hooks run Gradle checks and can take several minutes. **Do not block the agent session waiting inline.**

1. Run push in background with full permissions:

```bash
bash ~/.cursor/skills/stage-commit-push/push-with-hooks.sh
```

Use Shell tool with:
- `required_permissions: ["all"]`
- `block_until_ms: 0` (background immediately)
- `notify_on_output`: pattern `"PUSH_SUCCEEDED|PUSH_FAILED|hook.*FAILED|error:|rejected"`, reason `"Push hook result"`

2. **On `PUSH_SUCCEEDED`**: proceed to Stage 6
3. **On `PUSH_FAILED`**:
   - Read log at `/tmp/push-with-hooks-<branch>.log`
   - Run `bash ~/.cursor/skills/stage-commit-push/pre-push-fix.sh`
   - If fix produced changes: stage, amend, background push again
   - If detekt/apiCheck failures remain: fix code manually, then retry

4. If push hook modified files (spotlessApply on nikeapp):
   ```bash
   git add -u
   git commit --amend --no-edit
   bash ~/.cursor/skills/stage-commit-push/push-with-hooks.sh
   ```

---

## Stage 6: Create or Update PR (conditional)

```bash
gh pr view --json url -q '.url' 2>/dev/null
```

If PR needed → follow `create-or-update-pr` skill.

---

## Stage 7: Respond to PR Comments (conditional)

Only if user asked → follow `respond-to-pr-comments` skill.

---

## Summary Checklist

- [ ] Tests / detekt / spotless passed locally
- [ ] OpenSpec archived if complete
- [ ] Files staged
- [ ] Commit uses `TICKET-KEY: Description` (uppercase key)
- [ ] `git status` clean after commit
- [ ] Push backgrounded and completed successfully
- [ ] PR created or updated (if applicable)
- [ ] PR comments replied to (if applicable)
