# DIS Reference

## GitHub CLI without Homebrew (direct download)

macOS ARM64:

```bash
GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest \
  | grep -o '"tag_name": "v[^"]*"' | cut -d'"' -f4 | sed 's/^v//')
curl -sL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_macOS_arm64.zip" -o /tmp/gh.zip
unzip -o /tmp/gh.zip -d /tmp/gh && mkdir -p ~/.local/bin && install /tmp/gh/*/bin/gh ~/.local/bin/
gh auth login
```

---

## CLI Commands

| Command | Purpose |
|---------|---------|
| `dis` | Start MCP server on stdio (IDE calls this automatically) |
| `dis call <tool> [json]` | Call any MCP tool from the terminal |
| `dis setup <target>` | Install agent configs for an IDE |
| `dis upgrade [--check]` | Self-upgrade the binary |
| `dis capture <mode>` | Save learnings to knowledge base |
| `dis security-audit` | Scan for hardcoded secrets, API keys, absolute paths |
| `dis auth login [--env qa\|prod]` | Okta OAuth login (enables write operations) |
| `dis auth status` | Check Okta token status and expiry |
| `dis auth refresh` | Manually refresh expired Okta token |
| `dis auth slack [--profile name]` | Extract Slack credentials from Chrome (macOS) |
| `dis auth logout` | Delete stored Okta credentials |
| `dis serve` | Start HTTP MCP daemon (for Nike-managed Cursor) |
| `dis serve status` | Check if the HTTP daemon is running |
| `dis serve stop` | Stop the HTTP daemon |
| `dis serve restart` | Restart the HTTP daemon |

### CLI examples

```bash
# Call MCP tools from the terminal
dis call jira_get_ticket '{"ticketKey": "TG-123"}'
dis call rag_get_learnings '{}' --pretty
dis call confluence_search '{"cql": "space=MYSPACE"}'

# IDE setup
dis setup mcp cursor          # Register MCP server for Nike-managed Cursor
dis setup cursor              # Install bundled agent files for Cursor
dis setup claude              # Install agents for Claude Code
dis setup agents              # List all available agents
dis setup agents a11y-auditor # Install a specific agent

# Upgrade
dis upgrade          # Download and install latest version
dis upgrade --check  # Check only, don't install

# Knowledge capture
dis capture --implementation --ticket TG-123 --time 120 --files src/api/jira.rs
dis capture --pr-review --pr 42 --issues "Missing error handling"
dis capture --principle --summary "Pure functions first" --pattern "architecture"

# Security scanning
dis security-audit                          # Scan staged git files
dis security-audit --files=src/config.rs    # Scan specific files
dis security-audit --no-interactive         # CI-friendly mode

# Auth
dis auth login            # Login to prod (default)
dis auth login --env qa   # Login to QA environment
dis auth slack                    # Default Chrome profile
dis auth slack --profile "Profile 1"  # Named Chrome profile
```

---

## MCP Tools by Domain

### JIRA (20 tools)

| Tool | Description |
|------|-------------|
| `jira_get_ticket` | Get ticket details by key |
| `jira_search` | Search tickets using JQL |
| `jira_create_ticket` | Create a new ticket |
| `jira_update_ticket` | Update an existing ticket |
| `jira_add_comment` | Add a comment to a ticket |
| `jira_get_transitions` | Get available status transitions |
| `jira_transition_ticket` | Move ticket to a new status |
| `jira_assign_ticket` | Assign a ticket to a user |
| `jira_list_projects` | List all accessible projects |
| `jira_get_project` | Get project details |
| `jira_list_boards` | List boards by project |
| `jira_get_sprints` | Get sprints for a board |
| `jira_get_active_sprint` | Get the currently active sprint |
| `jira_add_to_sprint` | Move issues into a sprint |
| `jira_clone_ticket` | Clone ticket to another project |
| `jira_link_tickets` | Link two tickets together |
| `jira_get_velocity` | Get velocity metrics for a board |
| `jira_get_issue_types` | Get issue types for a project |
| `jira_get_editable_fields` | Get editable fields for a ticket |
| `jira_add_attachment` | Upload a file attachment to a ticket |

### Confluence (8 tools)

| Tool | Description |
|------|-------------|
| `confluence_get_page` | Get page content by ID |
| `confluence_search` | Search pages using CQL |
| `confluence_create_page` | Create a new page |
| `confluence_update_page` | Update an existing page |
| `confluence_list_spaces` | List all spaces |
| `confluence_get_space` | Get space details |
| `confluence_get_space_pages` | List pages in a space |
| `confluence_format_content` | Convert markdown to storage format |

### Jenkins (15 tools)

Jenkins tools only appear when Jenkins env vars are configured (see SKILL.md > Configure Credentials > Jenkins).

| Tool | Description |
|------|-------------|
| `jenkins_list_instances` | List configured instances |
| `jenkins_list_jobs` | List jobs in a folder |
| `jenkins_get_job` | Get job details |
| `jenkins_get_job_config` | Get raw XML configuration |
| `jenkins_get_build` | Get build details |
| `jenkins_get_build_log` | Get console output |
| `jenkins_search_build_log` | Search log for matching lines |
| `jenkins_get_build_history` | Recent build history |
| `jenkins_get_build_stages` | Pipeline stage breakdown |
| `jenkins_get_build_stats` | Success rate and duration stats |
| `jenkins_trigger_build` | Trigger a new build |
| `jenkins_create_job` | Create job from XML config |
| `jenkins_get_pending_input` | Get pending input actions for a build |
| `jenkins_submit_input` | Submit proceed/abort on a pending input |
| `jenkins_replay_build` | Replay a build with modified Jenkinsfile |

### RAG / Learnings (3 tools)

| Tool | Description |
|------|-------------|
| `rag_save_learning` | Save learning to knowledge files |
| `rag_get_learnings` | Read learnings by scope |
| `rag_get_system_knowledge` | Get system knowledge from seed/org data |

### Slack (6 base + 4 enhanced tools)

6 base tools work with Okta proxy or browser auth. 4 enhanced tools require `dis auth slack`.

| Tool | Description | Auth |
|------|-------------|------|
| `slack_history` | Get channel message history | base |
| `slack_thread` | Get thread replies for a message | base |
| `slack_channels` | Search and discover channels by name | base |
| `slack_user_info` | Get user profile by user ID | base |
| `slack_post` | Post a message to a channel or thread | base |
| `slack_user_search` | Search for users by name or email | base |
| `slack_search` | Search messages by keyword | browser |
| `slack_dm_open` | Open a 1:1 DM channel with a user | browser |
| `slack_draft` | Create a draft message for review | browser |
| `slack_scan_secrets` | Scan messages for leaked credentials | browser |



For troubleshooting, see the Troubleshooting section in [SKILL.md](SKILL.md).
