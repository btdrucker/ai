---
name: team-repos-canvas
description: Generates a Slack canvas markdown table of team repos from ~/.cursor/data/team-repos.json, with columns for Repository, Platform (Android, iOS, Android & iOS), and Slack Channel. Use when the user asks to refresh or recreate the team repos canvas, update the canvas table, or regenerate the repo list for Slack.
---

# Team Repos Canvas

Generates the markdown table for the team repos Slack canvas from `~/.cursor/data/team-repos.json`.

## Steps

1. Run the generator script:
   ```bash
   python3 ~/.cursor/skills/team-repos-canvas/scripts/generate-canvas.py
   ```

2. Show the full markdown output to the user — they will paste it into the Slack canvas at:
   `https://nike.enterprise.slack.com/docs/T08495J2Y/F0BATEGAZ7C`

3. Note any repos missing a `slackChannel` (they render as `—`) and ask the user if they want to look them up.

## Data source

`~/.cursor/data/team-repos.json` — each entry has:
- `role`: `"own"` or `"use"`
- `platform`: `"android"`, `"ios"`, or `"both"`
- `slackChannel` + `slackChannelId`: used to build the deep-link URL
- `org` + `repo`: used to build the GitHub URL

## Platform display

| JSON value | Column text |
|---|---|
| `android` | Android |
| `ios` | iOS |
| `both` | Android & iOS |
