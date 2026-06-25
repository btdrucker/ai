#!/usr/bin/env python3
"""SignalFx / Splunk Observability Cloud query script.

Commands:
  --list-dashboards              List all dashboards in the OCSP group
  --dashboard ID                 Fetch dashboard definition (charts + SignalFlow)
  --chart ID                     Fetch a single chart definition
  --execute PROGRAM              Execute a SignalFlow program and return data
  --detectors                    List active detectors
  --incidents                    List active incidents (alerts)
  --metric NAME                  Look up metric metadata
  --search-metric QUERY          Search metrics by name pattern

Auth: set SIGNALFX_TOKEN env var, or place the raw token in
      .cursor/skills/ops-splunk-observability-dashboard/signalfx_token.txt
      falling back to
      ~/.cursor/skills/ops-splunk-observability-dashboard/signalfx_token.txt
"""

import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.signalfx.com"
STREAM_BASE = "https://stream.signalfx.com"
OCSP_GROUP_ID = "D6EXYIbAYAA"

PROJECT_TOKEN_FILE = Path(__file__).parent.parent / "signalfx_token.txt"
HOME_TOKEN_FILE = (
    Path.home()
    / ".cursor/skills/ops-splunk-observability-dashboard/signalfx_token.txt"
)


def get_token() -> str:
    token = os.environ.get("SIGNALFX_TOKEN")
    if not token and PROJECT_TOKEN_FILE.exists():
        token = PROJECT_TOKEN_FILE.read_text().strip()
    if not token and HOME_TOKEN_FILE.exists():
        token = HOME_TOKEN_FILE.read_text().strip()
    if not token:
        print(
            "ERROR: SIGNALFX_TOKEN not set and no token file found.\n"
            f"  Set the env var, or place the raw token in:\n"
            f"    {PROJECT_TOKEN_FILE}\n"
            f"  Fallback path:\n"
            f"    {HOME_TOKEN_FILE}",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"X-SF-TOKEN": token})
    with urllib.request.urlopen(req, context=_ssl_context(), timeout=30) as resp:
        return json.loads(resp.read())


def _api_get(path: str, token: str, params: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    return _get(url, token)


def _post(url: str, token: str, body: dict | str,
          content_type: str = "application/json") -> bytes:
    if isinstance(body, dict):
        data = json.dumps(body).encode()
    else:
        data = body.encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"X-SF-TOKEN": token, "Content-Type": content_type},
    )
    with urllib.request.urlopen(req, context=_ssl_context(), timeout=60) as resp:
        return resp.read()


# -- Dashboard commands --------------------------------------------------------

def list_dashboards(token: str) -> list[dict]:
    """Fetch all dashboards in the OCSP group with their names."""
    group = _api_get(f"/v2/dashboardgroup/{OCSP_GROUP_ID}", token)
    configs = group.get("dashboardConfigs", [])

    results = []
    for cfg in configs:
        dashboard_id = cfg["dashboardId"]
        config_id = cfg["configId"]
        try:
            dash = _api_get(f"/v2/dashboard/{dashboard_id}", token)
            name = dash.get("name", "UNKNOWN")
        except Exception as e:
            name = f"ERROR: {e}"

        url = (
            f"https://app.signalfx.com/#/dashboard/{dashboard_id}"
            f"?groupId={OCSP_GROUP_ID}&configId={config_id}"
        )
        results.append({
            "name": name,
            "dashboardId": dashboard_id,
            "configId": config_id,
            "url": url,
        })
    return results


def get_dashboard(dashboard_id: str, token: str) -> dict:
    """Fetch a dashboard definition including chart layout."""
    dash = _api_get(f"/v2/dashboard/{dashboard_id}", token)
    charts = dash.get("charts", [])
    chart_details = []
    for chart_ref in charts:
        chart_id = chart_ref["chartId"]
        try:
            chart = _api_get(f"/v2/chart/{chart_id}", token)
            chart_details.append({
                "chartId": chart_id,
                "name": chart.get("name", "UNKNOWN"),
                "description": chart.get("description", ""),
                "programText": chart.get("programText", ""),
                "row": chart_ref.get("row"),
                "column": chart_ref.get("column"),
                "width": chart_ref.get("width"),
                "height": chart_ref.get("height"),
            })
        except Exception as e:
            chart_details.append({"chartId": chart_id, "error": str(e)})

    return {
        "dashboardId": dashboard_id,
        "name": dash.get("name", "UNKNOWN"),
        "description": dash.get("description", ""),
        "chartCount": len(charts),
        "charts": chart_details,
    }


def get_chart(chart_id: str, token: str) -> dict:
    """Fetch a single chart definition."""
    chart = _api_get(f"/v2/chart/{chart_id}", token)
    return {
        "chartId": chart_id,
        "name": chart.get("name", "UNKNOWN"),
        "description": chart.get("description", ""),
        "programText": chart.get("programText", ""),
        "options": chart.get("options", {}),
    }


# -- SignalFlow execution -----------------------------------------------------

def _parse_duration(duration: str) -> int:
    """Convert a duration string like '5m', '1h', '30s' to milliseconds."""
    match = re.match(r"^(\d+)([smhd])$", duration)
    if not match:
        raise ValueError(f"Invalid duration: {duration}. Use e.g. 5m, 1h, 30s")
    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1000, "m": 60_000, "h": 3_600_000, "d": 86_400_000}
    return value * multipliers[unit]


def _parse_sse_events(text: str) -> list[tuple[str, dict]]:
    """Parse a text/event-stream response into (event_type, payload) tuples.

    SSE format (RFC 8895):
      event: <type>
      data: <json line 1>
      data: <json line 2>
      <blank line>
    """
    events = []
    current_event = "message"
    data_lines: list[str] = []

    for line in text.split("\n"):
        if line.startswith("event: "):
            current_event = line[7:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip(" "))
        elif line.strip() == "" and data_lines:
            try:
                payload = json.loads("\n".join(data_lines))
                events.append((current_event, payload))
            except json.JSONDecodeError:
                pass
            data_lines = []
            current_event = "message"

    if data_lines:
        try:
            payload = json.loads("\n".join(data_lines))
            events.append((current_event, payload))
        except json.JSONDecodeError:
            pass

    return events


def execute_signalflow(program: str, token: str, duration: str = "5m",
                       resolution: str | None = None) -> dict:
    """Execute a SignalFlow program and return metric data.

    Uses the SignalFlow streaming API with start/stop to get a bounded
    result set.  The response is a Server-Sent Events stream whose
    event types are documented in the signalfx-python messages module.
    """
    now_ms = int(time.time() * 1000)
    duration_ms = _parse_duration(duration)
    start_ms = now_ms - duration_ms

    params = {"start": start_ms, "stop": now_ms, "immediate": "true"}
    if resolution:
        params["resolution"] = _parse_duration(resolution)

    url = f"{STREAM_BASE}/v2/signalflow/execute?{urllib.parse.urlencode(params)}"
    raw = _post(url, token, {"programText": program})
    text = raw.decode("utf-8", errors="replace")

    sse_events = _parse_sse_events(text)

    metadata: dict[str, dict] = {}
    data_points: list[dict] = []
    errors_list: list[dict] = []

    for event_type, payload in sse_events:
        if event_type == "metadata":
            ts_id = payload.get("tsId", "")
            metadata[ts_id] = payload.get("properties", {})
        elif event_type == "data":
            data_points.append({
                "logicalTimestampMs": payload.get("logicalTimestampMs"),
                "data": payload.get("data", []),
            })
        elif event_type == "error":
            errors_list.append(payload)

    result: dict = {
        "program": program,
        "duration": duration,
        "startMs": start_ms,
        "stopMs": now_ms,
        "metadataCount": len(metadata),
        "dataPointCount": len(data_points),
        "metadata": metadata,
        "data": data_points[-20:] if len(data_points) > 20 else data_points,
    }
    if errors_list:
        result["errors"] = errors_list
    return result


# -- Detectors and incidents ---------------------------------------------------

def list_detectors(token: str, limit: int = 20) -> list[dict]:
    """List detectors, optionally filtered."""
    resp = _api_get("/v2/detector", token, {"limit": limit})
    results = resp.get("results", [])
    return [{
        "id": d.get("id"),
        "name": d.get("name"),
        "description": d.get("description", ""),
        "programText": d.get("programText", "")[:200],
        "lastUpdated": d.get("lastUpdated"),
    } for d in results]


def list_incidents(token: str, limit: int = 20) -> list[dict]:
    """List active incidents."""
    resp = _api_get("/v2/incident", token, {"limit": limit})
    results = resp if isinstance(resp, list) else resp.get("results", resp)
    if not isinstance(results, list):
        return [results]
    return [{
        "id": inc.get("incidentId", inc.get("id")),
        "active": inc.get("active"),
        "severity": inc.get("severity"),
        "detectLabel": inc.get("detectLabel"),
        "detectorName": inc.get("detectorName"),
        "triggeredWhileMuted": inc.get("triggeredWhileMuted"),
    } for inc in results[:limit]]


# -- Metric metadata -----------------------------------------------------------

def get_metric(name: str, token: str) -> dict:
    """Look up metadata for a specific metric."""
    return _api_get(f"/v2/metric/{urllib.parse.quote(name, safe='')}", token)


def search_metrics(query: str, token: str, limit: int = 20) -> list[dict]:
    """Search metrics by name pattern."""
    resp = _api_get("/v2/metric", token, {"query": f"name:{query}", "limit": limit})
    results = resp.get("results", [])
    return [{
        "name": m.get("name"),
        "type": m.get("type"),
        "description": m.get("description", ""),
        "customProperties": m.get("customProperties", {}),
    } for m in results]


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Query Splunk Observability Cloud (SignalFx)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list-dashboards", action="store_true",
                       help="List all dashboards in the OCSP group")
    group.add_argument("--dashboard", metavar="ID",
                       help="Fetch dashboard definition by ID")
    group.add_argument("--chart", metavar="ID",
                       help="Fetch chart definition by ID")
    group.add_argument("--execute", metavar="PROGRAM",
                       help="Execute a SignalFlow program")
    group.add_argument("--detectors", action="store_true",
                       help="List detectors")
    group.add_argument("--incidents", action="store_true",
                       help="List active incidents")
    group.add_argument("--metric", metavar="NAME",
                       help="Look up metric metadata by name")
    group.add_argument("--search-metric", metavar="QUERY",
                       help="Search metrics by name pattern")

    parser.add_argument("--duration", default="5m",
                        help="Time range for --execute (e.g. 5m, 1h, 30s)")
    parser.add_argument("--resolution", default=None,
                        help="Resolution for --execute (e.g. 10s, 1m)")
    parser.add_argument("--limit", default=20, type=int,
                        help="Max results for list commands")

    args = parser.parse_args()
    token = get_token()

    if args.list_dashboards:
        result = list_dashboards(token)
    elif args.dashboard:
        result = get_dashboard(args.dashboard, token)
    elif args.chart:
        result = get_chart(args.chart, token)
    elif args.execute:
        result = execute_signalflow(args.execute, token, args.duration,
                                    args.resolution)
    elif args.detectors:
        result = list_detectors(token, args.limit)
    elif args.incidents:
        result = list_incidents(token, args.limit)
    elif args.metric:
        result = get_metric(args.metric, token)
    elif args.search_metric:
        result = search_metrics(args.search_metric, token, args.limit)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
