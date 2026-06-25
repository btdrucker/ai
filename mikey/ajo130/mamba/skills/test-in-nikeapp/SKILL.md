---
name: test-in-nikeapp
description: >-
  Publish a Mamba SNAPSHOT from the current branch, integrate it into Nike App
  Android, apply integration fixes when needed, and queue NikeApp-Manual-Debug.
  Opens a Nike App PR only when integration changes were made. Use when the user
  asks to test or verify a Mamba change in Nike App.
---

# Test in Nike App

Fast loop: **SNAPSHOT → Nike App bump → optional integration edits → Jenkins**.

Does **not** open a Nike App PR unless the agent made integration changes beyond the `Versions.mamba` bump.

## Jenkins policy (always)

**Queue NikeApp-Manual-Debug exactly once on every successful run.** Integration signal detection (Step 5) only decides *when* Jenkins runs — never *whether*.

| Path | When Jenkins runs | How |
|------|-------------------|-----|
| No integration signals (`NEEDS_INTEGRATION=false`) | Immediately after the version bump is pushed (Step 7) | `setup-nikeapp-worktree.sh` triggers Jenkins by default |
| Integration signals (`NEEDS_INTEGRATION=true`) | After integration edits are applied and pushed (Step 9) | Step 7 uses `--no-trigger-jenkins`; Step 9 triggers after Step 8 |

Step 5 answers: “Might Nike App need wiring changes before it compiles?” — not “Should we skip Jenkins?”
Even when Step 8 finds no edits beyond `Depends.kt`, still run Step 9 to queue the build.

## Step 1 — Resolve context (must run first)

```bash
MAMBA_REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$MAMBA_REPO" ]] || [[ ! -f "$MAMBA_REPO/gradle.properties" ]]; then
    echo "Error: must run from inside the Mamba Android repo." >&2
    exit 1
fi
BRANCH="$(git -C "$MAMBA_REPO" branch --show-current)"
NIKEAPP_REPO="${NIKEAPP_REPO:-$(dirname "$MAMBA_REPO")/mpe.app.nikeapp-android}"
SCRIPTS="$MAMBA_REPO/scripts"

if [[ "$BRANCH" == "main" || -z "$BRANCH" ]]; then
    echo "Error: refuse to publish from main or detached HEAD (branch=$BRANCH)." >&2
    exit 1
fi
# Primary clone (.git dir) or linked worktree (.git file) both valid.
if [[ ! -d "$NIKEAPP_REPO/.git" && ! -f "$NIKEAPP_REPO/.git" ]]; then
    echo "Error: Nike App repo not found at $NIKEAPP_REPO. Set NIKEAPP_REPO to the primary clone or a worktree path." >&2
    exit 1
fi
```

## Step 2 — Credentials preflight

```bash
"$SCRIPTS/lib/check-creds.sh"
```

Use `required_permissions: ["all"]` (Jenkins probe needs unrestricted network). If exit ≠ 0, surface the report and **stop** — do not create worktrees, publish, or trigger Jenkins. See `.cursor/skills/credentials-doctor/SKILL.md`.

## Step 3 — Mamba worktree

```bash
WT="$("$SCRIPTS/lib/worktree-add.sh" \
  --repo "$MAMBA_REPO" \
  --branch "$BRANCH" \
  --symlink-local-properties)"
```

## Step 4 — Confirm branch is committed and pushed

The SNAPSHOT embeds the commit hash; unpushed commits produce unresolvable artifacts. **Never auto-commit feature work with a generic message** — that loses author intent.

```bash
DIRTY="$(git -C "$WT" status --porcelain)"
```

- **Dirty (uncommitted changes)**: list the files to the user and stop. Ask them to commit with a real message (or run the `push-mamba-pr` skill), then re-run this skill.
- **Clean and ahead of origin**: push only.

```bash
if [[ -z "$DIRTY" ]]; then
    AHEAD="$(git -C "$WT" rev-list --count "@{u}..HEAD" 2>/dev/null || echo 0)"
    if [[ "$AHEAD" -gt 0 ]]; then
        "$SCRIPTS/lib/commit-and-push.sh" --repo "$WT" --push-only
    fi
fi
```

## Step 5 — Detect integration signals

```bash
API_DIFF="$(git -C "$WT" diff origin/main...HEAD --name-only -- '**/*.api' 2>/dev/null || true)"
DI_DIFF="$(git -C "$WT" diff origin/main...HEAD --name-only -- \
  'app/src/**/di/**' 'app/src/**/*Module*.kt' 'app/src/**/*HiltModules*.kt' 2>/dev/null || true)"

if [[ -n "$API_DIFF" || -n "$DI_DIFF" ]]; then
    NEEDS_INTEGRATION=true
else
    NEEDS_INTEGRATION=false
fi
```

If `$NEEDS_INTEGRATION` is true, summarize the changed files for the user — they explain why Step 8 integration edits are needed before Jenkins (Step 9).

## Step 6 — Publish SNAPSHOT

Expect ~3 minutes for a full publish. Set `block_until_ms` to at least 300000.

```bash
SNAPSHOT="$("$SCRIPTS/publish-mamba-snapshot.sh" --repo "$WT")"
```

Requires `local.properties` in the worktree (`--symlink-local-properties` handled it). Prefix Gradle calls with `GRADLE_USER_HOME="$HOME/.gradle"` and use `required_permissions: ["all"]`.

## Step 7 — Nike App worktree + version bump (+ Jenkins on fast path)

```bash
NIKEAPP_WT="$(dirname "$NIKEAPP_REPO")/$(basename "$NIKEAPP_REPO")--$(echo "$BRANCH" | tr '/' '-')"
```

Always pass `--nike-repo` so the script and the skill point at the same checkout.

Branch on `$NEEDS_INTEGRATION` only to control **Jenkins timing** — both paths queue a build:

- **NEEDS_INTEGRATION=false** — bump, push, and **trigger Jenkins now** (Step 7). Skip Steps 8 and 9.

```bash
"$SCRIPTS/setup-nikeapp-worktree.sh" \
  --version "$SNAPSHOT" \
  --branch "$BRANCH" \
  --nike-repo "$NIKEAPP_REPO"
```

- **NEEDS_INTEGRATION=true** — bump and push only; **defer Jenkins to Step 9** so integration edits land first.

```bash
"$SCRIPTS/setup-nikeapp-worktree.sh" \
  --version "$SNAPSHOT" \
  --branch "$BRANCH" \
  --nike-repo "$NIKEAPP_REPO" \
  --no-trigger-jenkins
```

`setup-nikeapp-worktree.sh` creates `$NIKEAPP_WT`, bumps `Versions.mamba`, commits, pushes with `--no-verify`, and (unless `--no-trigger-jenkins`) triggers Jenkins with `BRANCH=$BRANCH` automatically.

## Step 8 — Integration changes (only when `NEEDS_INTEGRATION=true`)

Inspect Nike App equivalents in `$NIKEAPP_WT`:

- `buildSrc/src/main/kotlin/Depends.kt` — already bumped by Step 7; do **not** count toward "integration changes made".
- Hilt / DI: `app/src/main/java/com/nike/mynike/**/di/**`, `*Module*.kt`, navigation entry points under `app/src/main/java/com/nike/mynike/navigation/mamba/`.

Apply fixes in `$NIKEAPP_WT`. Track whether any file beyond `Depends.kt` changed:

```bash
INTEGRATION_CHANGES="$(git -C "$NIKEAPP_WT" diff --name-only HEAD -- ':!buildSrc/src/main/kotlin/Depends.kt')"
```

If `$INTEGRATION_CHANGES` is non-empty, commit and open a draft Nike App PR (template path is absolute so it works from any CWD):

```bash
"$SCRIPTS/lib/commit-and-push.sh" \
  --repo "$NIKEAPP_WT" \
  --message "Integrate Mamba $SNAPSHOT."

NIKEAPP_PR="$("$SCRIPTS/lib/open-draft-pr.sh" \
  --repo nike-internal/mpe.app.nikeapp-android \
  --head "$BRANCH" \
  --title "Integrate Mamba $SNAPSHOT" \
  --body-template "$MAMBA_REPO/.github/pr-templates/nikeapp-snapshot.md" \
  --var snapshot="$SNAPSHOT" \
  --var companion_pr="<mamba-pr-url-if-any>" \
  --var smoke_test_area="<area under test>")"
```

If `$INTEGRATION_CHANGES` is empty, **skip** the Nike App PR.

## Step 9 — Trigger Jenkins (integration path only)

Run when Step 7 used `--no-trigger-jenkins` (`NEEDS_INTEGRATION=true`). This is the **deferred** Jenkins trigger — required after Step 8 so the build includes any integration fixes.

```bash
"$SCRIPTS/lib/trigger-jenkins.sh" \
  --job "/job/Consumer/job/Nike_App/job/Android/job/Dev/job/NikeApp-Manual-Debug" \
  --param "BRANCH=$BRANCH"
```

NikeApp-Manual-Debug is parameterized — `BRANCH` is required.

**Always run Step 9 on the integration path** — even when Step 8 made no edits beyond `Depends.kt` and no Nike App PR was opened.

**Do not run Step 9 when Step 7 already triggered Jenkins** (`NEEDS_INTEGRATION=false`) — that would queue a duplicate build.

## Closeout — report to the user

Copy this checklist into your final message. Mark skipped items explicitly.

| Item | Value |
|------|-------|
| Mamba branch | `$BRANCH` |
| Mamba worktree | `$WT` |
| SNAPSHOT version | `$SNAPSHOT` |
| Nike App worktree | `$NIKEAPP_WT` |
| Integration edits needed | `$NEEDS_INTEGRATION` (true/false) |
| Nike App PR | `$NIKEAPP_PR` if opened, else **skipped** (version bump only) |
| Jenkins | **always queued** — Step 7 (fast path) or Step 9 (integration path); say which step |
| Jenkins build URL | queue item URL or job-page URL returned by the trigger |
| TestFairy install link | **manual follow-up — see below** |
| Skipped steps | e.g. "Step 8–9 skipped — no integration signals; Jenkins ran in Step 7" |

If any step failed, stop the checklist and report the failing step, command, and error output before claiming success.

## TestFairy install link — manual follow-up (~30 min after Jenkins queues)

`NikeApp-Manual-Debug` runs `publish_dev_apk` for `NikeApp` and `NikeAppCN`, both of which upload to TestFairy. **The skill does not wait for the build to finish** — blocking the local agent on a 30+ min Jenkins build is wasteful, so fetching the install link is left as a manual step the user runs (or watches Slack for) once the build completes.

Tell the user any of these will work once `NikeApp-Manual-Debug` finishes:

1. **Slack** — `post_jenkins_dev_build_complete_message_to_slack` posts the result to the configured channel after the build.
2. **Jenkins console log** — grep the finished build for the TestFairy landing page:

```bash
JOB="/job/Consumer/job/Nike_App/job/Android/job/Dev/job/NikeApp-Manual-Debug"
curl -sS -u "$JENKINS_USER:$JENKINS_API_TOKEN" \
  "https://mobile-ci.nike.com:8443$JOB/<build#>/consoleText" \
  | rg -o 'https://nike\.testfairy\.com/join/[^[:space:]]+' \
  | sort -u
```

3. **TestFairy web UI** — sign in at [nike.testfairy.com](https://nike.testfairy.com) and find the NikeApp dev app for the branch.

> **Future automation:** a long-running cloud agent could poll Jenkins, scrape the console log on success, and post the TestFairy URL back. Until that exists, keep this as a manual lookup so the local agent never blocks on Jenkins.
