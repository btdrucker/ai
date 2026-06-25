#!/usr/bin/env bash
# checkout-ticket-branch.sh
# Sync default branch and create mpinau/<TICKET-KEY> or mpinau/<TICKET-KEY>/<slug>
#
# Usage:
#   checkout-ticket-branch.sh <TICKET-KEY> [slug]
#
# Examples:
#   checkout-ticket-branch.sh NIKEAPPUI-237
#   checkout-ticket-branch.sh nikeappui-237 product-wall-carousel
#
# Environment:
#   BRANCH_PREFIX  default: mpinau

set -euo pipefail

TICKET_KEY="${1:-}"
SLUG="${2:-}"
BRANCH_PREFIX="${BRANCH_PREFIX:-mpinau}"

if [[ -z "$TICKET_KEY" ]]; then
  echo "Error: TICKET-KEY is required"
  echo "Usage: $0 <TICKET-KEY> [slug]"
  exit 1
fi

# Enforce ALL CAPS for ticket key
TICKET_KEY="$(echo "$TICKET_KEY" | tr '[:lower:]' '[:upper:]')"

if [[ -n "$SLUG" ]]; then
  SLUG="$(echo "$SLUG" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed 's/[^a-z0-9-]//g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')"
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository"
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Error: no origin remote configured"
  exit 1
fi

git fetch origin

DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)"
if [[ -z "$DEFAULT_BRANCH" ]]; then
  if git show-ref --verify --quiet refs/remotes/origin/main; then
    DEFAULT_BRANCH="main"
  elif git show-ref --verify --quiet refs/remotes/origin/master; then
    DEFAULT_BRANCH="master"
  else
    DEFAULT_BRANCH="main"
  fi
fi

STASHED="no"
if [[ -n "$(git status --porcelain)" ]]; then
  git stash push -u -m "checkout-ticket-branch: WIP before sync"
  STASHED="yes"
fi

CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT" == "$DEFAULT_BRANCH" ]]; then
  git pull origin "$DEFAULT_BRANCH"
else
  git checkout "$DEFAULT_BRANCH"
  git pull origin "$DEFAULT_BRANCH"
fi

if [[ -n "$SLUG" ]]; then
  BRANCH_NAME="${BRANCH_PREFIX}/${TICKET_KEY}/${SLUG}"
else
  BRANCH_NAME="${BRANCH_PREFIX}/${TICKET_KEY}"
fi

if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "Error: branch already exists: ${BRANCH_NAME}"
  if [[ "$STASHED" == "yes" ]]; then
    echo "Stash preserved. Restore with: git stash pop"
  fi
  exit 1
fi

git checkout -b "$BRANCH_NAME"

if [[ "$STASHED" == "yes" ]]; then
  if ! git stash pop; then
    echo "Warning: stash pop produced conflicts — resolve manually"
    exit 1
  fi
fi

echo ""
echo "Branch ready: ${BRANCH_NAME}"
echo "Default branch synced: ${DEFAULT_BRANCH}"
git status --short --branch
