#!/usr/bin/env bash
# discover-nikeappui-jira-fields.sh
# Output NIKEAPPUI Jira field defaults discovered via Atlassian MCP.
#
# Usage:
#   discover-nikeappui-jira-fields.sh [issue_type]
#
# issue_type: Story (default) | Bug | Task

set -euo pipefail

ISSUE_TYPE="${1:-Story}"

echo "project_key=NIKEAPPUI"
echo "project_name=Nike App UI"
echo "assignee=Michael.Pinaud@nike.com"
echo "squad_field=customfield_30343"
echo "squad_name=Mamba Core"
echo "work_category_field=customfield_10040"
echo "platform_field=customfield_10246"
echo "platform_name=Android"
echo "acceptance_criteria_field=customfield_10241"
echo "epic_link_field=customfield_12940"
echo "jira_base_url=https://jira.nike.com/browse"

case "$ISSUE_TYPE" in
  Bug)
    echo "work_category_name=Defect"
    ;;
  Story|Task|*)
    echo "work_category_name=Feature"
    ;;
esac

echo ""
echo "# Workflow transitions (verify with jira_get_transitions):"
echo "transition_dev_ready=41"
echo "transition_dev=31"
echo "transition_pull_request=51"
echo "transition_qa=61"
echo "transition_done=91"
echo ""
echo "# Suggested epics when user does not specify (search for best match):"
echo "suggested_epic_NIKEAPPUI-993=Nike App Mamba Integration Work"
echo "suggested_epic_NIKEAPPUI-60=Spotlight V2 | Android"
echo "suggested_epic_NIKEAPPUI-61=Shop Carousel | Android"
