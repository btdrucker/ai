#!/usr/bin/env python3
"""Generate a Slack canvas markdown table from ~/.cursor/data/team-repos.json."""

import json
from pathlib import Path

DATA = Path.home() / ".cursor" / "data" / "team-repos.json"
SLACK_BASE = "https://nike.enterprise.slack.com/archives"
GITHUB_BASE = "https://github.com"

PLATFORM_LABELS = {"android": "Android", "ios": "iOS", "both": "Android & iOS"}


def row(repo: dict) -> str:
    name = repo["repo"]
    org = repo["org"]
    platform = PLATFORM_LABELS.get(repo.get("platform", "both"), "Android & iOS")
    gh_link = f"[{name}]({GITHUB_BASE}/{org}/{name})"
    ch_id = repo.get("slackChannelId")
    ch_name = repo.get("slackChannel")
    if ch_id and ch_name:
        slack_link = f"[#{ch_name}]({SLACK_BASE}/{ch_id})"
    else:
        slack_link = "—"
    return f"| {gh_link} | {platform} | {slack_link} |"


def table(repos: list) -> str:
    header = "| Repository | Platform | Slack Channel |\n|---|---|---|"
    rows = "\n".join(row(r) for r in repos)
    return f"{header}\n{rows}"


def main():
    repos = json.loads(DATA.read_text())
    own = [r for r in repos if r.get("role") == "own"]
    use = [r for r in repos if r.get("role") == "use"]

    print("## Repos We Own\n")
    print(table(own))
    print("\n## Repos We Use / Contribute To\n")
    print(table(use))


if __name__ == "__main__":
    main()
