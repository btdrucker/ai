---
name: productwall-build-snapshot
description: Publish a Product Wall snapshot to Artifactory and update const val productWallFeature in Nike App Android's Depends.kt — then stop. Use this when combining a Product Wall snapshot with a Mamba snapshot in the same Nike App branch (so both versions are set before triggering one Jenkins build). For a standalone Product Wall QA delivery, use productwall-build-snapshot-jenkins instead.
---

# Product Wall Build Snapshot (Depends.kt only)

Publishes a Product Wall snapshot to Artifactory and updates `Depends.kt` in Nike App Android. Stops there — no commit, no push, no Jenkins. Use this when you also have a Mamba snapshot that needs to land in the same Nike App branch before triggering a single Jenkins build.

## Prerequisites

- Artifactory credentials in macOS Keychain: `security find-generic-password -a "$(id -un)" -s "artifactory" -w`
- Ruby + Bundler installed (for Fastlane)
- Nike App Android branch already checked out (the mamba-build-snapshot skill typically creates it)

## Inputs

1. **TICKET_KEY** — Extract from the current Product Wall branch name.

## Workflow

### Step 1: Publish Product Wall Snapshot to Artifactory

In the `mpe.feature.productwall` repo, on the current feature branch, use the Gradle task directly (preferred — no Fastlane/Bundler dependency):

```bash
cd $HOME/mpe.feature.productwall/Android
GRADLE_USER_HOME=~/.gradle \
ARTIFACTORY_USERNAME="$(id -un)" \
ARTIFACTORY_PASSWORD="$(security find-generic-password -a "$(id -un)" -s "artifactory" -w)" \
./gradlew runArtifactoryPublish 2>&1 | tee /tmp/pw_snapshot_build.log
```

Requires `required_permissions: ["all"]`.

Fastlane alternative (if needed): `cd Fastlane && bundle exec fastlane android_publish_snapshot_feature` — but this requires `bundler:2.7.2` to be installed (`sudo gem install bundler:2.7.2`).

### Step 2: Extract the SNAPSHOT version

Version format: `MAJOR.MINOR.PATCH-<git-short-hash>-SNAPSHOT` (e.g., `24.1.1-0780c4a6-SNAPSHOT`)

```bash
grep -oE '[0-9]+\.[0-9]+\.[0-9]+-[a-f0-9]+-SNAPSHOT' /tmp/pw_snapshot_build.log | head -1
```

If not found in log, compute manually:
```bash
cd $HOME/mpe.feature.productwall/Android
HASH=$(git rev-parse --short HEAD)
VERSION=$(grep -E 'val (major|minor|patch)' feature/build.gradle.kts | grep -oE '[0-9]+' | paste -sd '.' -)
echo "${VERSION}-${HASH}-SNAPSHOT"
```

### Step 3: Update Depends.kt in Nike App Android

Update `const val productWallFeature` at line 187 of:
`buildSrc/src/main/kotlin/Depends.kt`

```kotlin
const val productWallFeature = "<SNAPSHOT_VERSION>"
```

Use `StrReplace` to swap the old version for the new one.

**Stop here.** The caller is responsible for committing, pushing, and triggering Jenkins (typically via the mamba-build-snapshot skill which handles those steps for the combined branch).

## Error Handling

| Step | Error | Recovery |
|------|-------|----------|
| Fastlane | `bundle: command not found` | Run `bundle install` in `Fastlane/` |
| Publishing | Auth failed | Update Keychain: `security add-generic-password -U -a "$(id -un)" -s "artifactory" -w "NEW_PASSWORD"` |
| Publishing | Build failure | Check compilation errors; may need to rebase onto `main` |
