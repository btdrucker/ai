#!/usr/bin/env bash
# discover-qa-transition.sh
# Discover QA transition ID for a ticket via Atlassian MCP helper output.
#
# Usage:
#   discover-qa-transition.sh <TICKET_KEY>
#
# Prints transition_id and name when QA transition is found.
# Agent should prefer calling jira_get_transitions via MCP directly;
# this script documents known defaults.

set -euo pipefail

TICKET_KEY="${1:-}"
TICKET_KEY="$(echo "$TICKET_KEY" | tr '[:lower:]' '[:upper:]')"

if [[ -z "$TICKET_KEY" ]]; then
  echo "Usage: $0 <TICKET_KEY>"
  exit 1
fi

PROJECT="${TICKET_KEY%%-*}"

echo "ticket_key=${TICKET_KEY}"
echo "project=${PROJECT}"
echo ""
echo "Known QA transition for NIKEAPPUI (verify with jira_get_transitions):"
echo "transition_qa_id=61"
echo "transition_qa_name=QA"
echo ""
echo "Agent: call jira_get_transitions issue_key=${TICKET_KEY} and confirm QA transition before running mamba-qa-ready.sh"
