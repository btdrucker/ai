---
name: mamba-build-local
description: Build and publish Mamba Android to local Maven repository, then automatically update the consumer app's dependency version. Use when preparing local validation builds before snapshot or release publishing.
---

# Mamba Build Local

Build Mamba Android locally and automatically update the consumer app's dependency version.

## Quick Start

Execute the script from the repo root:
```bash
bash scripts/mamba-build-local.sh
```

The script will:
1. Run `./publishing.sh --local` in the mamba repo
2. Wait for build completion
3. Extract the generated local version
4. Update the consumer app's dependency file with the new version
5. Report success with version details

## Configuration

Before running, set these environment variables:

```bash
export MAMBA_REPO_PATH="/path/to/mpe.app.mamba-android"
export CONSUMER_REPO_PATH="/path/to/consumer-app"
export DEPENDS_FILE_PATH="buildSrc/src/main/kotlin/Depends.kt"  # Relative to CONSUMER_REPO
export DEPENDS_LINE_NUMBER=223  # Line containing: const val mamba = "..."
```

Or modify the defaults in the script (lines 12-15).

## Workflow

**Step 1: Publish Local** → Runs publishing.sh with `--local` flag

**Step 2: Extract Version** → Parses gradle output to find generated version string

**Step 3: Update Dependency** → Updates consumer app's dependency file

**Step 4: Verify** → Confirms the update was successful

## What Gets Updated

Example - Line in dependency file before:
```kotlin
const val mamba = "47.0.0-20260527-f5dc84089"
```

Example - Line in dependency file after:
```kotlin
const val mamba = "47.0.0-20260528-97eb5b35-LOCAL"
```

## Output

Script reports:
- Build status (success/failure)
- Generated version string
- Dependency file update confirmation
- Next steps for testing

## Requirements

- `bash` shell
- `cd` access to both mamba and consumer repos
- `grep`, `sed`, `awk` (standard Unix tools)
- Write access to dependency file
- Publishing.sh credentials (interactive prompt)

## Notes

- Local builds use `-LOCAL` suffix to prevent Gradle treating dependency as changing
- Publishing requires manual credentials (interactive prompt in publishing.sh)
- Build artifacts stored in ~/.m2/repository/
- Script creates backup of dependency file before modifying
- Android Studio cache may need invalidation after update

