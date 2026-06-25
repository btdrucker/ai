---
name: mamba-build-snapshot-jenkins
description: Full end-to-end QA delivery pipeline. Publishes Mamba snapshot to Artifactory, creates a feature branch in Nike App Android, triggers Jenkins build, extracts TestFairy link, adds Jira comment, transitions ticket to QA, unassigns, and deletes the ephemeral branch. Use when preparing a Mamba snapshot for QA testing.
---

# Mamba Build Snapshot → QA Delivery

Fully automated pipeline from Mamba snapshot publish through QA ticket handoff — no PR required.

## Prerequisites

- Artifactory password stored in macOS Keychain: `security find-generic-password -a "$(id -un)" -s "artifactory" -w`
- DIS CLI installed with Jenkins configured: `NIKE_EMAIL=<your-jenkins-username>`, `MOBILE_CI_JENKINS_URL`, `MOBILE_CI_JENKINS_PAT` in `~/.zshrc`
- Atlassian MCP available for Jira operations

## Inputs

The agent needs to know:
1. **TICKET_KEY** — The Jira ticket (e.g., `NIKEAPPUI-237`). Extract from the current Mamba branch name.
2. **MAMBA_PR_URL** (optional) — URL of the Mamba PR for the comment. Extract from the current Mamba branch via `gh pr view --json url`.

## Workflow

### Step 1: Publish Mamba Snapshot to Artifactory

In the `mpe.app.mamba-android` repo, on the current feature branch:

```bash
cd $MAMBA_REPO  # defaults to $HOME/mpe.app.mamba-android
printf 'Y\nY\n' | ./publishing.sh 2>&1 | tee /tmp/mamba_snapshot_build.log
```

Extract the SNAPSHOT version from the build log:
```bash
grep -oP '\d+\.\d+\.\d+-\d+-[a-f0-9]+-SNAPSHOT' /tmp/mamba_snapshot_build.log | head -1
```

If publishing fails with auth error, prompt user to update Keychain:
```bash
security add-generic-password -U -a "$(id -un)" -s "artifactory" -w "NEW_PASSWORD"
```

### Step 2: Create Feature Branch in Nike App Android

```bash
cd $NIKEAPP_REPO  # defaults to $HOME/mpe.app.nikeapp-android
git checkout main
git pull origin main
git checkout -b feature/<branch-context>-<TICKET_KEY>
```

Branch naming convention: `feature/<descriptive-slug>-<TICKET_KEY>`
Example: `feature/mamba-pw-thumbnail-fix-NIKEAPPUI-127`

### Step 3: Update Mamba Version in Depends.kt

Update line 223 of `buildSrc/src/main/kotlin/Depends.kt`:

```kotlin
const val mamba = "<SNAPSHOT_VERSION>"
```

Use exact line replacement — the mamba version is at line 223.

### Step 4: Stage, Commit, Push

```bash
git add buildSrc/src/main/kotlin/Depends.kt
git commit -m "<TICKET_KEY>: Update Mamba to <SNAPSHOT_VERSION> snapshot"
git push --no-verify -u origin <branch-name>
```

### Step 5: Trigger Jenkins Build via DIS

```bash
source ~/.zshrc
dis call jenkins_trigger_build '{"instance": "mobile-ci", "path": "Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual", "parameters": {"BRANCH": "origin/<branch-name>"}}'
```

IMPORTANT: The BRANCH parameter must include the `origin/` prefix.

### Step 6: Poll Jenkins Until Complete

Wait 20 minutes initially, then poll every 3 minutes:

```bash
source ~/.zshrc
dis call jenkins_get_build '{"instance": "mobile-ci", "path": "Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual"}'
```

Check `"building": false` and `"result": "SUCCESS"`. Note the build number.

### Step 7: Extract TestFairy Link

```bash
source ~/.zshrc
dis call jenkins_search_build_log '{"instance": "mobile-ci", "path": "Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual", "build_number": "<BUILD_NUMBER>", "pattern": "Build URL"}'
```

From results, extract the build ID from `https://nike.testfairy.com/projects/432/builds/<ID>`.

Construct QA link: `https://nike.testfairy.com/join/NikeApp-Android-Feature-World?id=<ID>`

The World variant (projects/432) is the primary QA link.

### Step 8: Add Comment to Jira Ticket

Use Atlassian MCP `jira_add_comment`. Format the comment like the NIKEAPPUI-93 example:

```
Test ready!

build here ->
NikeApp-Android-Feature-World
Release Notes for Version <APP_VERSION>:
https://nike.testfairy.com/join/NikeApp-Android-Feature-World?id=<TESTFAIRY_BUILD_ID>

PR -> <MAMBA_PR_URL>

nike app branch used for testing -> https://github.com/nike-internal/mpe.app.nikeapp-android/tree/<branch-name>

<Optional: brief description of what changed and testing guidance>
```

Do NOT tag anyone in the comment. QA will pick it up from the ticket queue.

### Step 9: Transition Ticket to QA

First discover the QA transition ID:
```
jira_get_transitions issue_key=<TICKET_KEY>
```

For NIKEAPPUI tickets, QA transition is typically ID `61`. Always verify.

Then transition:
```
jira_transition_issue issue_key=<TICKET_KEY> transition_id=<QA_TRANSITION_ID>
```

### Step 10: Unassign Ticket

```
jira_update_issue issue_key=<TICKET_KEY> fields={"assignee": null}
```

### Step 11: Delete Remote Nike App Branch

The feature branch in Nike App Android was only needed to run the Jenkins job. Delete it now:

```bash
cd $HOME/mpe.app.nikeapp-android
gh repo set-default nike-internal/mpe.app.nikeapp-android
gh api repos/nike-internal/mpe.app.nikeapp-android/git/refs/heads/<branch-name> --method DELETE
```

Confirm deletion:
```bash
gh api repos/nike-internal/mpe.app.nikeapp-android/git/refs/heads/<branch-name> 2>&1 | grep -c "Not Found" && echo "Branch deleted" || echo "Branch still exists"
```

Use `required_permissions: ["all"]` for all `gh` commands.

## Jenkins Details

- **Instance:** `mobile-ci`
- **Job path:** `Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual`
- **Parameter:** `BRANCH` (format: `origin/feature/...`)
- **Estimated build time:** 20-30 minutes
- **TestFairy World project:** 432 (primary QA link)
- **TestFairy China project:** 431

## Error Handling

| Step | Error | Recovery |
|------|-------|----------|
| Publishing | Auth failed | Prompt user to update Keychain password |
| Jenkins trigger | AUTH_FAILED | Check MOBILE_CI_JENKINS_PAT in ~/.zshrc |
| Jenkins build | FAILURE result | Report failure, link to console log |
| Jira transition | Invalid transition | Re-discover transitions with jira_get_transitions |
| Branch delete | 404 Not Found | Branch may already be deleted — safe to ignore |
| Branch delete | 422 Unprocessable | Branch name may be wrong — verify with `gh api repos/nike-internal/mpe.app.nikeapp-android/branches` |

## DIS Commands Reference

All `dis call` commands require `required_permissions: ["all"]` in Cursor.

```bash
# List instances
dis call jenkins_list_instances '{}'

# Trigger build
dis call jenkins_trigger_build '{"instance": "mobile-ci", "path": "Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual", "parameters": {"BRANCH": "origin/feature/..."}}'

# Check build status
dis call jenkins_get_build '{"instance": "mobile-ci", "path": "Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual", "build_number": "NNNN"}'

# Search build log
dis call jenkins_search_build_log '{"instance": "mobile-ci", "path": "Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual", "build_number": "NNNN", "pattern": "Build URL"}'
```

## Notes

- No PR is needed in Nike App Android — Jenkins can build directly from a pushed branch
- The `--no-verify` flag on push skips pre-push hooks (snapshot branches don't need PRA)
- TestFairy landing page URLs are static; the `?id=` parameter makes each build unique
- The feature branch in Nike App Android is ephemeral — it exists only to trigger Jenkins; Step 11 deletes it immediately after the Jira handoff
- Snapshot versions use `-SNAPSHOT` suffix (Gradle standard)
