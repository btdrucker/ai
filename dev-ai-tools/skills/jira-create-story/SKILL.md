---
name: jira-create-story
description: >
  Create a Jira story on the SRPLT board with all required fields pre-filled.
  Use when the user wants to create a Jira story, ticket, or issue for Search
  Platform, SRPLT, or the Search Engineering team. Trigger phrases: "create a
  story", "new ticket", "new Jira story", "file a ticket", "create SRPLT".
---

# Create SRPLT Jira Story

Creates a properly configured Jira story in the SRPLT project (Search Platform)
with squad, epic, sprint, fix version, and labels pre-filled.

## Related skills

- **`jira`** -- Jira operations gateway (MCP prerequisite check, fallback logic, error handling)
- **`dis`** -- DIS installation and configuration (fallback MCP server)

## Workflow

### Step 1: Verify MCP server

Follow the MCP prerequisite check from the `jira` skill: try
`user-atlassian-mcp-server` first, fall back to
`user-nike-dev-integration-system-mcp` (DIS) if unavailable. If using DIS,
note the tool name differences (see `jira` skill mapping table) --
in particular, use `jira_create_ticket` instead of `jira_create_issue`.

### Step 2: Fetch dynamic data

Fetch all dynamic data **in parallel** before asking any questions:

**Active and future sprints** (board 25116 = "Search Platform (SRPLT + SAD)"):
```
jira_get_sprints_from_board(board_id="25116", state="active")
jira_get_sprints_from_board(board_id="25116", state="future")
```

**Active epics:**
```
jira_search(
  jql="project = SRPLT AND issuetype = Epic AND status != Done ORDER BY updated DESC",
  fields="summary,status",
  limit=20
)
```

**Recently used epics** (best signal for which epics the team is actively filing under):
```
jira_search(
  jql="project = SRPLT AND issuetype = Story AND 'Epic Link' is not EMPTY ORDER BY created DESC",
  fields="customfield_12940",
  limit=20
)
```
Extract unique epic keys from `customfield_12940` values.

**Fix versions:**
```
jira_get_project_versions(project_key="SRPLT")
```

### Step 3: Resolve fix version

Nike uses fiscal year quarters as fix versions. The fiscal year starts June 1.

| Calendar months | Fiscal quarter |
|-----------------|----------------|
| Jun -- Aug      | Q1             |
| Sep -- Nov      | Q2             |
| Dec -- Feb      | Q3             |
| Mar -- May      | Q4             |

From the versions list, find the unreleased version matching the current fiscal
quarter (pattern: `FY__ Q_`). For example, if today is June 2026, the current
quarter is FY27 Q1.

### Step 4: Gather information

Use AskQuestion to collect inputs. If the user already provided a summary or
description in their prompt, skip asking for those fields.

**Round 1 -- required fields:**

- **Summary/title** -- free text. If the user provided context in conversation
  (e.g. while working on code or discussing an issue), synthesize a concise
  summary from that context and confirm it.

- **Squad** -- present as a choice:
  - Phoenix (default -- most stories use this)
  - SEAL

- **Work Category** -- **required by Jira**. Present as a choice:
  - Feature (new user-facing capability)
  - Technical Investment (tech debt, upgrades, observability, infra)
  - Production Support (ops tasks, support requests, incident follow-ups)

- **Epic** -- present epics in two groups:
  1. **Recently used** (from the recent-stories query) -- show first
  2. **Other active epics** (from the epic search, minus those already shown)
  3. A "None / Skip" option

  If the story context clearly fits an epic, suggest it at the top.

**Round 2 -- optional fields (ask in a second pass):**

- **Description** -- suggest user-story format (see template below). Accept
  freeform text too.
- **Labels** -- freeform, comma-separated. Mention common labels observed on
  the board for reference (see label reference below).
- **Sprint** -- present active sprint first, then future sprints, then
  "Backlog (no sprint)". Default: Backlog.
- **Priority** -- default "TBD". Options: TBD, Critical, Major, Minor, Trivial.
- **Story points** -- numeric. Common values: 1, 2, 3, 5, 8, 13.
- **Assignee** -- default: unassigned. Accept display name or email.

Present round 2 as optional -- tell the user they can skip all of these and
the story will be created with sensible defaults (no description, no labels,
backlog sprint, TBD priority, no points, unassigned).

### Step 5: Create the story

Use `jira_create_issue`:

```
project_key: "SRPLT"
issue_type: "Story"
summary: <user-provided>
description: <user-provided or omit>
assignee: <user-provided or omit>
additional_fields: {
  "fixVersions": [{"name": "<resolved fix version>"}],
  "customfield_10040": {"value": "<work category>"},
  "customfield_30343": {"value": "<squad>"},
  "customfield_12940": "<epic_key or omit>",
  "customfield_11541": <sprint_id as number or omit>,
  "customfield_10013": <story_points as number or omit>,
  "labels": [<labels array or omit>],
  "priority": {"name": "<priority>"}
}
```

**Custom field reference:**

| Field ID           | Name          | Format                                              | Required |
|--------------------|---------------|------------------------------------------------------|----------|
| `customfield_10040`| Work Category | `{"value": "Feature"}`, `"Technical Investment"`, or `"Production Support"` | **Yes** |
| `customfield_30343`| Squad         | `{"value": "Phoenix"}` or `{"value": "SEAL"}`       | **Yes** |
| `customfield_12940`| Epic Link     | Epic key string, e.g. `"SRPLT-979"`                 | No       |
| `customfield_11541`| Sprint        | Sprint ID as integer                                 | No       |
| `customfield_10013`| Story Points  | Number                                               | No       |

Omit any field the user did not provide a value for. Do not send null values --
just leave the key out of `additional_fields`.

### Step 6: Confirm

After creation, display:

- Issue key and URL: `https://jira.nike.com/browse/<KEY>`
- Summary of all fields that were set
- Suggest next steps: "Add more details in Jira", "Assign to someone",
  "Move to the current sprint"

---

## Summary title conventions

SRPLT stories follow a `Prefix | Description` naming pattern. Common prefixes:

| Prefix       | When to use                                    |
|--------------|------------------------------------------------|
| `Kingpin`    | Changes to Kingpin (search query service)      |
| `Typeahead`  | Search typeahead / autocomplete changes        |
| `OCSP`       | Online customer search platform changes        |
| `Envoy`      | Product feed ingestion (Envoy service)         |
| `Maestro`    | Product feed orchestration (Maestro service)   |
| `KirbyV2`    | Feed processing (KirbyV2 service)              |
| `PW API`     | Product Wall API changes                       |
| `Bronto`     | Bronto ranking / AIML integration              |
| `Research`   | Research / investigation tasks                 |
| `Spike`      | Time-boxed investigation or proof of concept   |

If the story clearly relates to a specific service, suggest the prefix. If not,
a plain title is fine.

## Description template

Suggest this format when the user wants help writing a description:

```
h3. Purpose
<Why this work is needed>

h3. Scope
* Item 1
* Item 2

h3. Acceptance Criteria
* Criterion 1
* Criterion 2

h3. References
* [SRPLT-XXX|https://jira.nike.com/browse/SRPLT-XXX]
```

Or the simpler user-story format:

```
As a [role], I want [capability], so that [benefit].

h3. Acceptance Criteria
* Criterion 1
* Criterion 2
```

## Label reference

Labels are freeform. Common labels observed on the SRPLT board:

| Category   | Examples                                                    |
|------------|-------------------------------------------------------------|
| Tech area  | `aiml`, `bronto`, `elasticsearch`, `search`, `ios`, `android` |
| Feature    | `mvi-personalization`, `search-personalization`, `product-wall`, `OCSP` |
| Priority   | `priority-high`                                             |
| Type       | `tech-debt`, `investigation`, `intake_request`, `cost-optimization`, `decommission` |
| Phase      | `search-personalization-ph1`, `search-personalization-ph2`, `scale` |
| Process    | `collection-staleness`, `feature-flag`, `clickmod-instrumentation` |

## Board reference

- **Board**: Search Platform (SRPLT + SAD) (ID: `25116`, scrum)
- **Alt board**: Phoenix - Search Platform Scrum (ID: `24210`, scrum)
- **Project**: SRPLT (Search Platform)
- **Jira URL**: https://jira.nike.com/browse/SRPLT
