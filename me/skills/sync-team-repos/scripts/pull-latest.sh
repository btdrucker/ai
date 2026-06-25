#!/usr/bin/env bash
# Pull latest for all team repos.
# - Clones any missing repos (serial, silent if nothing to clone)
# - Fetches + pulls all repos in parallel (captured output, printed as table)
#
# Usage: pull-latest.sh [--dry-run]
#
# Reads repo list from ~/.cursor/data/team-repos.json
# Expects each entry to have: org, repo, localPath

set -euo pipefail

REPOS_FILE="${HOME}/.cursor/data/team-repos.json"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true
TMPDIR_BASE=$(mktemp -d)
trap 'rm -rf "$TMPDIR_BASE"' EXIT

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed. Run: brew install jq" >&2
  exit 1
fi

if [[ ! -f "$REPOS_FILE" ]]; then
  echo "ERROR: Repo list not found at $REPOS_FILE" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 1: Clone missing repos (serial, only print on clone/fail)
# ---------------------------------------------------------------------------
CLONE_FAILED=()

while IFS= read -r entry; do
  ORG=$(echo "$entry" | jq -r '.org')
  REPO=$(echo "$entry" | jq -r '.repo')
  RAW_PATH=$(echo "$entry" | jq -r '.localPath')
  LOCAL_PATH="${RAW_PATH/#\~/$HOME}"

  [[ -d "$LOCAL_PATH/.git" ]] && continue

  PARENT_DIR=$(dirname "$LOCAL_PATH")
  mkdir -p "$PARENT_DIR"

  if $DRY_RUN; then
    echo "[dry-run] would clone: git@github.com:${ORG}/${REPO}.git -> $LOCAL_PATH"
    continue
  fi

  echo "Cloning $ORG/$REPO ..."
  if ! git clone "git@github.com:${ORG}/${REPO}.git" "$LOCAL_PATH" 2>&1; then
    echo "  ❌ Failed to clone $REPO"
    CLONE_FAILED+=("$REPO")
  fi
done < <(jq -c '.[]' "$REPOS_FILE")

# ---------------------------------------------------------------------------
# Phase 2+3: Fetch + pull all repos in parallel, capture output per-repo
# ---------------------------------------------------------------------------

# Result files: <tmpdir>/<repo>.result  contains "STATUS|DETAIL"
# STATUS: pulled | up-to-date | skipped-branch | skipped-dirty | failed

process_repo() {
  local ORG="$1"
  local REPO="$2"
  local LOCAL_PATH="$3"
  local DRY_RUN="$4"
  local OUT_FILE="$5"

  # Write a default so the file always exists even on unexpected exit
  echo "failed|unexpected error" > "$OUT_FILE"
  set +e

  if [[ ! -d "$LOCAL_PATH/.git" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "dry-run|would clone first" > "$OUT_FILE"
    else
      echo "failed|not cloned" > "$OUT_FILE"
    fi
    return
  fi

  # Detect default branch (local ref, fall back to gh api)
  DEFAULT_BRANCH=""
  RAW_REF=$(git -C "$LOCAL_PATH" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null || true)
  if [[ -n "$RAW_REF" ]]; then
    DEFAULT_BRANCH="${RAW_REF#refs/remotes/origin/}"
  elif command -v gh &>/dev/null; then
    DEFAULT_BRANCH=$(gh api "repos/$ORG/$REPO" --jq '.default_branch' 2>/dev/null || true)
    # Cache result for next time
    if [[ -n "$DEFAULT_BRANCH" ]]; then
      git -C "$LOCAL_PATH" remote set-head origin "$DEFAULT_BRANCH" 2>/dev/null || true
    fi
  fi
  [[ -z "$DEFAULT_BRANCH" ]] && DEFAULT_BRANCH="main"

  CURRENT_BRANCH=$(git -C "$LOCAL_PATH" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

  # Check dirty state
  if ! git -C "$LOCAL_PATH" diff --quiet 2>/dev/null || \
     ! git -C "$LOCAL_PATH" diff --cached --quiet 2>/dev/null; then
    echo "skipped-dirty|${CURRENT_BRANCH} (uncommitted changes)" > "$OUT_FILE"
    return
  fi

  # Not on default branch
  if [[ "$CURRENT_BRANCH" != "$DEFAULT_BRANCH" ]]; then
    # Still fetch so remote refs are up to date
    git -C "$LOCAL_PATH" fetch --all --quiet 2>/dev/null || true
    BEHIND=$(git -C "$LOCAL_PATH" rev-list --count "HEAD..origin/${DEFAULT_BRANCH}" 2>/dev/null || echo "?")
    echo "skipped-branch|${CURRENT_BRANCH} (${BEHIND} commits behind ${DEFAULT_BRANCH})" > "$OUT_FILE"
    return
  fi

  # On default branch, clean — fetch + pull
  if $DRY_RUN; then
    echo "dry-run|would pull ${DEFAULT_BRANCH}" > "$OUT_FILE"
    return
  fi

  git -C "$LOCAL_PATH" fetch --all --quiet 2>/dev/null
  BEFORE=$(git -C "$LOCAL_PATH" rev-parse HEAD)
  git -C "$LOCAL_PATH" pull --ff-only --quiet 2>/dev/null
  AFTER=$(git -C "$LOCAL_PATH" rev-parse HEAD)

  if [[ "$BEFORE" == "$AFTER" ]]; then
    echo "up-to-date|${DEFAULT_BRANCH}" > "$OUT_FILE"
  else
    COUNT=$(git -C "$LOCAL_PATH" rev-list --count "${BEFORE}..${AFTER}")
    echo "pulled|${DEFAULT_BRANCH} (+${COUNT} commits)" > "$OUT_FILE"
  fi
}

export -f process_repo

# Launch all repos in parallel
PIDS=()
REPOS_ORDER=()

while IFS= read -r entry; do
  ORG=$(echo "$entry" | jq -r '.org')
  REPO=$(echo "$entry" | jq -r '.repo')
  RAW_PATH=$(echo "$entry" | jq -r '.localPath')
  LOCAL_PATH="${RAW_PATH/#\~/$HOME}"
  OUT_FILE="$TMPDIR_BASE/${REPO}.result"

  process_repo "$ORG" "$REPO" "$LOCAL_PATH" "$DRY_RUN" "$OUT_FILE" &
  PIDS+=($!)
  REPOS_ORDER+=("$ORG|$REPO|$LOCAL_PATH")
done < <(jq -c '.[]' "$REPOS_FILE")

# Wait for all parallel jobs
for PID in "${PIDS[@]}"; do
  wait "$PID" || true
done

# ---------------------------------------------------------------------------
# Print results table
# ---------------------------------------------------------------------------
echo ""
printf "%-45s %s\n" "REPO" "STATUS"
printf "%-45s %s\n" "----" "------"

PULL_FAILED=()

for entry in "${REPOS_ORDER[@]}"; do
  IFS='|' read -r ORG REPO LOCAL_PATH <<< "$entry"
  OUT_FILE="$TMPDIR_BASE/${REPO}.result"

  if [[ ! -f "$OUT_FILE" ]]; then
    printf "%-45s %s\n" "$REPO" "❌ no result"
    PULL_FAILED+=("$REPO")
    continue
  fi

  IFS='|' read -r STATUS DETAIL < "$OUT_FILE"
  case "$STATUS" in
    pulled)          printf "%-45s %s\n" "$REPO" "✅ $DETAIL" ;;
    up-to-date)      printf "%-45s %s\n" "$REPO" "— up to date ($DETAIL)" ;;
    skipped-branch)  printf "%-45s %s\n" "$REPO" "⏭️  $DETAIL" ;;
    skipped-dirty)   printf "%-45s %s\n" "$REPO" "⚠️  dirty: $DETAIL" ;;
    dry-run)         printf "%-45s %s\n" "$REPO" "🔍 $DETAIL" ;;
    failed)          printf "%-45s %s\n" "$REPO" "❌ $DETAIL"
                     PULL_FAILED+=("$REPO") ;;
    *)               printf "%-45s %s\n" "$REPO" "❓ unknown: $STATUS|$DETAIL" ;;
  esac
done

echo ""

TOTAL_FAILED=$(( ${#CLONE_FAILED[@]} + ${#PULL_FAILED[@]} ))
[[ $TOTAL_FAILED -gt 0 ]] && exit 1 || exit 0
