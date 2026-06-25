#!/usr/bin/env bash
# Add Jira autolink references to all team repos (idempotent).
#
# Adds these autolinks to every repo in ~/.cursor/data/team-repos.json:
#   NIKEAPPUI-  → https://jira.nike.com/browse/NIKEAPPUI-<num>
#   NIKEAPCORE- → https://jira.nike.com/browse/NIKEAPCORE-<num>
#   XTAK-       → https://jira.nike.com/browse/XTAK-<num>
#
# Usage:
#   add-autolinks.sh [--dry-run]
#
# Requires: gh CLI authenticated with admin access to repos, jq installed
# NOTE: Run from your own terminal — gh does not pick up its keychain token
#       from Cursor's shell.

set -euo pipefail

REPOS_FILE="${HOME}/.cursor/data/team-repos.json"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# ---------------------------------------------------------------------------
# Autolinks to add: "PREFIX|URL_TEMPLATE" (all alphanumeric)
# ---------------------------------------------------------------------------
AUTOLINKS=(
  "NIKEAPPUI-|https://jira.nike.com/browse/NIKEAPPUI-<num>"
  "NIKEAPCORE-|https://jira.nike.com/browse/NIKEAPCORE-<num>"
  "XTAK-|https://jira.nike.com/browse/XTAK-<num>"
)

# ---------------------------------------------------------------------------
# Prereq checks
# ---------------------------------------------------------------------------
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed. Run: brew install jq" >&2
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI is required but not installed. Run: brew install gh" >&2
  exit 1
fi

if [[ ! -f "$REPOS_FILE" ]]; then
  echo "ERROR: Repo list not found at $REPOS_FILE" >&2
  exit 1
fi

if ! gh auth status &>/dev/null; then
  echo "ERROR: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Helper: check if an autolink prefix already exists for this repo
# ---------------------------------------------------------------------------
autolink_exists() {
  local ORG="$1" REPO="$2" PREFIX="$3"
  gh api "repos/${ORG}/${REPO}/autolinks" --jq '.[].key_prefix' 2>/dev/null \
    | grep -qxF "$PREFIX"
}

# ---------------------------------------------------------------------------
# Per-repo result tracking
# repo_results["org/repo"] = "added:N|skipped:N|failed:PREFIX1 PREFIX2"
# We'll build a simple parallel arrays approach instead (bash 3 compat)
# ---------------------------------------------------------------------------
REPO_NAMES=()
declare -A REPO_ADDED REPO_SKIPPED REPO_FAILED_LINKS REPO_NO_ADMIN

TOTAL=$(jq 'length' "$REPOS_FILE")
INDEX=0

while IFS= read -r entry; do
  INDEX=$(( INDEX + 1 ))
  ORG=$(echo "$entry" | jq -r '.org')
  REPO=$(echo "$entry" | jq -r '.repo')
  KEY="${ORG}/${REPO}"
  REPO_NAMES+=("$KEY")
  REPO_ADDED[$KEY]=0
  REPO_SKIPPED[$KEY]=0
  REPO_FAILED_LINKS[$KEY]=""
  REPO_NO_ADMIN[$KEY]=false

  echo "[$( printf '%2d' "$INDEX")/${TOTAL}] ${KEY}"

  for autolink in "${AUTOLINKS[@]}"; do
    IFS='|' read -r PREFIX URL_TPL <<< "$autolink"
    printf "         %-14s " "${PREFIX}"

    # Idempotency check (runs even in dry-run so the report is accurate)
    if autolink_exists "$ORG" "$REPO" "$PREFIX"; then
      echo "⏭️  already exists"
      REPO_SKIPPED[$KEY]=$(( ${REPO_SKIPPED[$KEY]} + 1 ))
      continue
    fi

    if $DRY_RUN; then
      echo "🔍 would add → ${URL_TPL}"
      REPO_ADDED[$KEY]=$(( ${REPO_ADDED[$KEY]} + 1 ))
      continue
    fi

    # Attempt to add; capture stderr for diagnosis
    ERR_TMP=$(mktemp)
    if gh api \
        --method POST \
        "repos/${ORG}/${REPO}/autolinks" \
        --field key_prefix="${PREFIX}" \
        --field url_template="${URL_TPL}" \
        --field is_alphanumeric=false \
        --silent 2>"$ERR_TMP"; then
      echo "✅ added"
      REPO_ADDED[$KEY]=$(( ${REPO_ADDED[$KEY]} + 1 ))
    else
      ERR_BODY=$(cat "$ERR_TMP")
      rm -f "$ERR_TMP"
      # 403/422 with "Must have admin rights" → mark as no-admin
      if echo "$ERR_BODY" | grep -qi "admin\|forbidden\|403"; then
        echo "🔒 no admin access"
        REPO_NO_ADMIN[$KEY]=true
      else
        echo "❌ failed"
      fi
      REPO_FAILED_LINKS[$KEY]="${REPO_FAILED_LINKS[$KEY]} ${PREFIX}"
    fi
    rm -f "$ERR_TMP"
  done

done < <(jq -c '.[]' "$REPOS_FILE")

# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------
TOTAL_ADDED=0
TOTAL_SKIPPED=0
REPOS_ALL_OK=()
REPOS_PARTIAL=()
REPOS_NO_ADMIN=()
REPOS_OTHER_FAIL=()

for KEY in "${REPO_NAMES[@]}"; do
  A=${REPO_ADDED[$KEY]}
  S=${REPO_SKIPPED[$KEY]}
  F=${REPO_FAILED_LINKS[$KEY]}
  TOTAL_ADDED=$(( TOTAL_ADDED + A ))
  TOTAL_SKIPPED=$(( TOTAL_SKIPPED + S ))

  if [[ -z "$F" ]]; then
    REPOS_ALL_OK+=("$KEY  (added: ${A}, already existed: ${S})")
  elif ${REPO_NO_ADMIN[$KEY]}; then
    REPOS_NO_ADMIN+=("$KEY  (added: ${A}, skipped: ${S}, blocked:${F})")
  else
    REPOS_OTHER_FAIL+=("$KEY  (added: ${A}, skipped: ${S}, failed:${F})")
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  AUTOLINK REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "  Autolink operations: %d added, %d already existed\n" "$TOTAL_ADDED" "$TOTAL_SKIPPED"
echo ""

if [[ ${#REPOS_ALL_OK[@]} -gt 0 ]]; then
  echo "  ✅ Fully configured (${#REPOS_ALL_OK[@]} repos)"
  for r in "${REPOS_ALL_OK[@]}"; do echo "     $r"; done
  echo ""
fi

if [[ ${#REPOS_NO_ADMIN[@]} -gt 0 ]]; then
  echo "  🔒 No admin access — links not added (${#REPOS_NO_ADMIN[@]} repos)"
  for r in "${REPOS_NO_ADMIN[@]}"; do echo "     $r"; done
  echo ""
fi

if [[ ${#REPOS_OTHER_FAIL[@]} -gt 0 ]]; then
  echo "  ❌ Unexpected failures (${#REPOS_OTHER_FAIL[@]} repos)"
  for r in "${REPOS_OTHER_FAIL[@]}"; do echo "     $r"; done
  echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_FAILED=$(( ${#REPOS_NO_ADMIN[@]} + ${#REPOS_OTHER_FAIL[@]} ))
[[ $TOTAL_FAILED -gt 0 ]] && exit 1 || exit 0
