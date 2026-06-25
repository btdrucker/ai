---
name: draft-jira-tickets
description: Draft Jira epics and stories for a body of work in the ACTIV Jira project. Use when the user asks to write, draft, or create Jira tickets, stories, or epics for a feature, refactor, or work stream.
disable-model-invocation: true
---

# Draft Jira Tickets

Draft tickets to a markdown file for review before submitting to Jira.

## Output file

Create (or overwrite) `JIRA_TICKETS_DRAFT.md` in a logical location near the work being described (e.g. alongside a `CHANGES.md`).

## Ticket structure

Every work stream gets **one Epic** plus **one or more Stories** linked to it.

### Epic

| Field | Guidance |
|-------|----------|
| Project | Always `ACTIV` |
| Type | Epic |
| Epic Name | Matches the Summary |
| Summary | Short, general — describes the theme, not a list of tasks |
| Description | 2–4 sentences on the user value and motivation. No implementation details. |
| Applicable Platform/s | Android · iOS · Wear OS · watchOS (multi-select, include only relevant ones) |
| Application/s | NRC · NTC (multi-select, include only relevant ones) |

### Story

| Field | Guidance |
|-------|----------|
| Project | Always `ACTIV` |
| Type | Story |
| Summary | One sentence describing the user-observable behavior |
| Description | What the user can do / see / experience. No code, files, or technical layers. |
| Epic Link | Reference to the parent Epic |
| Applicable Platform/s | Same multi-select as Epic |
| Application/s | Same multi-select as Epic |

## Definition of a work stream

A work stream is a body of work that ships fully in a single app version. If the work stream spans multiple apps or platforms, different binaries may ship on their own release schedule, but all work for a given app ships together in one version.

## Rules

- **No implementation details** — never mention code, files, classes, functions, databases, APIs, or technical architecture in any ticket.
- **User-observable only** — describe what the user sees, does, or experiences.
- **Be specific** — avoid vague phrases like "sensible default" or "may be affected". Name the exact values, options, or outcomes visible to the user.
- **Stories by behavior, not by layer** — one story covers the full end-to-end behavior (e.g. "User can log elevation gain"). Never split a story by technical layer (e.g. not "network layer", "database layer", "UI layer" as separate stories).
- **Input fields** — for any user-editable field, call out: input type (numeric, text, etc.), maximum length if applicable, how focus is triggered, and when the Save/CTA button becomes enabled or disabled.
- **Save/CTA enablement** — distinguish between "enables when any field has a value" (add flows) and "enables when any field differs from its saved value" (edit flows).
- **Epic is general** — the epic describes the theme; the stories list the specifics.
- **UI-heavy work** — note in the description that screenshots are attached; do not try to describe the UI in prose. Write it as a present-tense statement ("Screenshots are attached.") so it remains accurate once the images are added and no editing is needed.
- **No Acceptance Criteria field** — all content goes in Description.

## Markdown template

```markdown
## Epic — [Epic Name]

**Project:** ACTIV
**Type:** Epic
**Epic Name:** [Epic Name]
**Summary:** [Short theme statement]
**Applicable Platform/s:** Android
**Application/s:** NRC

**Description:**
[2–4 sentences on user value and motivation.]

---

## Story N — [Behavior description]

**Project:** ACTIV
**Type:** Story
**Epic Link:** [Epic Name]
**Summary:** [One-sentence user-observable behavior]
**Applicable Platform/s:** Android
**Application/s:** NRC

**Description:**
[What the user can do or see. No technical details.]

---
```

## Jira custom field reference

When submitting tickets via the MCP tool, use these field IDs and exact option values:

| Draft field | Jira field name | Custom field ID | Type |
|---|---|---|---|
| Epic Name | Epic Name | `customfield_12941` | string |
| Epic Link | Epic Link | `customfield_12940` | epic key (e.g. `ACTIV-123`) |
| Applicable Platform/s | Applicable Platforms | `customfield_10246` | multiselect array |
| Application/s | Application/s | `customfield_31828` | multiselect array |

**Valid option values — must match exactly:**

- `customfield_10246` (Applicable Platforms): `"Android"`, `"iOS"`, `"Wear OS"`, `"watchOS"`
- `customfield_31828` (Application/s): `"NRC"`, `"NTC"`

Multiselect fields are passed as an array of `{"value": "..."}` objects, e.g.:
```json
"customfield_10246": [{"value": "Android"}, {"value": "iOS"}]
```

**Creation order:**
1. Create the Epic first (to get its key).
2. Create Stories with `customfield_12940` set to the Epic's key, or use `jira_link_to_epic` after creation.

## Process

1. All tickets go in the **ACTIV** project. No need to ask the user for a project key.
2. Read the work description (e.g. `CHANGES.md`, conversation context, or the user's summary).
3. Identify the overarching theme → write the Epic.
4. Identify each distinct user-observable behavior → write one Story per behavior, numbered sequentially (Story 1, Story 2, …) so individual stories can be referenced by number.
5. Write all tickets to `JIRA_TICKETS_DRAFT.md`, including the **Project** field on every ticket.
6. Present a brief summary of what was drafted and invite the user to review and request changes.
