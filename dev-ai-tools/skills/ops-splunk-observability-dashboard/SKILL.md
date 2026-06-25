---
name: ops-splunk-observability-dashboard
description: >
  Open and analyze the OCSP Splunk Observability (SignalFx) dashboard in the
  IDE browser. Browse service dashboards (Kingpin, Envoy, CompositeRules,
  ConceptZero, etc.) and run API-based metric analysis. Use when the user
  mentions OCSP dashboard, Splunk dashboard, SignalFx dashboard, observability
  metrics, or asks to view/analyze a Search service dashboard.
---

# Splunk Observability Dashboard

Opens the OCSP dashboard group in the IDE browser and supports API-based
metric analysis via the SignalFx REST and SignalFlow APIs.

**Full API reference, endpoints, URL patterns, and SignalFlow docs:** see
[REFERENCE.md](REFERENCE.md).

## Related skills

- **`search-kb`** -- identify which service to view and its architecture context
- **`ops-query-splunk`** -- query Splunk Cloud logs (separate product from Observability)

---

## Step 1: Okta SSO

1. Open `https://nike.okta.com` in the IDE browser with `position: "beside"`
2. Tell the user: "The Okta login page is open in the browser panel. It may
   take a while to load -- please sign in and let me know when you're done."
3. Wait for the user to confirm -- do NOT attempt to detect SSO completion
   automatically (MFA, passkeys, redirect behavior varies). The Okta page
   can be slow to load and may show "The page has timed out" -- the user
   may need to refresh the browser panel.

## Step 2: Resolve and navigate to the dashboard

1. **Resolve the dashboard ID.** Resolve `SKILL_DIR` as the directory
   containing this `SKILL.md` file. Run:

   ```bash
   python3 "${SKILL_DIR}/scripts/signalfx_query.py" --list-dashboards
   ```

   This fetches the current list of dashboards (tabs) in the OCSP group by
   calling the SignalFx REST API. It requires a valid API token.

   If the script fails because no token is available, fall through to the
   token retrieval flow in Step 3 below, then retry.

2. **If the user specified a service** (e.g. "show me envoy"), match the
   name from the `--list-dashboards` output (case-insensitive) and navigate
   directly to that tab. Skip the tab picker in step 3.

3. **If no specific service was requested**, navigate to the Kingpin
   dashboard (the default), then present the full list of tabs via
   `AskQuestion`: "Which tab would you like me to navigate to?"

4. Navigate the browser to the selected dashboard URL:

   ```
   https://app.signalfx.com/#/dashboard/{dashboardId}?groupId=D6EXYIbAYAA&configId={configId}
   ```

   The `dashboardId` and `configId` values come from the `--list-dashboards`
   output. The user can see the dashboard in the browser panel -- no
   screenshot needed.

---

## Step 3: API-based analysis (on demand)

Triggered when the user asks analytical questions like "what's the RPM?",
"compare CPU across hosts", "show me the SignalFlow program for this chart",
"are there any active incidents?", etc.

Use the API to answer questions instead of taking screenshots -- the API
provides structured data that can be analyzed programmatically.

### Token retrieval (lazy)

The token is only needed when the user requests API analysis. Retrieve it
automatically -- do not ask the user for permission.

1. Check for an existing token in this order:
   - Environment variable `SIGNALFX_TOKEN`
   - `${SKILL_DIR}/signalfx_token.txt`
   - `~/.cursor/skills/ops-splunk-observability-dashboard/signalfx_token.txt`

2. If no token is found, retrieve it automatically:
   1. Navigate to `https://app.signalfx.com/#/myprofile` in the IDE browser
   2. Use `browser_snapshot` to find the "Show User API Access Token" button
      and click it
   3. Read the token value from the DOM snapshot (it appears as a readonly
      textbox)
   4. Save the token to `${SKILL_DIR}/signalfx_token.txt`

3. If an API call returns 401 / expired token: re-grab the token using the
   same browser flow. The user should already be SSO'd from Step 1, so
   navigating to the profile page should work without re-auth.

### Sandbox permissions

The script calls `api.signalfx.com` and `stream.signalfx.com`, which are
outside the default sandbox allowlist. To avoid repeated authorization
prompts, **batch multiple queries into a single shell call** using `&&`
or `;` so the user only approves once. Use `required_permissions:
["full_network"]` on the shell call.

### Available API commands

All commands use `python3 "${SKILL_DIR}/scripts/signalfx_query.py"`.

#### Dashboard and chart inspection

```bash
# List all dashboards (tabs) in the OCSP group
--list-dashboards

# Fetch a dashboard with all chart definitions and SignalFlow programs
--dashboard {dashboardId}

# Fetch a single chart (name, SignalFlow program, display options)
--chart {chartId}
```

#### Live metric data (SignalFlow execution)

```bash
# Execute a SignalFlow program -- returns actual metric values
--execute "data('cpu.utilization', filter=filter('app', 'envoy')).mean().publish(label='cpu')" --duration 5m

# With custom resolution
--execute "data('requests.count', rollup='rate').sum().publish()" --duration 1h --resolution 1m
```

To get live data for a specific dashboard chart: fetch the chart definition
with `--chart`, extract its `programText`, and pass it to `--execute`.

#### Detectors and incidents

```bash
# List detectors (alerting rules)
--detectors --limit 20

# List active incidents (firing alerts)
--incidents --limit 20
```

#### Metric metadata

```bash
# Look up a specific metric
--metric cpu.utilization

# Search metrics by name pattern
--search-metric "requests.*" --limit 10
```

### API details

See [REFERENCE.md](REFERENCE.md) for full endpoint documentation, SSE
response format, SignalFlow syntax, and token management details.
