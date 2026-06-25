#!/usr/bin/env bash
# push-with-hooks.sh
# Push current branch and capture hook output for monitoring.
#
# Usage:
#   push-with-hooks.sh [remote] [branch]
#
# Defaults: remote=origin, branch=current HEAD
#
# Exit codes:
#   0 = push succeeded
#   1 = push failed (hooks or remote rejection)
#
# Output log: /tmp/push-with-hooks-<branch>.log

set -euo pipefail

REMOTE="${1:-origin}"
BRANCH="${2:-$(git rev-parse --abbrev-ref HEAD)}"
LOG="/tmp/push-with-hooks-${BRANCH//\//-}.log"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository"
  exit 1
fi

echo "Pushing ${REMOTE}/${BRANCH}..."
echo "Log: ${LOG}"

set +e
git push "$REMOTE" "$BRANCH" 2>&1 | tee "$LOG"
EXIT_CODE=${PIPESTATUS[0]}
set -e

if [[ "$EXIT_CODE" -eq 0 ]]; then
  echo ""
  echo "PUSH_SUCCEEDED"
  git status --short --branch
  exit 0
fi

echo ""
echo "PUSH_FAILED exit=${EXIT_CODE}"

if grep -qE "spotless|Spotless" "$LOG"; then
  echo "HINT: spotless failure — run pre-push-fix.sh then amend and retry"
fi
if grep -qE "detekt|Detekt" "$LOG"; then
  echo "HINT: detekt failure — fix reported issues before retry"
fi
if grep -qE "apiCheck|kompare" "$LOG"; then
  echo "HINT: apiCheck failure — review public API changes"
fi
if grep -qE "checkSortDependencies|SortDependencies" "$LOG"; then
  echo "HINT: dependency sort failure — run pre-push-fix.sh"
fi

exit "$EXIT_CODE"
