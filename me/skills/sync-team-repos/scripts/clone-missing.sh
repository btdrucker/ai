#!/usr/bin/env bash
# Clone any team repos that don't exist locally yet.
# Usage: clone-missing.sh [--dry-run]
#
# Reads repo list from ~/.cursor/data/team-repos.json
# Expects each entry to have: org, repo, localPath

set -euo pipefail

REPOS_FILE="${HOME}/.cursor/data/team-repos.json"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed. Run: brew install jq" >&2
  exit 1
fi

if [[ ! -f "$REPOS_FILE" ]]; then
  echo "ERROR: Repo list not found at $REPOS_FILE" >&2
  exit 1
fi

CLONED=()
SKIPPED=()
FAILED=()

while IFS= read -r entry; do
  ORG=$(echo "$entry" | jq -r '.org')
  REPO=$(echo "$entry" | jq -r '.repo')
  RAW_PATH=$(echo "$entry" | jq -r '.localPath')
  LOCAL_PATH="${RAW_PATH/#\~/$HOME}"

  if [[ -d "$LOCAL_PATH/.git" ]]; then
    SKIPPED+=("$REPO")
    continue
  fi

  PARENT_DIR=$(dirname "$LOCAL_PATH")
  mkdir -p "$PARENT_DIR"

  if $DRY_RUN; then
    echo "[dry-run] would clone: git@github.com:${ORG}/${REPO}.git -> $LOCAL_PATH"
    CLONED+=("$REPO (dry-run)")
    continue
  fi

  echo "Cloning $ORG/$REPO ..."
  if git clone "git@github.com:${ORG}/${REPO}.git" "$LOCAL_PATH" 2>&1; then
    CLONED+=("$REPO")
  else
    FAILED+=("$REPO")
  fi
done < <(jq -c '.[]' "$REPOS_FILE")

echo ""
echo "### ✅ Cloned (${#CLONED[@]})"
for r in "${CLONED[@]}"; do echo "  - $r"; done

echo ""
echo "### ⏭️  Skipped — already exists (${#SKIPPED[@]})"
for r in "${SKIPPED[@]}"; do echo "  - $r"; done

echo ""
echo "### ❌ Failed (${#FAILED[@]})"
for r in "${FAILED[@]}"; do echo "  - $r"; done

[[ ${#FAILED[@]} -gt 0 ]] && exit 1 || exit 0
