---
name: create-nikeappui-ticket
description: Create a JIRA ticket in the NIKEAPPUI project for Nike App UI squad work. Defaults to Mamba Core squad, Feature/Defect work category, Android platform. Use when creating Nike App UI engineering tickets.
---

# Create Nike App UI Ticket

Create a JIRA ticket in the **NIKEAPPUI** project (Nike App UI) with squad defaults.

## Tool preference

- Use the Atlassian MCP server JIRA tools directly.
- Do not use `dis` for this skill.

## Defaults (always applied unless overridden)

- **Project:** `NIKEAPPUI` (Nike App UI)
- **Assignee:** Michael Pinaud (`Michael.Pinaud@nike.com`) unless the user explicitly asks for someone else
- **Ticket key format:** Always uppercase (`NIKEAPPUI-123`)
- **Squad:** Mamba Core (`customfield_30343`: `{"name": "Mamba Core"}`)
- **Work Category:** `Feature` for Story/Task, `Defect` for Bug (`customfield_10040`)
- **Applicable Platforms:** Android for Android work (`customfield_10246`: `[{"name": "Android"}]`)
- **Acceptance Criteria field:** `customfield_10241` (never embed in description)

Load defaults from script:

```bash
bash ~/.cursor/skills/create-nikeappui-ticket/discover-nikeappui-jira-fields.sh [Story|Bug|Task]
```

## Epic (no single team default)

Unlike EXTE, NIKEAPPUI has feature-area epics. **Ask or infer** from the request:

| Epic | When to use |
|------|-------------|
| `NIKEAPPUI-993` | General Nike App Mamba integration work |
| `NIKEAPPUI-60` | Spotlight V2 Android |
| `NIKEAPPUI-61` | Shop Carousel Android |
| `NIKEAPPUI-70` | Android Mamba IT2 Bottom Nav |

Search when unsure:

```text
jira_search jql="project = NIKEAPPUI AND issuetype = Epic AND summary ~ \"Android\" ORDER BY updated DESC"
```

Link via `jira_link_to_epic` after creation.

## Instructions

1. **Parse the user's request** for summary, description, issue type, assignee override, epic override.

2. **Create the ticket** using `jira_create_issue`:
   - `project_key`: `NIKEAPPUI`
   - `issue_type`: Story / Bug / Task
   - `summary`: from user request
   - `assignee`: `Michael.Pinaud@nike.com` unless overridden
   - `description`: JIRA wiki markup — never include Acceptance Criteria here
   - `additional_fields`:
     ```json
     {
       "customfield_30343": {"name": "Mamba Core"},
       "customfield_10040": {"name": "Feature"},
       "customfield_10246": [{"name": "Android"}]
     }
     ```
     Use `"Defect"` for Bug issue type.

3. **Acceptance Criteria** → `customfield_10241` when present in the request.

4. **Link to epic** via `jira_link_to_epic` (user-specified or best match from table above).

5. **Set workflow placement** after creation:
   - Use `jira_get_transitions`, then `jira_transition_issue`
   - NIKEAPPUI workflow mapping:
     | Requested state | Transition name | Typical ID |
     |-----------------|-----------------|------------|
     | To Do / Dev Ready | Dev Ready | 41 |
     | In Progress | Dev | 31 |
     | Pull Request | Pull Request | 51 |
     | QA | QA | 61 |
     | Done | Done | 91 |
   - Always verify IDs with `jira_get_transitions` — do not hardcode without checking.

6. **Confirm** with uppercase ticket key and link:
   ```
   https://jira.nike.com/browse/NIKEAPPUI-XXX
   ```

## Examples

User: "Create a ticket for aligning product wall carousel thumbnails"

→ `NIKEAPPUI-XXXX` Story, Mamba Core, Feature, Android, linked to best-matching epic.

User: "Create a bug for shop nav pill prefix under NIKEAPPUI-61"

→ `NIKEAPPUI-XXXX` Bug, Work Category Defect, linked to `NIKEAPPUI-61`.
