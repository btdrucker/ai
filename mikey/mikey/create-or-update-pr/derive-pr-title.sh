#!/usr/bin/env bash
# derive-pr-title.sh
# Derive PR title as TICKET-KEY: Description from branch or latest commit.
#
# Usage:
#   derive-pr-title.sh

set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
latest_msg="$(git log -1 --pretty=%s 2>/dev/null || echo "")"

ticket=""
if [[ "$branch" =~ ([A-Z][A-Z0-9]+-[0-9]+) ]]; then
  ticket="${BASH_REMATCH[1]}"
fi

if [[ -z "$ticket" && "$latest_msg" =~ ^([A-Z][A-Z0-9]+-[0-9]+): ]]; then
  ticket="${BASH_REMATCH[1]}"
fi

if [[ -n "$ticket" && "$latest_msg" =~ ^${ticket}:\ *(.*)$ ]]; then
  echo "${ticket}: ${BASH_REMATCH[1]}"
  exit 0
fi

if [[ -n "$ticket" ]]; then
  desc="$(echo "$latest_msg" | sed -E 's/^[A-Z][A-Z0-9]+-[0-9]+:\ *//')"
  if [[ -z "$desc" || "$desc" == "$latest_msg" ]]; then
    desc="$(echo "$branch" | sed "s|.*/${ticket}/||; s|.*/${ticket}||; s|.*/||; s/-/ /g")"
    desc="$(echo "$desc" | sed 's/\b\(\w\)/\u\1/g')"
  fi
  echo "${ticket}: ${desc}"
  exit 0
fi

echo "$latest_msg"
