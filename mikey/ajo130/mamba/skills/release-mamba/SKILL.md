---
name: release-mamba
description: >-
  Weekly Mamba Android release: paired draft PRs on release/mamba/vX.Y.Z branches,
  SNAPSHOT publish and Jenkins in phase 1; after the Mamba PR merges, publish in
  release mode, tag with the library version, and update the Nike App PR. Re-entrant
  — re-run with the same version to advance phases. Use when the user asks to
  release mamba or run a weekly release.
---

# Release Mamba

Two-phase, re-entrant weekly release. Branch convention: **`release/mamba/vX.Y.Z`** (e.g. `release/mamba/v48.1.0`) in **both** Mamba and Nike App repos.

The skill never mutates the user's primary checkout — all work happens in dedicated worktrees.

## Step 0 — Ask for release version

**Ask the user** for the target semver (e.g. `48.1.0`). Do not auto-bump `gradle.properties`.

## Step 1 — Resolve context (must run first)

```bash
VERSION="48.1.0"   # set from user input
BRANCH="release/mamba/v${VERSION}"

MAMBA_REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$MAMBA_REPO" ]] || [[ ! -f "$MAMBA_REPO/gradle.properties" ]]; then
    echo "Error: must run from inside the Mamba Android repo." >&2
    exit 1
fi
NIKEAPP_REPO="${NIKEAPP_REPO:-$(dirname "$MAMBA_REPO")/mpe.app.nikeapp-android}"
SCRIPTS="$MAMBA_REPO/scripts"
MAMBA_REPO_SLUG="nike-internal/mpe.app.mamba-android"
NIKEAPP_REPO_SLUG="nike-internal/mpe.app.nikeapp-android"

# Primary clone (.git dir) or linked worktree (.git file) both valid.
if [[ ! -d "$NIKEAPP_REPO/.git" && ! -f "$NIKEAPP_REPO/.git" ]]; then
    echo "Error: Nike App repo not found at $NIKEAPP_REPO. Set NIKEAPP_REPO to the primary clone or a worktree path." >&2
    exit 1
fi
```

The tag written in Phase 2 uses the **library version output** (e.g. `48.1.0-20260609-abc123`), not `vX.Y.Z`. The branch keeps the `v` prefix; the tag does not.

## Step 2 — Credentials preflight

```bash
"$SCRIPTS/lib/check-creds.sh"
```

Use `required_permissions: ["all"]` (Jenkins probe needs unrestricted network). Stop on non-zero exit.

## Step 3 — Detect phase via PR state

```bash
git -C "$MAMBA_REPO" fetch origin --quiet
MAMBA_PR_STATE="$(gh pr list \
  --repo "$MAMBA_REPO_SLUG" \
  --head "$BRANCH" \
  --state all \
  --json state \
  --jq '.[0].state // "NONE"')"
MAMBA_PR_URL="$(gh pr list \
  --repo "$MAMBA_REPO_SLUG" \
  --head "$BRANCH" \
  --state all \
  --json url \
  --jq '.[0].url // empty')"
```

Route on `$MAMBA_PR_STATE`:

| Value | Action |
|-------|--------|
| `NONE` | Run **Phase 1** below. |
| `OPEN` | Tell user: PR `$MAMBA_PR_URL` needs CODEOWNER approval + green CI, then merge. Re-run `release-mamba` with the same version when done. **Stop.** |
| `MERGED` | Run **Phase 2** below. |
| `CLOSED` | Tell user: PR was closed without merge. Investigate before proceeding. **Stop.** |

The skill is safe to re-run at any time — phase detection is the only state.

---

## Phase 1 — Open paired PRs + SNAPSHOT

### 1a — Mamba release worktree

```bash
MAMBA_WT="$("$SCRIPTS/lib/worktree-add.sh" \
  --repo "$MAMBA_REPO" \
  --branch "$BRANCH" \
  --base origin/main \
  --symlink-local-properties)"
```

### 1b — Bump `gradle.properties`

```bash
if [[ "$(uname -s)" == "Darwin" ]]; then
    sed -i '' "s/^version=.*/version=${VERSION}/" "$MAMBA_WT/gradle.properties"
else
    sed -i.bak "s/^version=.*/version=${VERSION}/" "$MAMBA_WT/gradle.properties"
    rm -f "$MAMBA_WT/gradle.properties.bak"
fi

if ! grep -q "^version=${VERSION}$" "$MAMBA_WT/gradle.properties"; then
    echo "Error: failed to bump gradle.properties to $VERSION." >&2
    exit 1
fi
```

Commit and push. **Pre-push hooks are skipped** (`commit-and-push.sh` defaults to `--no-verify`) because this is metadata-only — but the PR's CI run is the gate before merge. If the user wants local PRA validation first, recommend running the `push-mamba-pr` skill in `$MAMBA_WT` after this commit and before re-running.

```bash
"$SCRIPTS/lib/commit-and-push.sh" \
  --repo "$MAMBA_WT" \
  --add gradle.properties \
  --message "Version ${VERSION}."
```

### 1c — Mamba draft PR

```bash
MAMBA_PR="$("$SCRIPTS/lib/open-draft-pr.sh" \
  --repo "$MAMBA_REPO_SLUG" \
  --head "$BRANCH" \
  --title "Release Mamba ${VERSION}" \
  --body "Release branch \`$BRANCH\`. Weekly Mamba Android release.")"
```

### 1d — Publish SNAPSHOT

Expect ~3 minutes. Set `block_until_ms` to at least 300000.

```bash
SNAPSHOT="$("$SCRIPTS/publish-mamba-snapshot.sh" --repo "$MAMBA_WT")"
```

### 1e — Nike App worktree (mirror branch)

```bash
NIKEAPP_WT="$(dirname "$NIKEAPP_REPO")/$(basename "$NIKEAPP_REPO")--$(echo "$BRANCH" | tr '/' '-')"

"$SCRIPTS/setup-nikeapp-worktree.sh" \
  --version "$SNAPSHOT" \
  --branch "$BRANCH" \
  --nike-repo "$NIKEAPP_REPO" \
  --no-trigger-jenkins
```

### 1f — Nike App draft PR

```bash
NIKEAPP_PR="$("$SCRIPTS/lib/open-draft-pr.sh" \
  --repo "$NIKEAPP_REPO_SLUG" \
  --head "$BRANCH" \
  --title "Release Mamba ${VERSION}" \
  --body-template "$MAMBA_REPO/.github/pr-templates/nikeapp-snapshot.md" \
  --var snapshot="$SNAPSHOT" \
  --var companion_pr="$MAMBA_PR" \
  --var smoke_test_area="Release smoke test")"
```

### 1g — Jenkins

```bash
"$SCRIPTS/lib/trigger-jenkins.sh" \
  --job "/job/Consumer/job/Nike_App/job/Android/job/Dev/job/NikeApp-Manual-Debug" \
  --param "BRANCH=$BRANCH"
```

Tell the user: "Merge `$MAMBA_PR` once CODEOWNERs approve and CI is green, then re-run `release-mamba` with version `${VERSION}` to advance to Phase 2."

### Phase 1 closeout

| Item | Value |
|------|-------|
| Release version | `$VERSION` |
| Branch | `$BRANCH` |
| Mamba worktree | `$MAMBA_WT` |
| Mamba PR | `$MAMBA_PR` |
| SNAPSHOT | `$SNAPSHOT` |
| Nike App worktree | `$NIKEAPP_WT` |
| Nike App PR | `$NIKEAPP_PR` |
| Jenkins | queued in step 1g |
| Next action | Merge Mamba PR, then re-run with same `$VERSION` |

---

## Phase 2 — Publish release, tag, update Nike App PR

The Mamba PR is merged. Publish from a **detached worktree at `origin/main`** so the user's primary checkout is untouched.

### 2a — Detached release worktree + version guard

```bash
git -C "$MAMBA_REPO" fetch origin --quiet
RELEASE_WT="$("$SCRIPTS/lib/worktree-add.sh" \
  --repo "$MAMBA_REPO" \
  --detach origin/main \
  --symlink-local-properties \
  --no-fetch)"

if ! grep -q "^version=${VERSION}$" "$RELEASE_WT/gradle.properties"; then
    actual="$(grep '^version=' "$RELEASE_WT/gradle.properties" || echo '<missing>')"
    echo "Error: $RELEASE_WT/gradle.properties has '$actual', expected 'version=$VERSION'." >&2
    echo "The release commit is not on origin/main yet. Confirm the merge landed and re-run." >&2
    exit 1
fi
```

### 2b — Publish release (not SNAPSHOT)

Expect ~3 minutes. Set `block_until_ms` to at least 300000.

```bash
RELEASE_VER="$("$SCRIPTS/lib/publish-gradle.sh" \
  --repo "$RELEASE_WT" \
  --release)"
```

Uses `-PIS_RELEASE=true`. Output is the library version string (no `-SNAPSHOT` suffix), e.g. `48.1.0-20260609-abc123def`.

### 2c — Tag and push

Tag name = `$RELEASE_VER` (library version output). No GitHub Release body.

```bash
"$SCRIPTS/lib/tag-and-release.sh" \
  --repo "$RELEASE_WT" \
  --tag "$RELEASE_VER"
```

### 2d — Update Nike App PR to release version

Re-use the Phase 1 Nike App worktree. If it was removed (e.g. user pruned), re-create it pointing at the existing remote branch — **not** `origin/main`, which would lose the SNAPSHOT bump:

```bash
NIKEAPP_WT="$(dirname "$NIKEAPP_REPO")/$(basename "$NIKEAPP_REPO")--$(echo "$BRANCH" | tr '/' '-')"

if [[ ! -d "$NIKEAPP_WT" ]]; then
    "$SCRIPTS/lib/worktree-add.sh" \
        --repo "$NIKEAPP_REPO" \
        --branch "$BRANCH" \
        --base "origin/$BRANCH" \
        --symlink-local-properties
fi
```

Bump `Versions.mamba` from SNAPSHOT → release version. **Re-use `setup-nikeapp-worktree.sh`** for the patch+commit+push so the macOS/Linux-safe sed and Depends.kt patching logic stays in one place:

```bash
"$SCRIPTS/setup-nikeapp-worktree.sh" \
  --version "$RELEASE_VER" \
  --branch "$BRANCH" \
  --nike-repo "$NIKEAPP_REPO" \
  --no-trigger-jenkins
```

Update the PR body and mark ready (idempotent — skip `ready` if already non-draft):

```bash
NIKEAPP_PR_NUM="$(gh pr list \
  --repo "$NIKEAPP_REPO_SLUG" \
  --head "$BRANCH" \
  --json number \
  --jq '.[0].number')"

gh pr edit "$NIKEAPP_PR_NUM" \
  --repo "$NIKEAPP_REPO_SLUG" \
  --body "Bumps \`Versions.mamba\` to release \`$RELEASE_VER\` (tag: \`$RELEASE_VER\`). Companion: $MAMBA_PR_URL"

IS_DRAFT="$(gh pr view "$NIKEAPP_PR_NUM" --repo "$NIKEAPP_REPO_SLUG" --json isDraft --jq '.isDraft')"
if [[ "$IS_DRAFT" == "true" ]]; then
    gh pr ready "$NIKEAPP_PR_NUM" --repo "$NIKEAPP_REPO_SLUG"
fi
```

### 2e — Re-trigger Jenkins

```bash
"$SCRIPTS/lib/trigger-jenkins.sh" \
  --job "/job/Consumer/job/Nike_App/job/Android/job/Dev/job/NikeApp-Manual-Debug" \
  --param "BRANCH=$BRANCH"
```

### Phase 2 closeout

| Item | Value |
|------|-------|
| Release version (semver) | `$VERSION` |
| Published library version | `$RELEASE_VER` |
| Git tag | `$RELEASE_VER` |
| Nike App worktree | `$NIKEAPP_WT` |
| Nike App PR | updated + marked ready (PR #$NIKEAPP_PR_NUM) |
| Jenkins | re-queued in step 2e |

## Gradle

Always prefix shell calls: `GRADLE_USER_HOME="$HOME/.gradle"` and `required_permissions: ["all"]`.

## Re-run safety

Re-invoke `release-mamba` with the same `$VERSION` at any time. Step 3 routes by `$MAMBA_PR_STATE` so partial runs resume cleanly. Phase 2 is idempotent except for `git tag` — if it fails because the tag already exists, pass `--force` to `tag-and-release.sh` only if you intend to replace it.
