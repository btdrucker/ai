---
name: ops-query-splunk
description: >
  Query Nike Splunk logs for Search Engineering services using the Splunk
  REST API. Use when the user asks to search Splunk, investigate logs, look
  up service activity, trace a request, check traffic, or debug a service
  by name and environment. Supports free-form SPL queries and pre-built
  templates for all Search team Waffle EC2 services.
---

# Query Splunk

Runs Splunk searches against `https://nike.splunkcloud.com:8089` via the REST API.

**Service names, query recipes, result formatting, and the Splunk Web UI link:** see [REFERENCE.md](REFERENCE.md).

## Related skills

- **`search-kb`** -- identify which service to query and its architecture context
- **`vscode-workspace`** -- verify which service repos are in the active workspace

## Authentication

Requires `SPLUNK_JWT_TOKEN` in the environment. If not set, the script exits with an error.

Resolve `SKILL_DIR` as the directory containing this `SKILL.md` file.

As an alternative to the env var, place the raw token value in `${SKILL_DIR}/splunk_token.txt`.

If the project-local token file is missing, the script falls back to `~/.cursor/skills/query-splunk/splunk_token.txt`.

### If the token is expired or the query returns a 401 / authentication error

1. Tell the user: "Your Splunk token has expired. Please generate a new one:"
   1. Go to `https://nike.splunkcloud.com/en-US/app/initialize_nike/welcome_nike`
   2. Settings -> Tokens -> New Token -> Create
   3. Copy the token immediately -- it is only shown once
2. Ask the user to paste the new token into the chat
3. Write the new token to `${SKILL_DIR}/splunk_token.txt` (overwrite the old value). If you want it shared across repos, also update `~/.cursor/skills/query-splunk/splunk_token.txt`.
4. Retry the query

Signs the token may be expired:

- Script exits with a non-zero code and output contains `401`, `403`, or `"Invalid token"`
- The JWT `exp` field (base64-decode the middle segment) is in the past

## Running a query

### Free-form SPL

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --spl "index=np-app app=wholesaleeventscomposerv1 error" \
  --time-range -1h \
  --max-results 50
```

### Named service template

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --service wholesaleeventscomposerv1 \
  --env test \
  --filter "error" \
  --time-range -4h \
  --max-results 100
```

Output is JSON printed to stdout. Progress dots go to stderr.

## Arguments

| Argument        | Default | Description                                             |
| --------------- | ------- | ------------------------------------------------------- |
| `--spl`         | --      | Full SPL query string (free-form mode)                  |
| `--service`     | --      | Named service (template mode; see [REFERENCE.md](REFERENCE.md)) |
| `--env`         | `test`  | `test` or `prod`                                        |
| `--filter`      | --      | Additional filter appended to template query            |
| `--time-range`  | `-1h`   | Splunk earliest time (e.g. `-4h`, `-1d`, `2026-05-21T07:00:00`) |
| `--latest-time` | `now`   | Splunk latest time (default `now`)                      |
| `--max-results` | `100`   | Max results to return                                   |

## Index quick reference

| Service family                   | env=test  | env=prod |
| -------------------------------- | --------- | -------- |
| Waffle EC2 services (most Search services) | `np-app` | `app` |

All Waffle EC2 services use the same `np-app` / `app` index. The primary filter is the `app=<serviceName>` field embedded in each service's log4j pattern.
