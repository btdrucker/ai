# Service Name Reference

All names accepted by `--service`. These map to `app=<name>` in the log4j pattern.

## Wholesale Events Composer

| `--service` name                       | Description                              |
| -------------------------------------- | ---------------------------------------- |
| `wholesaleeventscomposerv1`            | Wholesale events SQS consumer (incremental) |
| `wholesaleeventscomposerfullloadv1`    | Wholesale events full-load processor     |

## Search / Ingest

| `--service` name       | Description                         |
| ---------------------- | ----------------------------------- |
| `searchservicev3`      | Search service v3                   |
| `searchservicev2`      | Search service v2                   |
| `searchingestv2`       | Search ingest v2 (log4j: `app=searchIngestV2`) |
| `searchreplicatorv3`   | Search replicator v3                |
| `searchschemasv4`      | Search schemas v4                   |
| `searchschemasv3`      | Search schemas v3                   |
| `searchindexesv3`      | Search indexes v3                   |
| `searchclustersv2`     | Search clusters v2                  |

## Product Feed

| `--service` name          | Description                      |
| ------------------------- | -------------------------------- |
| `productfeedv2`           | Product feed v2                  |
| `productfeedprocessorv2`  | Product feed processor v2        |
| `productfeedcardv2`       | Product feed card v2             |
| `productfeedrollupsv2`    | Product feed rollups v2          |
| `productfeedstreamv2`     | Product feed stream v2           |
| `pfinventory`             | PF inventory                     |
| `pfmonitor`               | PF monitor                       |
| `pfeventhandler`          | PF event handler                 |

## Concept

| `--service` name   | Description           |
| ------------------- | --------------------- |
| `conceptzerov3`     | Concept zero v3       |
| `conceptingestv3`   | Concept ingest v3     |
| `conceptsetlv3`     | Concept SETL v3       |

## Recommend / Nav

| `--service` name       | Description                |
| ---------------------- | -------------------------- |
| `recommendnavv1`       | Recommend nav v1           |
| `recommendrulesv2`     | Recommend rules v2         |
| `recommendconceptsv1`  | Recommend concepts v1      |
| `compositerulesv2`     | Composite rules v2         |
| `navattributesv2`      | Nav attributes v2          |

## Kingpin / Smart Search / Strategies / Typeahead

| `--service` name    | Description            |
| ------------------- | ---------------------- |
| `kingpinv1`         | Kingpin v1 (log4j: `app=kingpin`)  |
| `smartsearchv1`     | Smart search v1        |
| `searchstrategies`  | Search strategies      |
| `searchtypeahead`   | Search typeahead       |

## Other Services

| `--service` name         | Description                |
| ------------------------ | -------------------------- |
| `collectionsv2`          | Collections v2             |
| `collectionsmanagerv2`   | Collections manager v2     |
| `kirbyv2`                | Kirby v2                   |
| `envoy`                  | Envoy                      |
| `maestro`                | Maestro                    |
| `visualsearchservice`    | Visual search service      |
| `raptorv1`               | Raptor v1                  |

## ECS Services

| `--service` name          | Notes                                       |
| ------------------------- | ------------------------------------------- |
| `autocompleteingestv1`    | Uses `sourcetype=log4j:autocompleteingestv1` instead of `app=` filter |

## Adding a new service

1. Add an entry to the `SERVICES` dict in `splunk_query.py`
2. Most Waffle EC2 services follow the pattern: `index={index} app=<appName>`
3. The `appName` matches the value in the service's `log4j2.xml` pattern: `app=<appName>`
4. Update this file with the new service name

---

# Common Query Patterns

Resolve `SKILL_DIR` as the directory containing `SKILL.md`.

### All activity for a service (test)

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --service wholesaleeventscomposerv1 --env test --time-range -24h
```

### Errors only

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --service wholesaleeventscomposerv1 --env test --filter "ERROR" --time-range -4h
```

### Startup logs (look for Spring Boot banner or ApplicationStarted)

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --service wholesaleeventscomposerv1 --env test \
  --filter '"Started Application" OR "ApplicationStartedEvent"' \
  --time-range -7d
```

### Check traffic volume (use stats in free-form SPL)

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --spl 'index=np-app app=wholesaleeventscomposerv1 | stats count by _time span=1h' \
  --time-range -7d --max-results 500
```

### Trace a request by traceId

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --spl 'index=np-app app=wholesaleeventscomposerv1 traceId=<your-trace-id>' \
  --time-range -24h
```

### Absolute time window

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --service wholesaleeventscomposerv1 --env prod \
  --time-range "2026-05-20T00:00:00" --latest-time "2026-05-20T23:59:59"
```

### High-volume services

Some services (e.g. maestro, kingpin, kirbyv2, searchingestv2) generate very high log volume. Template-mode queries against these services may time out or fail with a 400 error on the results fetch.

Note: `--max-results` does not short-circuit the Splunk scan -- it only limits the output after the search completes. Use `| head N` in free-form SPL to stop scanning early.

Workarounds:

- Use a shorter `--time-range` (e.g. `-5m` instead of `-1h`)
- Use free-form SPL with `| head N` to stop scanning early:

```bash
python3 "${SKILL_DIR}/scripts/splunk_query.py" \
  --spl 'index=np-app app=maestro | head 10' \
  --time-range -1h
```

- Add a specific `--filter` to narrow results before Splunk scans the full time range

---

# Presenting Results

- Parse the JSON array of `results` objects
- Each result has a `_raw` field with the full log line and structured fields
- The log4j pattern includes: `traceId=`, `spanId=`, log level, timestamp, thread, class, `app=<name>`, `version=`
- For timeline views, sort by `_time`; for error summaries, group by log level or message

---

# Splunk Web UI

The Search team Splunk app is at: `https://nike.splunkcloud.com/en-US/app/nike_search/`

Direct search URL pattern:

```
https://nike.splunkcloud.com/en-US/app/nike_search/search?q=search index%3Dnp-app app%3Dwholesaleeventscomposerv1&earliest=-1h&latest=now
```
