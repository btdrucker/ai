---
name: sync-team-repos
description: Clone any team repos that don't have a local copy. Use when the user asks to clone, sync, or set up local copies of team repositories.
disable-model-invocation: true
---

# Sync Team Repos

Ensures all team repos listed in `~/.cursor/data/team-repos.json` have local clones.

## First-time setup

Make the scripts executable (one-time):
```bash
chmod +x ~/.cursor/skills/sync-team-repos/scripts/clone-missing.sh
chmod +x ~/.cursor/skills/sync-team-repos/scripts/pull-latest.sh
chmod +x ~/.cursor/skills/sync-team-repos/scripts/add-autolinks.sh
```

## Scripts

### clone-missing.sh

Clones repos that don't have a local copy yet. Silent if all repos already exist.

```bash
# Dry run
~/.cursor/skills/sync-team-repos/scripts/clone-missing.sh --dry-run

# Clone all missing
~/.cursor/skills/sync-team-repos/scripts/clone-missing.sh
```

### pull-latest.sh

Fetches and pulls all repos in parallel. Prints a status table when done.

- Clones any still-missing repos first (serial)
- Fetches + pulls all repos in parallel
- Pulls only if on default branch and clean
- Skips with explanation if on a feature branch or dirty

```bash
# Dry run
~/.cursor/skills/sync-team-repos/scripts/pull-latest.sh --dry-run

# Pull latest everywhere
~/.cursor/skills/sync-team-repos/scripts/pull-latest.sh
```

**Example output:**
```
REPO                                          BRANCH               STATUS
----                                          ------               ------
mpe.feature.pdp                               main                 ✅ main (+3 commits)
mpe.capability.product                        main                 — up to date (main)
mpe.app.mamba-android                         feat/new-screen      ⏭️  feat/new-screen (2 commits behind main)
mpe.component.banner                          main                 ⚠️  dirty: main (uncommitted changes)
```

### add-autolinks.sh

Adds three Jira autolink references to every repo in the list. Idempotent — safely skips any that already exist.

| Prefix | URL |
|---|---|
| `NIKEAPPUI-` | `https://jira.nike.com/browse/NIKEAPPUI-<num>` |
| `NIKEAPCORE-` | `https://jira.nike.com/browse/NIKEAPCORE-<num>` |
| `XTAK-` | `https://jira.nike.com/browse/XTAK-<num>` |

```bash
# Dry run (no API calls made)
~/.cursor/skills/sync-team-repos/scripts/add-autolinks.sh --dry-run

# Add to all repos
~/.cursor/skills/sync-team-repos/scripts/add-autolinks.sh
```

**Example output:**
```
[ 1/22] nike-internal/mpe.feature.pdp
         NIKEAPPUI-     ✅ added
         NIKEAPCORE-    ✅ added
         XTAK-          ⏭️  already exists
[ 2/22] nike-internal/mpe.app.mamba-android
         NIKEAPPUI-     🔒 no admin access
         NIKEAPCORE-    🔒 no admin access
         XTAK-          🔒 no admin access
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AUTOLINK REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Autolink operations: 57 added, 3 already existed

  ✅ Fully configured (19 repos)
     nike-internal/mpe.feature.pdp  (added: 2, already existed: 1)
     ...

  🔒 No admin access — links not added (3 repos)
     nike-internal/mpe.app.mamba-android  (added: 0, skipped: 0, blocked: NIKEAPPUI- NIKEAPCORE- XTAK-)
     ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> **Note:** `gh` must be authenticated in your **own terminal** — it does not pick up the keychain token from Cursor's shell. Run all scripts from a regular terminal session.

## Repo list

Canonical list lives at `~/.cursor/data/team-repos.json`. Each entry has `org`, `repo`, and `localPath`.

## Prerequisites

- `jq` installed (`brew install jq`)
- SSH key authorized for `github.com` / `nike-internal` org
- `gh` CLI authenticated (used as fallback for default branch detection and required for `add-autolinks.sh`)
- **Run all scripts from your own terminal** — `gh` does not pick up its keychain token from Cursor's shell
