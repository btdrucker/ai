#!/usr/bin/env bash
# discover-commit-style.sh
# Infer commit message format from recent git history.
#
# Usage:
#   discover-commit-style.sh [ticket-key]
#
# Output (stdout):
#   format=<ticket|conventional|freeform>
#   example=<one-line example>
#   ticket_key=<uppercase ticket key if provided or inferred>

set -euo pipefail

INPUT_TICKET="${1:-}"
INPUT_TICKET="$(echo "$INPUT_TICKET" | tr '[:lower:]' '[:upper:]')"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "format=freeform"
  echo "example=Update implementation"
  exit 0
fi

LOG="$(git log --oneline -30 2>/dev/null || true)"

ticket_count=0
conventional_count=0

while IFS= read -r line; do
  msg="${line#* }"
  if [[ "$msg" =~ ^[A-Z][A-Z0-9]+-[0-9]+: ]]; then
    ticket_count=$((ticket_count + 1))
  elif [[ "$msg" =~ ^(feat|fix|chore|docs|refactor|test|build|ci|perf|style)(\([^)]+\))?: ]]; then
    conventional_count=$((conventional_count + 1))
  fi
done <<< "$LOG"

if [[ "$ticket_count" -ge "$conventional_count" && "$ticket_count" -gt 0 ]]; then
  FORMAT="ticket"
  EXAMPLE="$(echo "$LOG" | grep -E '^[0-9a-f]+ [A-Z][A-Z0-9]+-[0-9]+:' | head -1 | sed 's/^[0-9a-f]* //')"
  [[ -z "$EXAMPLE" ]] && EXAMPLE="NIKEAPPUI-237: Short description of change"
elif [[ "$conventional_count" -gt 0 ]]; then
  FORMAT="conventional"
  EXAMPLE="$(echo "$LOG" | grep -E '^[0-9a-f]+ (feat|fix|chore|docs|refactor|test|build|ci|perf|style)(\([^)]+\))?:' | head -1 | sed 's/^[0-9a-f]* //')"
  [[ -z "$EXAMPLE" ]] && EXAMPLE="fix(scope): Short description"
else
  FORMAT="freeform"
  EXAMPLE="$(echo "$LOG" | head -1 | sed 's/^[0-9a-f]* //')"
  [[ -z "$EXAMPLE" ]] && EXAMPLE="Short description of change"
fi

TICKET_KEY="$INPUT_TICKET"
if [[ -z "$TICKET_KEY" ]]; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [[ "$branch" =~ ([A-Z][A-Z0-9]+-[0-9]+) ]]; then
    TICKET_KEY="${BASH_REMATCH[1]}"
  fi
fi

echo "format=${FORMAT}"
echo "example=${EXAMPLE}"
echo "ticket_key=${TICKET_KEY}"
