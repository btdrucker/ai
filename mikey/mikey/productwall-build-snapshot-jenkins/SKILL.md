---
name: productwall-build-snapshot-jenkins
description: Full end-to-end QA delivery pipeline for Product Wall. Publishes PW snapshot to Artifactory, creates a feature branch in Nike App Android, updates Depends.kt, commits, pushes, triggers Jenkins build, extracts TestFairy link, adds Jira comment, transitions ticket to QA, and unassigns. Use when Product Wall is the only dependency needing a snapshot build.
---

# Product Wall Build Snapshot → QA Delivery

Fully automated pipeline from Product Wall snapshot publish through QA ticket handoff — no PR required.

## Prerequisites

- Artifactory credentials available as environment variables: `ARTIFACTORY_USERNAME` and `ARTIFACTORY_PASSWORD`
  - Credentials can be sourced from macOS Keychain: `security find-generic-password -a "$(id -un)" -s "artifactory" -w`
- DIS CLI installed with Jenkins configured: `NIKE_EMAIL=<your-jenkins-username>`, `MOBILE_CI_JENKINS_URL`, `MOBILE_CI_JENKINS_PAT` in `~/.zshrc`
- Atlassian MCP available for Jira operations
- Ruby + Bundler installed (for Fastlane)

## Inputs

The agent needs to know:
1. **TICKET_KEY** — The Jira ticket (e.g., `NIKEAPPUI-127`). Extract from the current Product Wall branch name.
2. **PW_PR_URL** (optional) — URL of the Product Wall PR for the comment. Extract from the current branch via `gh pr view --json url`.

## Workflow

### Step 1: Publish Product Wall Snapshot to Artifactory

In the `mpe.feature.productwall` repo, on the current feature branch:

**Option A — Gradle (preferred):**

```bash
cd $PW_REPO/Android  # defaults to $HOME/mpe.feature.productwall/Android
GRADLE_USER_HOME=~/.gradle \
ARTIFACTORY_USERNAME="$(id -un)" \
ARTIFACTORY_PASSWORD="$(security find-generic-password -a "$(id -un)" -s "artifactory" -w)" \
./gradlew runArtifactoryPublish 2>&1 | tee /tmp/pw_snapshot_build.log
```

**Option B — Fastlane (requires bundler:2.7.2):**

```bash
cd $PW_REPO/Fastlane  # defaults to $HOME/mpe.feature.productwall/Fastlane
bundle exec fastlane android_publish_snapshot_feature 2>&1 | tee /tmp/pw_snapshot_build.log
```

If Fastlane fails with bundler version error: `sudo gem install bundler:2.7.2`

**Option C — Local Maven only (no Artifactory, for local testing):**

```bash
cd $PW_REPO/Android  # defaults to $HOME/mpe.feature.productwall/Android
./gradlew :feature:publishToMavenLocal 2>&1 | tee /tmp/pw_snapshot_build.log
```

For QA delivery, use Option A or B (publishes to Artifactory so Jenkins can resolve it). Option C is only for local dev testing in Android Studio.

### Step 1a: Extract the SNAPSHOT version

The version format is `MAJOR.MINOR.PATCH-<git-short-hash>-SNAPSHOT` (e.g., `24.1.1-0780c4a6-SNAPSHOT`).

Extract from the build log:
```bash
grep -oE '[0-9]+\.[0-9]+\.[0-9]+-[a-f0-9]+-SNAPSHOT' /tmp/pw_snapshot_build.log | head -1
```

If that doesn't match, compute it manually:
```bash
cd $PW_REPO/Android
HASH=$(git rev-parse --short HEAD)
VERSION=$(grep -E 'val (major|minor|patch)' feature/build.gradle.kts | grep -oE '[0-9]+' | paste -sd '.' -)
echo "${VERSION}-${HASH}-SNAPSHOT"
```

For Option C (local), verify the published artifact:
```bash
ls ~/.m2/repository/com/nike/mpe/productwall-feature/ | grep SNAPSHOT
```

### Step 2: Create Feature Branch in Nike App Android

```bash
cd $NIKEAPP_REPO  # defaults to $HOME/mpe.app.nikeapp-android
git checkout main
git pull origin main
git checkout -b feature/<branch-context>-<TICKET_KEY>
```

Branch naming convention: `feature/<descriptive-slug>-<TICKET_KEY>`
Example: `feature/pw-scroll-into-view-NIKEAPPUI-127`

### Step 3: Update Product Wall Version in Depends.kt

Update line 187 of `buildSrc/src/main/kotlin/Depends.kt`:

```kotlin
const val productWallFeature = "<SNAPSHOT_VERSION>"
```

Use exact line replacement — the productWallFeature version is at line 187.

### Step 4: Stage, Commit, Push

```bash
git add buildSrc/src/main/kotlin/Depends.kt
git commit -m "<TICKET_KEY>: Update Product Wall to <SNAPSHOT_VERSION> snapshot"
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

Use Atlassian MCP `jira_add_comment`. Format:

```
Test ready!

build here ->
NikeApp-Android-Feature-World
Release Notes for Version <APP_VERSION>:
https://nike.testfairy.com/join/NikeApp-Android-Feature-World?id=<TESTFAIRY_BUILD_ID>

PR -> <PW_PR_URL>

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
gh api repos/nike-internal/mpe.app.nikeapp-android/git/refs/heads/<branch-name> --method DELETE
```

Confirm deletion:
```bash
gh api repos/nike-internal/mpe.app.nikeapp-android/git/refs/heads/<branch-name> 2>&1 | grep -c "Not Found" && echo "Branch deleted" || echo "Branch still exists"
```

Use `required_permissions: ["all"]` for all `gh` commands.

## Key Differences from Mamba Snapshot

| Aspect | Mamba | Product Wall |
|--------|-------|--------------|
| Repo | `mpe.app.mamba-android` | `mpe.feature.productwall` |
| Publish command | `printf 'Y\nY\n' \| ./publishing.sh` | `bundle exec fastlane android_publish_snapshot_feature` |
| Working directory | Repo root | `Fastlane/` (Fastlane) or `Android/` (Gradle) |
| Version format | `X.Y.Z-YYYYMMDD-hash-SNAPSHOT` | `X.Y.Z-hash-SNAPSHOT` |
| Depends.kt constant | `const val mamba` (line 223) | `const val productWallFeature` (line 187) |
| Artifact coordinates | `com.nike.mamba:*` | `com.nike.mpe:productwall-feature` |
| Jenkins / TestFairy / Jira | Same | Same |

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
| Fastlane | `bundle: command not found` | Install Ruby + Bundler, run `bundle install` in `Fastlane/` |
| Publishing | Auth failed | Verify `ARTIFACTORY_USERNAME` / `ARTIFACTORY_PASSWORD` env vars; update Keychain if needed |
| Publishing | Gradle build failure | Check compilation errors; may need to rebase onto `main` first |
| Jenkins trigger | AUTH_FAILED | Check `MOBILE_CI_JENKINS_PAT` in `~/.zshrc` |
| Jenkins build | FAILURE result | Report failure, link to console log |
| Jira transition | Invalid transition | Re-discover transitions with `jira_get_transitions` |
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
- Product Wall has both iOS and Android — this skill only covers the Android flow
- The `publishToMavenLocal` option (Option C) does NOT upload to Artifactory; Jenkins won't be able to resolve it. Use it only for local Android Studio testing.
