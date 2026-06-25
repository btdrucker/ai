#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-}"
TICKET_KEY="${2:-}"
UPDATES_FILE="${3:-}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JIRA_BASE="${JIRA_BASE_URL:-https://jira.nike.com}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <test|prod> <TICKET-KEY> [updates.jsonl]

Verify typeahead API responses contain the ticket's popular search terms.

The updates file can be either:
  - A parsed ticket JSONL (from parse-jira-jsonl.py)
  - The repo's popular_search_terms.jsonl (will verify all marketplaces in it)

Arguments:
  test|prod       Environment to verify
  TICKET-KEY      Jira ticket key (e.g. SRPLT-985), used for display only
  updates.jsonl   JSONL file with expected terms (strongly recommended).
                  When omitted, fetches Jira description (requires JIRA_API_TOKEN).

Environment (when fetching Jira):
  JIRA_API_TOKEN  Bearer token for jira.nike.com
  JIRA_BASE_URL   Optional override (default: https://jira.nike.com)
EOF
}

if [[ "${ENV}" != "test" && "${ENV}" != "prod" ]]; then
  usage >&2
  exit 1
fi

if [[ -z "${TICKET_KEY}" ]]; then
  usage >&2
  exit 1
fi

if [[ "${ENV}" == "test" ]]; then
  SNKRS_BASE="https://snkrs.test.commerce.nikecloud.com"
else
  SNKRS_BASE="https://snkrs.prod.commerce.nikecloud.com"
fi

TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

if [[ -n "${UPDATES_FILE}" ]]; then
  PARSED="${UPDATES_FILE}"
else
  if [[ -z "${JIRA_API_TOKEN:-}" ]]; then
    echo "error: JIRA_API_TOKEN required to fetch ${TICKET_KEY}, or pass a JSONL file as third argument" >&2
    echo "hint: pass the repo's popular_search_terms.jsonl or a parsed ticket JSONL" >&2
    exit 1
  fi
  DESC_FILE="${TMPDIR}/jira-description.txt"
  curl -sf \
    -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
    -H "Accept: application/json" \
    "${JIRA_BASE}/rest/api/2/issue/${TICKET_KEY}?fields=description" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['fields']['description'])" \
    > "${DESC_FILE}"
  PARSED="${TMPDIR}/parsed.jsonl"
  python3 "${SCRIPT_DIR}/parse-jira-jsonl.py" -i "${DESC_FILE}" -o "${PARSED}" >/dev/null
fi

python3 - <<'PY' "${PARSED}" "${ENV}" "${SNKRS_BASE}" "${TICKET_KEY}"
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

parsed_path, env, snkrs_base, ticket_key = sys.argv[1:5]

checks = []
with open(parsed_path, encoding="utf-8") as handle:
    for raw_line in handle:
        line = raw_line.strip()
        if not line:
            continue
        obj = json.loads(line)
        marketplace = obj["marketplace"]
        for lang_entry in obj["languages"]:
            language = lang_entry["language"]
            terms = lang_entry["searchTerms"]
            checks.append((marketplace, language, terms))

failures = []
passes = []

for marketplace, language, terms in checks:
    params = urllib.parse.urlencode({
        "country": marketplace,
        "language": language,
        "count": "10",
    })
    url = f"{snkrs_base}/search/suggestions/v1?{params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        failures.append((marketplace, language, terms, url, f"HTTP {exc.code}"))
        continue
    except urllib.error.URLError as exc:
        failures.append((marketplace, language, terms, url, str(exc.reason)))
        continue

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        failures.append((marketplace, language, terms, url, "invalid JSON response"))
        continue

    api_terms = {
        entry.get("displayText", "").lower()
        for entry in data.get("searchTerms", [])
    }

    missing = [t for t in terms if t.lower() not in api_terms]
    if missing:
        failures.append(
            (marketplace, language, terms, url,
             f"missing: {', '.join(missing)}")
        )
    else:
        passes.append((marketplace, language, terms, url))

print(f"Typeahead verification ({env}) for {ticket_key}")
print(f"{'Marketplace':<12} {'Language':<10} {'Status':<6} {'Terms':<40} URL")
print("-" * 120)
for marketplace, language, terms, url in passes:
    print(f"{marketplace:<12} {language:<10} PASS   {', '.join(terms):<40} {url}")
for marketplace, language, terms, url, detail in failures:
    print(f"{marketplace:<12} {language:<10} FAIL   {detail:<40} {url}")

print("-" * 120)
print(f"Passed: {len(passes)}  Failed: {len(failures)}")

if failures:
    sys.exit(1)
PY
