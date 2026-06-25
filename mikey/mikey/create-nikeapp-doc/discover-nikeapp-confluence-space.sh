#!/usr/bin/env bash
# discover-nikeapp-confluence-space.sh
# Output Nike App UI Confluence defaults discovered via Atlassian MCP.
#
# Usage:
#   discover-nikeapp-confluence-space.sh

set -euo pipefail

echo "space_key=NDEE"
echo "space_name=Nike Digital Engineering (NDEE)"
echo "default_parent_page_id=1760200073"
echo "default_parent_title=Nike app overall flow"
echo "default_parent_url=https://confluence.nike.com/pages/viewpage.action?pageId=1760200073"
echo ""
echo "# Alternate parent for squad-wide docs:"
echo "alternate_space_key=MOBILEC"
echo "alternate_parent_page_id=431703022"
echo "alternate_parent_title=Nike App Squad"
