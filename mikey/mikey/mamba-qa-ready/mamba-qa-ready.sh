#!/usr/bin/env bash
# mamba-qa-ready.sh
# Move a ticket to QA with "Test ready!" comment, transition, and unassign.
#
# Usage:
#   mamba-qa-ready.sh <TICKET_KEY> <TESTFAIRY_LINK> [TRANSITION_ID] [MAMBA_PR_URL] [NIKEAPP_BRANCH_URL]
#
# Examples:
#   mamba-qa-ready.sh NIKEAPPUI-237 "https://nike.testfairy.com/join/..." 61
#   mamba-qa-ready.sh NIKEAPPUI-237 "https://nike.testfairy.com/join/..." 61 "https://github.com/.../pull/456" "https://github.com/.../tree/feature/..."
#
# Notes:
#   - TICKET_KEY is uppercased automatically
#   - TRANSITION_ID: agent should discover via jira_get_transitions (MCP) before calling
#   - Uses dis CLI for Jira API calls

set -euo pipefail

TICKET_KEY="${1:-}"
TESTFAIRY_LINK="${2:-}"
TRANSITION_ID="${3:-}"
MAMBA_PR_URL="${4:-}"
NIKEAPP_BRANCH_URL="${5:-}"

if [[ -z "$TICKET_KEY" || -z "$TESTFAIRY_LINK" ]]; then
  echo "Usage: $0 <TICKET_KEY> <TESTFAIRY_LINK> [TRANSITION_ID] [MAMBA_PR_URL] [NIKEAPP_BRANCH_URL]"
  exit 1
fi

TICKET_KEY="$(echo "$TICKET_KEY" | tr '[:lower:]' '[:upper:]')"

echo "Processing ${TICKET_KEY} for QA..."

# Build comment
COMMENT="Test ready!

build here ->
NikeApp-Android-Feature-World
${TESTFAIRY_LINK}"

if [[ -n "$MAMBA_PR_URL" ]]; then
  COMMENT="${COMMENT}

PR -> ${MAMBA_PR_URL}"
fi

if [[ -n "$NIKEAPP_BRANCH_URL" ]]; then
  COMMENT="${COMMENT}

nike app branch used for testing -> ${NIKEAPP_BRANCH_URL}"
fi

echo ""
echo "Step 1: Adding comment..."
echo "---"
echo "$COMMENT"
echo "---"

dis call jira_add_comment "{\"issue_key\": \"$TICKET_KEY\", \"comment\": $(echo "$COMMENT" | jq -Rs .)}" > /dev/null 2>&1 || {
  echo "Error: Failed to add comment"
  exit 1
}
echo "  ✓ Comment added"

if [[ -z "$TRANSITION_ID" ]]; then
  echo ""
  echo "TRANSITION_REQUIRED"
  echo "Call jira_get_transitions for ${TICKET_KEY} via Atlassian MCP,"
  echo "find the QA transition, then re-run with transition ID as 3rd argument."
  exit 2
fi

echo ""
echo "Step 2: Transitioning to QA (transition_id=${TRANSITION_ID})..."
dis call jira_transition_issue "{\"issue_key\": \"$TICKET_KEY\", \"transition_id\": \"${TRANSITION_ID}\"}" > /dev/null 2>&1 || {
  echo "Error: Failed to transition ticket to QA"
  exit 1
}
echo "  ✓ Transitioned to QA"

echo ""
echo "Step 3: Unassigning ticket..."
dis call jira_update_issue "{\"issue_key\": \"$TICKET_KEY\", \"fields\": {\"assignee\": null}}" > /dev/null 2>&1 || {
  echo "Warning: Failed to unassign ticket (non-fatal)"
}
echo "  ✓ Unassigned"

echo ""
echo "✓ ${TICKET_KEY} is ready for QA"
echo "  - Comment: Test ready! + TestFairy link"
echo "  - Status: QA"
echo "  - Assignee: none"
