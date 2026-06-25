#!/usr/bin/env python3
"""Splunk query script for Nike Search Engineering services.

Usage:
  Free-form SPL:
    python3 splunk_query.py --spl "index=np-app app=wholesaleeventscomposerv1 error" [--time-range -1h] [--max-results 100]

  Named service template:
    python3 splunk_query.py --service wholesaleeventscomposerv1 --env test [--filter "error"] [--time-range -4h]

Auth: set SPLUNK_JWT_TOKEN env var, or place raw token in
      .cursor/skills/query-splunk/splunk_token.txt
      falling back to ~/.cursor/skills/query-splunk/splunk_token.txt
"""

import argparse
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SPLUNK_BASE_URL = "https://nike.splunkcloud.com:8089"
PROJECT_TOKEN_FILE = Path(__file__).parent.parent / "splunk_token.txt"
HOME_TOKEN_FILE = Path.home() / ".cursor/skills/query-splunk/splunk_token.txt"

# -- Index resolution ----------------------------------------------------------

def resolve_indexes(env: str) -> dict:
    is_prod = env in ("prod", "waffle-prod")
    return {
        "index": "app" if is_prod else "np-app",
    }


# -- Service SPL templates -----------------------------------------------------
# {index} -> np-app (test) or app (prod)
# {env}   -> environment string (test / prod)
#
# Waffle EC2 services log to /var/log/nike/<appName>/<appName>.log.
# The platform-level Splunk forwarder ships them; the app= field in the
# log4j pattern is the primary filter.

_WAFFLE_EC2_BASE = 'index={index} app={app_name}'

SERVICES: dict[str, str] = {
    # Wholesale Events Composer -------------------------------------------------
    "wholesaleeventscomposerv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="wholesaleeventscomposerv1",
    ),
    "wholesaleeventscomposerfullloadv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="wholesaleeventscomposerfullloadv1",
    ),

    # Search / Ingest services --------------------------------------------------
    "searchservicev3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchservicev3",
    ),
    "searchservicev2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchservicev2",
    ),
    "searchingestv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchIngestV2",
    ),
    "searchreplicatorv3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchreplicatorv3",
    ),
    "searchschemasv4": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchschemasv4",
    ),
    "searchschemasv3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchschemasv3",
    ),
    "searchindexesv3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchindexesv3",
    ),
    "searchclustersv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchclustersv2",
    ),

    # Product Feed services -----------------------------------------------------
    "productfeedv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="productfeedv2",
    ),
    "productfeedprocessorv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="productfeedprocessorv2",
    ),
    "productfeedcardv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="productfeedcardv2",
    ),
    "productfeedrollupsv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="productfeedrollupsv2",
    ),
    "productfeedstreamv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="productfeedstreamv2",
    ),
    "pfinventory": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="pfinventory",
    ),
    "pfmonitor": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="pfmonitor",
    ),
    "pfeventhandler": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="pfeventhandler",
    ),

    # Concept services ----------------------------------------------------------
    "conceptzerov3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="conceptzerov3",
    ),
    "conceptingestv3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="conceptingestv3",
    ),
    "conceptsetlv3": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="conceptsetlv3",
    ),

    # Recommend / Nav services --------------------------------------------------
    "recommendnavv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="recommendnavv1",
    ),
    "recommendrulesv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="recommendrulesv2",
    ),
    "recommendconceptsv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="recommendconceptsv1",
    ),
    "compositerulesv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="compositerulesv2",
    ),
    "navattributesv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="navattributesv2",
    ),

    # Kingpin / Smart Search / Strategies / Typeahead ---------------------------
    "kingpinv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="kingpin",
    ),
    "smartsearchv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="smartsearchv1",
    ),
    "searchstrategies": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchstrategies",
    ),
    "searchtypeahead": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="searchtypeahead",
    ),

    # Other services ------------------------------------------------------------
    "collectionsv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="collectionsv2",
    ),
    "collectionsmanagerv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="collectionsmanagerv2",
    ),
    "kirbyv2": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="kirbyv2",
    ),
    "envoy": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="envoy",
    ),
    "maestro": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="maestro",
    ),
    "visualsearchservice": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="visualsearchservice",
    ),
    "raptorv1": _WAFFLE_EC2_BASE.format(
        index="{index}", app_name="raptorv1",
    ),

    # ECS services (same index, different log format) ---------------------------
    "autocompleteingestv1": (
        'index={index} sourcetype="log4j:autocompleteingestv1"'
    ),
}


def build_spl(service: str, env: str, extra_filter: str | None) -> str:
    template = SERVICES.get(service)
    if template is None:
        known = ", ".join(sorted(SERVICES))
        print(f"ERROR: unknown service '{service}'. Known: {known}", file=sys.stderr)
        sys.exit(1)
    indexes = resolve_indexes(env)
    spl = template.format(**indexes)
    if extra_filter:
        spl = f"{spl} {extra_filter}"
    return f"search {spl}"


# -- Splunk API ----------------------------------------------------------------

def get_token() -> str:
    token = os.environ.get("SPLUNK_JWT_TOKEN")
    if not token and PROJECT_TOKEN_FILE.exists():
        token = PROJECT_TOKEN_FILE.read_text().strip()
    if not token and HOME_TOKEN_FILE.exists():
        token = HOME_TOKEN_FILE.read_text().strip()
    if not token:
        print(
            "ERROR: SPLUNK_JWT_TOKEN not set and no token file found.\n"
            f"  Set the env var, or place the raw token in: {PROJECT_TOKEN_FILE}\n"
            f"  Fallback token path: {HOME_TOKEN_FILE}",
            file=sys.stderr,
        )
        sys.exit(1)
    return token


def _ssl_context() -> ssl.SSLContext:
    # nike.splunkcloud.com uses a certificate signed by an internal CA that
    # is not in the default trust store on most developer machines.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


MAX_RETRIES = 3
RETRY_DELAY = 2


def _request_with_retry(req: urllib.request.Request, retries: int = MAX_RETRIES) -> dict:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, context=_ssl_context(), timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (502, 503, 504) and attempt < retries - 1:
                print(f"[{e.code}; retry {attempt + 1}/{retries}]", end="", file=sys.stderr, flush=True)
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            raise


def _post(path: str, token: str, body: dict) -> dict:
    url = f"{SPLUNK_BASE_URL}{path}"
    data = urllib.parse.urlencode(body).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Authorization": f"Bearer {token}"},
    )
    return _request_with_retry(req)


def _get(path: str, token: str, params: dict | None = None) -> dict:
    url = f"{SPLUNK_BASE_URL}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {token}"}
    )
    return _request_with_retry(req)


def run_search(spl: str, token: str, time_range: str, max_results: int, latest_time: str = "now") -> list[dict]:
    job = _post(
        "/services/search/jobs",
        token,
        {
            "output_mode": "json",
            "search": spl,
            "earliest_time": time_range,
            "latest_time": latest_time,
            "count": str(max_results),
        },
    )
    sid = job["sid"]
    print(f"Job sid={sid} ", end="", file=sys.stderr, flush=True)

    poll_start = time.monotonic()
    max_poll_secs = 300
    while True:
        if time.monotonic() - poll_start > max_poll_secs:
            print(
                f"\nERROR: job {sid} not done after {max_poll_secs}s. "
                "Try a shorter --time-range or use free-form SPL with '| head N'.",
                file=sys.stderr,
            )
            sys.exit(1)
        status_raw = _get(f"/services/search/jobs/{sid}", token, {"output_mode": "json"})
        entry = status_raw.get("entry", [{}])[0]
        content = entry.get("content", {})
        if content.get("isDone"):
            print(" done", file=sys.stderr)
            break
        print(".", end="", file=sys.stderr, flush=True)
        time.sleep(2)

    try:
        results = _get(
            f"/services/search/jobs/{sid}/results/",
            token,
            {"output_mode": "json", "count": str(max_results)},
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace") if e.fp else ""
        if e.code == 400:
            if body:
                print(f"Splunk error detail: {body[:500]}", file=sys.stderr)
            print(
                f"\nERROR: Splunk returned 400 when fetching results for job {sid}.\n"
                "This typically happens with high-volume services (e.g. maestro, kingpin)\n"
                "where the search scans too much data.\n"
                "Workaround: use free-form SPL with '| head N' to limit the scan, e.g.:\n"
                f"  --spl 'index=<idx> app=<name> | head {max_results}'\n"
                "Or use a shorter --time-range (e.g. -5m).",
                file=sys.stderr,
            )
            sys.exit(1)
        raise
    return results.get("results", [])


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Query Nike Splunk for Search Engineering services")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--spl",     help="Full SPL query string")
    group.add_argument("--service", help="Named service (see service-reference.md)")
    parser.add_argument("--env",         default="test",  help="Environment: test or prod (default: test)")
    parser.add_argument("--filter",      default=None,    help="Extra SPL filter appended to template query")
    parser.add_argument("--time-range",  default="-1h",   help="Splunk time range, e.g. -4h, -1d (default: -1h)")
    parser.add_argument("--latest-time", default="now",   help="Splunk latest time (default: now)")
    parser.add_argument("--max-results", default=100, type=int, help="Max results (default: 100)")
    args = parser.parse_args()

    token = get_token()

    if args.spl:
        spl = args.spl if args.spl.strip().startswith("search") else f"search {args.spl}"
    else:
        spl = build_spl(args.service, args.env, args.filter)

    print(f"SPL: {spl}", file=sys.stderr)

    results = run_search(spl, token, args.time_range, args.max_results, args.latest_time)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
