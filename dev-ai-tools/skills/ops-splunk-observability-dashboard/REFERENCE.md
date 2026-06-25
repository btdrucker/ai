# Splunk Observability Dashboard Reference

## API details

| Field | Value |
|-------|-------|
| Realm | `us0` |
| REST API endpoint | `https://api.signalfx.com` |
| Stream API endpoint | `https://stream.signalfx.com` |
| Auth header | `X-SF-TOKEN: {token}` |
| Org | Nike CDT - Commerce (`Chi3thvAYAQ`) |
| Dashboard group | OCSP (`D6EXYIbAYAA`) |

## REST API endpoints

All REST endpoints use `https://api.signalfx.com` as the base URL and
require the `X-SF-TOKEN` header.

### Dashboards and charts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v2/dashboardgroup/{id}` | Fetch dashboard group (lists member dashboards) |
| GET | `/v2/dashboard/{id}` | Fetch dashboard definition (lists member charts) |
| GET | `/v2/chart/{id}` | Fetch chart definition (includes SignalFlow program) |

### Detectors and incidents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v2/detector` | List detectors (query params: `limit`, `offset`, `name`, `tags`) |
| GET | `/v2/detector/{id}` | Fetch a specific detector |
| GET | `/v2/detector/{id}/events` | Fetch events for a detector |
| GET | `/v2/detector/{id}/incidents` | Fetch incidents for a detector |
| GET | `/v2/incident` | List active incidents (query params: `limit`, `offset`) |
| GET | `/v2/incident/{id}` | Fetch a specific incident |

### Metric metadata

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v2/metric` | Search metrics (query param: `query=name:{pattern}`) |
| GET | `/v2/metric/{name}` | Fetch metadata for a specific metric |
| GET | `/v2/metrictimeseries` | Search metric time series by dimensions |
| GET | `/v2/dimension` | Search dimensions (query param: `query={key}:{value}`) |
| GET | `/v2/tag` | List tags |

### Other useful endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v2/organization` | Fetch org details |
| GET | `/v2/crosslink` | List data links (crosslinks between services) |

## SignalFlow streaming API

The SignalFlow API runs analytics programs and returns time series data.
It uses a **streaming** endpoint (not the REST endpoint) and returns
Server-Sent Events (SSE).

### Endpoint

```
POST https://stream.signalfx.com/v2/signalflow/execute
```

### Query parameters

| Param | Type | Description |
|-------|------|-------------|
| `start` | int (ms) | Start timestamp in Unix epoch milliseconds |
| `stop` | int (ms) | Stop timestamp -- makes it a bounded query |
| `resolution` | int (ms) | Minimum data resolution |
| `immediate` | bool | If `true`, don't wait for future data |

### Request body

```json
{"programText": "data('cpu.utilization').mean().publish(label='cpu')"}
```

Content-Type can be `application/json` (with `programText` key) or
`text/plain` (raw SignalFlow program text).

### SSE response format

The response is `text/event-stream` containing these event types:

| Event type | Payload fields | Description |
|------------|---------------|-------------|
| `control-message` | `event`, `timestampMs` | Stream lifecycle (STREAM_START, JOB_START, END_OF_CHANNEL) |
| `metadata` | `tsId`, `properties` | Dimension metadata for a time series ID |
| `data` | `logicalTimestampMs`, `data[]` | Array of `{tsId, value}` data points |
| `message` | `logicalTimestampMs`, `message` | Info messages about the computation |
| `error` | `errors[]` | Computation errors |

### SSE parsing

Each SSE message consists of:
1. An `event: <type>` line identifying the event type
2. One or more `data: <content>` lines forming a multi-line JSON object
3. A blank line separating messages

Concatenate all `data:` lines (stripping the prefix) and parse as JSON.

---

## URL patterns

### Browser URL (for navigating the IDE browser)

```
https://app.signalfx.com/#/dashboard/{dashboardId}?groupId=D6EXYIbAYAA&configId={configId}
```

Optional filter parameters:

```
&sources[]=app_group:Product_Feeds&sources[]=app:envoy&sources[]=env:prod
&startTime=-1h&endTime=Now&density=2
```

### User profile (for token retrieval)

```
https://app.signalfx.com/#/myprofile
```

---

## Token management

### Token types

| Type | Lifetime | How to get |
|------|----------|------------|
| User API Access Token | Expires on logout or after 30 days | Profile page > "Show User API Access Token" |
| Org access token | Long-lived (admin-configurable) | Settings > Access Tokens > New Token (requires `token_mgmt` capability) |
| Session token (`POST /v2/session`) | 30 days (no logout expiry) | Requires email + password -- NOT available for SSO-only orgs |

Nike uses SSO, so `POST /v2/session` is not available. The skill uses the
User API Access Token by default. An admin-created org token with `read_only`
scope is an optional upgrade for longer-lived access.

### Token retrieval flow

1. Navigate to `https://app.signalfx.com/#/myprofile` in the IDE browser
2. Click "Show User API Access Token"
3. Read the token value from the DOM snapshot (appears as a readonly textbox)
4. Save to `${SKILL_DIR}/signalfx_token.txt`

### Token expiry handling

If an API call returns HTTP 401:
- The token likely expired (user logged out of SignalFx, or 30-day limit)
- Re-grab the token using the browser flow above
- The user should already be SSO'd, so no re-auth is needed

---

## SignalFlow quick reference

SignalFlow is the query language used in chart definitions. Each chart's
`programText` field contains one or more SignalFlow statements.

### Common patterns

```python
# Basic metric query with filters
A = data('requests.count',
    filter=filter('app', 'kingpinv1') and (not filter('uri', '/health')),
    rollup='rate'
).sum(by=['method', 'uri', 'app_version']).publish(label='A')

# Scale to per-minute
C = (A).scale(60).publish(label='C')

# Time-shifted comparison (yesterday)
D = (A).timeshift('1d').publish(label='D', enable=False)

# Percentile calculation
B = data('request.duration',
    filter=filter('app', 'kingpinv1')
).percentile(pct=95).publish(label='B')

# Mean over a window
data('cpu.utilization', filter=filter('app', 'envoy')).mean(over='1m').publish()
```

### Key functions

| Function | Purpose |
|----------|---------|
| `data(metric, filter=..., rollup=...)` | Fetch a metric time series |
| `filter(dimension, value)` | Filter by dimension value |
| `.sum(by=[...])` | Aggregate by dimensions |
| `.mean()` / `.mean(over='5m')` | Average across time series or over a window |
| `.percentile(pct=N)` | Nth percentile |
| `.scale(N)` | Multiply values by N |
| `.timeshift(duration)` | Shift data back in time |
| `.publish(label=...)` | Output the stream (required for results) |
| `.count()` | Count of time series |
| `.max()` / `.min()` | Max/min across time series |
| `.top(N)` / `.bottom(N)` | Top/bottom N time series by value |
| `detect(when(...))` | Create a detector condition |

### Rollup types

| Rollup | Meaning |
|--------|---------|
| `rate` | Per-second rate of change |
| `sum` | Sum over the rollup period |
| `average` | Mean over the rollup period |
| `latest` | Most recent value |
| `max` / `min` | Max/min over the rollup period |

---

## Script usage

Resolve `SKILL_DIR` as the directory containing `SKILL.md`.

All commands require a valid API token (see Token management above).

### List all dashboards (tabs) in the OCSP group

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --list-dashboards
```

Returns JSON array of `{name, dashboardId, configId, url}` objects.

### Fetch a dashboard with all chart definitions

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --dashboard GKQEytpAYAA
```

Returns the dashboard name, chart count, and an array of chart objects
including `name`, `programText` (SignalFlow), and layout coordinates.

### Fetch a single chart

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --chart GKQE1LTAgAA
```

Returns the chart name, description, SignalFlow program, and display options.

### Execute a SignalFlow program (live metric data)

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" \
  --execute "data('cpu.utilization', filter=filter('app', 'envoy')).mean().publish(label='cpu')" \
  --duration 5m
```

Options:
- `--duration` (default `5m`): lookback window -- e.g. `30s`, `5m`, `1h`, `1d`
- `--resolution`: minimum data resolution -- e.g. `10s`, `1m`

Returns `{program, duration, startMs, stopMs, metadataCount, dataPointCount,
metadata, data}`.  Each data point contains `logicalTimestampMs` and an
array of `{tsId, value}` pairs.

### Dynamic queries: extract and run a chart's program

To get live data for a dashboard chart, combine `--chart` and `--execute`:

```bash
# 1. Get the chart's SignalFlow program
PROGRAM=$(python3 "${SKILL_DIR}/scripts/signalfx_query.py" --chart GKQE1LTAgAA \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['programText'])")

# 2. Execute it to get live data
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --execute "$PROGRAM" --duration 10m
```

### List detectors

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --detectors --limit 20
```

Returns detector name, ID, description, and a truncated SignalFlow program.

### List active incidents (alerts)

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --incidents --limit 20
```

Returns incident ID, severity, detector name, and active/muted status.

### Look up metric metadata

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --metric cpu.utilization
```

Returns the metric type (GAUGE, COUNTER, CUMULATIVE_COUNTER) and properties.

### Search metrics by name pattern

```bash
python3 "${SKILL_DIR}/scripts/signalfx_query.py" --search-metric "requests.*" --limit 10
```

Returns matching metric names, types, and custom properties.
