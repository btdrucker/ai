---
name: mamba-qa-ready
description: >-
  Full QA handoff for a Mamba feature branch: publish SNAPSHOT, bump Nike App
  Depends.kt, queue Omega-Android-Feature-Manual (DIS), poll Jenkins with
  backoff, extract TestFairy install link, and update Jira (comment, move to
  QA, unassign). QA snapshots only — not weekly release. Use when the user
  asks to hand off to QA, make a build QA-ready, or run mamba-qa-ready.
---

# Mamba QA Ready

End-to-end dev → QA handoff: **SNAPSHOT → Nike App bump (no PR) → DIS Jenkins → poll → TestFairy link → Jira**.

This is **not** the same as `test-in-nikeapp`: different Jenkins job (`Omega-Android-Feature-Manual` / DIS), never opens a Nike App PR, polls Jenkins to completion with backoff, and updates Jira.

## Rules every step must follow

- **Every `Shell` call in this skill must use `required_permissions: ["all"]`** — Gradle, Jenkins, Keychain, and Jira all need it.
- **Never auto-commit feature work with a generic message** — `WIP`, `Update`, `Fix` are forbidden. If a tree is dirty, stop and ask the user.
- **All shared values live in `$STATE`** (a JSON file). Each step reads what it needs with `jq` instead of relying on shell variables carrying across calls.
- **On any failure, stop and report the failing step** — do not continue and do not claim success.

## Step 1 — Resolve context + create state file

```bash
MAMBA_REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
[[ -n "$MAMBA_REPO" && -f "$MAMBA_REPO/gradle.properties" ]] \
  || { echo "Error: run from inside the Mamba Android repo." >&2; exit 1; }

BRANCH="$(git -C "$MAMBA_REPO" branch --show-current)"
NIKEAPP_REPO="${NIKEAPP_REPO:-$(dirname "$MAMBA_REPO")/mpe.app.nikeapp-android}"
SCRIPTS="$MAMBA_REPO/scripts"
JENKINS_JOB="${JENKINS_JOB:-/job/Consumer/job/Nike_App/job/Android/job/Dev/job/Omega-Android-Feature-Manual}"
TESTFAIRY_JOIN_APP="${TESTFAIRY_JOIN_APP:-NikeApp-Android-Feature-World}"

[[ "$BRANCH" != "main" && -n "$BRANCH" ]] \
  || { echo "Error: refuse to publish from main or detached HEAD." >&2; exit 1; }
[[ -d "$NIKEAPP_REPO/.git" || -f "$NIKEAPP_REPO/.git" ]] \
  || { echo "Error: Nike App repo not found at $NIKEAPP_REPO." >&2; exit 1; }

JIRA_TICKET=""
[[ "$BRANCH" =~ (MMBA-[0-9]+) ]] && JIRA_TICKET="${BASH_REMATCH[1]}"

mkdir -p "$MAMBA_REPO/.cursor"
STATE="$MAMBA_REPO/.cursor/mamba-qa-ready.state.json"

jq -n \
  --arg mamba_repo "$MAMBA_REPO" \
  --arg branch "$BRANCH" \
  --arg nikeapp_repo "$NIKEAPP_REPO" \
  --arg scripts "$SCRIPTS" \
  --arg jenkins_job "$JENKINS_JOB" \
  --arg testfairy_join_app "$TESTFAIRY_JOIN_APP" \
  --arg jira_ticket "$JIRA_TICKET" \
  '{mamba_repo:$mamba_repo, branch:$branch, nikeapp_repo:$nikeapp_repo,
    scripts:$scripts, jenkins_job:$jenkins_job,
    testfairy_join_app:$testfairy_join_app, jira_ticket:$jira_ticket,
    snapshot:"", wt:"", nikeapp_wt:"", queued_at:0, build_number:"",
    build_url:"", testfairy_url:"", poll_count:0, status:"started"}' \
  > "$STATE"

echo "State: $STATE"
cat "$STATE"
```

If `jira_ticket` is empty, **ask the user for it now** and update state:

```bash
jq --arg t "MMBA-XXXX" '.jira_ticket = $t' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
```

> **Read state in any later step:** `BRANCH="$(jq -r .branch "$STATE")"` etc.

## Step 2 — Credentials preflight

```bash
"$(jq -r .scripts "$STATE")/lib/check-creds.sh"
```

Exit ≠ 0: surface the report and **stop**.

## Step 3 — Mamba worktree + record `$WT`

```bash
MAMBA_REPO="$(jq -r .mamba_repo "$STATE")"
BRANCH="$(jq -r .branch "$STATE")"
SCRIPTS="$(jq -r .scripts "$STATE")"

WT="$("$SCRIPTS/lib/worktree-add.sh" --repo "$MAMBA_REPO" --branch "$BRANCH" --symlink-local-properties)"

jq --arg wt "$WT" '.wt = $wt' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
```

## Step 4 — Push guard

The SNAPSHOT embeds the commit hash; unpushed commits produce unresolvable artifacts. **Never auto-commit feature work with a generic message** — that loses author intent.

```bash
WT="$(jq -r .wt "$STATE")"
SCRIPTS="$(jq -r .scripts "$STATE")"

DIRTY="$(git -C "$WT" status --porcelain)"
if [[ -n "$DIRTY" ]]; then
    echo "Dirty tree — stopping. Files:" >&2
    echo "$DIRTY" >&2
    exit 1
fi

AHEAD="$(git -C "$WT" rev-list --count "@{u}..HEAD" 2>/dev/null || echo 0)"
if [[ "$AHEAD" -gt 0 ]]; then
    "$SCRIPTS/lib/commit-and-push.sh" --repo "$WT" --push-only
fi
```

On dirty: list the files to the user and stop. Ask them to commit with a real message (or run `push-mamba-pr`), then re-run this skill.

## Step 5 — Detect integration signals (informational)

```bash
WT="$(jq -r .wt "$STATE")"
API_DIFF="$(git -C "$WT" diff origin/main...HEAD --name-only -- '**/*.api' 2>/dev/null || true)"
DI_DIFF="$(git -C "$WT" diff origin/main...HEAD --name-only -- \
  'app/src/**/di/**' 'app/src/**/*Module*.kt' 'app/src/**/*HiltModules*.kt' 2>/dev/null || true)"

NEEDS_INTEGRATION=false
[[ -n "$API_DIFF" || -n "$DI_DIFF" ]] && NEEDS_INTEGRATION=true

jq --argjson n "$NEEDS_INTEGRATION" '.needs_integration = $n' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
echo "NEEDS_INTEGRATION=$NEEDS_INTEGRATION"
[[ "$NEEDS_INTEGRATION" == true ]] && echo -e "$API_DIFF\n$DI_DIFF"
```

## Step 6 — Publish SNAPSHOT

~3 minutes. Set `block_until_ms` to at least `300000`.

```bash
WT="$(jq -r .wt "$STATE")"
SCRIPTS="$(jq -r .scripts "$STATE")"

SNAPSHOT="$(GRADLE_USER_HOME="$HOME/.gradle" "$SCRIPTS/publish-mamba-snapshot.sh" --repo "$WT")"
[[ -n "$SNAPSHOT" ]] || { echo "Error: publish returned empty version." >&2; exit 1; }

jq --arg s "$SNAPSHOT" '.snapshot = $s' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
echo "SNAPSHOT=$SNAPSHOT"
```

## Step 7 — Nike App worktree + version bump (no Jenkins yet)

We defer Jenkins to Step 9 so `queued_at` is recorded immediately before trigger. **No Nike App PR for QA snapshots.**

```bash
SNAPSHOT="$(jq -r .snapshot "$STATE")"
BRANCH="$(jq -r .branch "$STATE")"
NIKEAPP_REPO="$(jq -r .nikeapp_repo "$STATE")"
SCRIPTS="$(jq -r .scripts "$STATE")"

NIKEAPP_WT="$(dirname "$NIKEAPP_REPO")/$(basename "$NIKEAPP_REPO")--$(echo "$BRANCH" | tr '/' '-')"

"$SCRIPTS/setup-nikeapp-worktree.sh" \
  --version "$SNAPSHOT" \
  --branch "$BRANCH" \
  --nike-repo "$NIKEAPP_REPO" \
  --no-trigger-jenkins

jq --arg wt "$NIKEAPP_WT" '.nikeapp_wt = $wt' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"
```

Re-running this on an already-bumped worktree is a no-op (the script idempotently skips push when there's no diff).

## Step 8 — Integration edits (only if `needs_integration == true`)

```bash
NEEDS_INTEGRATION="$(jq -r .needs_integration "$STATE")"
NIKEAPP_WT="$(jq -r .nikeapp_wt "$STATE")"
SCRIPTS="$(jq -r .scripts "$STATE")"
SNAPSHOT="$(jq -r .snapshot "$STATE")"

if [[ "$NEEDS_INTEGRATION" == true ]]; then
    # Apply Nike App wiring fixes in $NIKEAPP_WT:
    #   - app/src/main/java/com/nike/mynike/**/di/**
    #   - *Module*.kt, navigation/mamba/
    # Then:
    INTEGRATION_CHANGES="$(git -C "$NIKEAPP_WT" diff --name-only HEAD -- ':!buildSrc/src/main/kotlin/Depends.kt')"
    if [[ -n "$INTEGRATION_CHANGES" ]]; then
        "$SCRIPTS/lib/commit-and-push.sh" \
          --repo "$NIKEAPP_WT" \
          --message "Integrate Mamba $SNAPSHOT for QA."
    fi
fi
```

Skip this step entirely if `needs_integration` is `false`. **No PR opens either way.**

## Step 9 — Queue DIS Jenkins build

Record `queued_at` **immediately before** the trigger — `wait-jenkins-build.sh --since` uses it to find the right build number.

```bash
SCRIPTS="$(jq -r .scripts "$STATE")"
JENKINS_JOB="$(jq -r .jenkins_job "$STATE")"
BRANCH="$(jq -r .branch "$STATE")"

QUEUED_AT="$(date +%s)"
jq --argjson q "$QUEUED_AT" '.queued_at = $q | .status = "queued"' "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

"$SCRIPTS/lib/trigger-jenkins.sh" --job "$JENKINS_JOB" --param "BRANCH=$BRANCH"
```

## Step 10 — Poll Jenkins with backoff

The agent **must not** hold one shell open for 30+ min. Use a one-shot background sleeper that emits a sentinel on completion, end the turn, and the wake notification resumes Step 10.

### 10a — Pick the next wait

```bash
POLL_COUNT="$(jq -r .poll_count "$STATE")"
case "$POLL_COUNT" in
    0) WAIT_SECONDS=900 ;;   # first check: 15 min after queue
    1) WAIT_SECONDS=600 ;;   # second: +10 min
    *) WAIT_SECONDS=300 ;;   # every later check: +5 min
esac
echo "POLL_COUNT=$POLL_COUNT  WAIT_SECONDS=$WAIT_SECONDS"
```

### 10b — Arm the wake

Run this with `block_until_ms: 0` and `notify_on_output: { pattern: "^AGENT_LOOP_WAKE_mamba_qa", reason: "Jenkins poll wake" }`. Do **not** start a second sleeper while one is running — check `terminals/` first.

```bash
STATE_PATH="$STATE"
(
  sleep "$WAIT_SECONDS"
  echo "AGENT_LOOP_WAKE_mamba_qa {\"state\":\"$STATE_PATH\",\"action\":\"poll\"}"
) &
echo "Armed wake in $WAIT_SECONDS s. Ending turn."
```

End the turn. When the wake fires, read the JSON payload, then run step 10c with the `state` path from the payload.

### 10c — One probe on each wake

```bash
STATE="<value of \"state\" from the wake payload>"
SCRIPTS="$(jq -r .scripts "$STATE")"
JENKINS_JOB="$(jq -r .jenkins_job "$STATE")"
QUEUED_AT="$(jq -r .queued_at "$STATE")"
BRANCH="$(jq -r .branch "$STATE")"
JOIN_APP="$(jq -r .testfairy_join_app "$STATE")"

set +e
RESULT="$("$SCRIPTS/lib/wait-jenkins-build.sh" \
  --job "$JENKINS_JOB" --since "$QUEUED_AT" --branch "$BRANCH" \
  --join-app "$JOIN_APP" --check-only 2>&1)"
EXIT=$?
set -e

STATUS="$(printf '%s\n' "$RESULT" | sed -n 's/^STATUS=//p')"
BUILD_NUMBER="$(printf '%s\n' "$RESULT" | sed -n 's/^BUILD_NUMBER=//p')"
BUILD_URL="$(printf '%s\n' "$RESULT" | sed -n 's/^BUILD_URL=//p')"
TESTFAIRY_URL="$(printf '%s\n' "$RESULT" | sed -n 's/^TESTFAIRY_URL=//p')"

jq --arg bn "$BUILD_NUMBER" --arg bu "$BUILD_URL" --arg tf "$TESTFAIRY_URL" \
   '.build_number = $bn | .build_url = $bu | (if $tf != "" then .testfairy_url = $tf else . end)' \
   "$STATE" > "$STATE.tmp" && mv "$STATE.tmp" "$STATE"

echo "STATUS=$STATUS EXIT=$EXIT"
```

### 10d — Decide

| `STATUS` (exit) | Action |
|---|---|
| `BUILDING` or `NOT_FOUND` (1) | `jq '.poll_count += 1' "$STATE"` → go back to 10a → arm next wake → end turn |
| `SUCCESS` with non-empty `TESTFAIRY_URL` (0) | Mark `status = "success"` in state → go to Step 11 |
| `SUCCESS` with empty `TESTFAIRY_URL` (0) | **Stop** — TestFairy upload missing. Report `BUILD_URL` and ask the user to check the console log manually |
| `FAILURE` / `UNSTABLE` / `ABORTED` (2) | Mark `status = "failed"` → **stop** — report `BUILD_URL` |

**Max polls:** if `poll_count >= 24` (~2.5 h), stop and ask the user whether to continue (don't bump `poll_count` further automatically).

## Step 11 — Jira handoff (Atlassian MCP)

Read everything from state:

```bash
ISSUE="$(jq -r .jira_ticket "$STATE")"
BRANCH="$(jq -r .branch "$STATE")"
SNAPSHOT="$(jq -r .snapshot "$STATE")"
BUILD_URL="$(jq -r .build_url "$STATE")"
TESTFAIRY_URL="$(jq -r .testfairy_url "$STATE")"

[[ -n "$ISSUE" && -n "$TESTFAIRY_URL" && -n "$BUILD_URL" ]] \
  || { echo "Missing required state for Jira handoff." >&2; exit 1; }
```

### 11a — Add comment

Call MCP tool `jira_add_comment` with **exactly** these arguments (substitute the variables in the comment body):

```json
{
  "issue_key": "<ISSUE>",
  "comment": "## QA build ready\n\n| Field | Value |\n|-------|-------|\n| Mamba branch | `<BRANCH>` |\n| SNAPSHOT | `<SNAPSHOT>` |\n| Jenkins | [build](<BUILD_URL>) |\n| TestFairy | [Install Nike App](<TESTFAIRY_URL>) |\n\nBuilt via Omega-Android-Feature-Manual (DIS). Please install from TestFairy and verify."
}
```

If the call fails, record `comment_status = "failed"` in state and continue to 11b.

### 11b — Transition to QA

1. Call `jira_get_transitions` with `{ "issue_key": "<ISSUE>" }`. Response is an array of `{ "id": "...", "name": "..." }`.
2. From the response, pick the entry whose `name` matches (case-insensitive) one of: `Ready for QA`, `QA`, `Move to QA`, `In QA`.
3. If **no** match, **stop** and show the user the full transitions list — let them pick.
4. Call `jira_transition_issue` with:

```json
{
  "issue_key": "<ISSUE>",
  "transition_id": "<id from step 2>",
  "comment": "Build ready for QA — see TestFairy link above."
}
```

### 11c — Unassign

Call `jira_update_issue`:

```json
{
  "issue_key": "<ISSUE>",
  "fields": { "assignee": null }
}
```

If that returns an error, retry once with `{ "fields": { "assignee": { "accountId": null } } }`. If still failing, record `assignee_status = "failed"` and surface the error to the user.

## Closeout — report to the user

Read state and fill **every** row from observed values (use `✅` / `❌` exactly as you observed — do not assume success):

```bash
jq . "$STATE"
```

```
| Item              | Value                                  |
|-------------------|----------------------------------------|
| Mamba branch      | <branch>                               |
| Jira ticket       | <jira_ticket>                          |
| SNAPSHOT          | <snapshot>                             |
| Nike App worktree | <nikeapp_wt>                           |
| Jenkins build     | <build_url> (#<build_number>)          |
| TestFairy install | <testfairy_url>                        |
| Jira comment      | ✅ / ❌ (with error if ❌)              |
| Jira transition   | ✅ → <transition name> / ❌            |
| Jira unassign     | ✅ / ❌                                |
| Polls run         | <poll_count>                           |
```

If any step failed, **stop the checklist and report the failing step, command, and error output** before claiming success.

## State file reference

`$MAMBA_REPO/.cursor/mamba-qa-ready.state.json`:

| Key | Set by step | Used by |
|-----|-------------|---------|
| `mamba_repo`, `branch`, `nikeapp_repo`, `scripts`, `jenkins_job`, `testfairy_join_app`, `jira_ticket` | 1 | All later steps |
| `wt` | 3 | 4, 5, 6 |
| `needs_integration` | 5 | 8 |
| `snapshot` | 6 | 7, 8, 11 |
| `nikeapp_wt` | 7 | 8, closeout |
| `queued_at` | 9 | 10c |
| `poll_count` | 10d | 10a, closeout |
| `build_number`, `build_url`, `testfairy_url` | 10c | 11, closeout |
| `status` | 9, 10d | closeout |

If a wake payload arrives with no `state` key, re-derive `STATE` from `$MAMBA_REPO/.cursor/mamba-qa-ready.state.json` using `git rev-parse --show-toplevel`.

## TestFairy URL format

`wait-jenkins-build.sh` scans the Jenkins console for `https://nike.testfairy.com/projects/<n>/builds/<build-id>` and builds the install link:

`https://nike.testfairy.com/join/NikeApp-Android-Feature-World?id=<build-id>`

Override the join slug with `TESTFAIRY_JOIN_APP` if the team uses a different one.
