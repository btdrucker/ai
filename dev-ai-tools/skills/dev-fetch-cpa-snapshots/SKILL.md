---
name: dev-fetch-cpa-snapshots
description: >
  Fetches CPA (Consumer Product API) debug snapshots for a product code
  across style-color variants or marketplace/language combinations and saves
  individual JSON files under /tmp/cpa-snapshots/{timestamp}/. Supports bare
  style codes (auto-discovers all colorways per market), explicit style-color
  codes, geo group expansion (e.g. "APLA", "EMEA"), nested or flat output
  layout. Use when asked to "fetch CPA snapshots", "get CPA data for a product",
  "download CPA product snapshots", or "CPA debug for {product code}".
---

# Fetch CPA Snapshots

## Related skills

- **`search-kb`** -- CPA / OCPP team context

Fetches Consumer Product API (CPA) payloads from the Discover Platform debug
endpoint and saves one JSON file per style-color / marketplace / language
combination.

**Script:** `scripts/fetch_cpa.py` (in this skill folder)

Resolve `SKILL_DIR` as the directory containing this `SKILL.md` file.

---

## Debug endpoint

```
# Style-color code -> single CPA JSON object
{DEBUG_BASE}/marketplace/{marketplace}/language/{language}/consumerChannelId/{channelId}/productCode/{styleColorCode}/audienceId/cpa

# Bare style code -> JSON array (one element per colorway in that market/language)
{DEBUG_BASE}/marketplace/{marketplace}/language/{language}/consumerChannelId/{channelId}/productCode/{styleCode}/audienceId/cpa
```

`DEBUG_BASE` = `https://debug.discover-platform-prod.nikecloud.com/discover/debug/v1`

Examples:

- `FZ7013-500` -> one record
- `FZ7013` -> all colorways for US/en (array response)

Different markets may return different colorway sets.

The debug API wraps payloads as `{"objects": [...]}`. The fetch script unwraps
this automatically before saving one file per product record.

---

## Supported consumer channels

Default: **NIKE.COM** (`d9a5bc42-4b9c-4976-858a-f159cf99c647`)

| Channel | ID |
|---------|-----|
| Nike.com | `d9a5bc42-4b9c-4976-858a-f159cf99c647` |
| Nike App | `82a74ac1-c527-4470-b7b0-fb5f3ef3c2e2` |
| SNKRS Web | `010794e5-35fe-4e32-aaff-cd2c74f89d61` |
| SNKRS App | `008be467-6c78-4079-94f0-70e2d6cc4003` |
| WeChat | `15d92135-394e-487a-8afa-f6c8525c9ea9` |

Channel lookup (all channels):  
`https://snkrs.prod.commerce.nikecloud.com/globalization/consumer_channels/v3/?fields=id,name,marketplaces`

Channel detail (marketplaces, languages, geo groups):  
`https://snkrs.prod.commerce.nikecloud.com/globalization/consumer_channels/v3/{channelId}`

Channel slug for paths: lowercase, non-alphanumeric -> `-`, collapse runs  
(`NIKE.COM` -> `nike-com`, `NIKE APP` -> `nike-app`).

---

## Input forms

| Input | Example | Meaning |
|-------|---------|---------|
| Style-color | `FZ7013-500` | Single colorway |
| Style code | `FZ7013` | All colorways per target market/language |
| List | `FZ7013-500, FZ7013-100` | Explicit colorways |

---

## Iteration modes

| Mode | Product input | Scope |
|------|---------------|-------|
| `by-marketplace` | style-color (`FZ7013-500`) | geo / marketplace(s) / all |
| `by-style-colors` | style code (`FZ7013`) | single market + language (default US/en) |
| `combined` | style code (`FZ7013`) | geo group -- each market gets its colorway array |

**Inference (no AskQuestion):**

- Style-color + geo/market -> `by-marketplace`
- Style code, no market -> `by-style-colors` (US/en)
- Style code + geo/market -> `combined`
- Comma-separated style-colors -> `by-marketplace` over the list

**Combined strategy:** one style-code call per (marketplace, language); save each array element.

---

## Scope / marketplace resolution

From channel detail JSON, filter `marketplaces[]`:

- **Geo** ("APLA", "EMEA", "NA", "GC"): `marketplaceGroups` contains `nikeGeo-{GEO}` (case-insensitive match on geo token)
- **Marketplace id** ("US", "GB"): match `id` (case-insensitive)
- **"all"**: every marketplace on the channel
- **Default:** US only, language `en`

Per marketplace: use `defaultLanguage` unless user requests **all languages** -- then use every `languages[].id`.

**Cap:** 100 saved files per run. If the resolved plan exceeds 100, use **AskQuestion** to narrow scope before fetching.

---

## AskQuestion gates

Ask only when genuinely ambiguous:

1. Channel unspecified and marketplace exists on multiple supported channels -- confirm channel (else default Nike.com).
2. Resolved file count would exceed 50 -- show count; suggest geo group or fewer products.
3. "All marketplaces" with no product constraint -- NIKE.COM has 60+ markets; confirm or suggest a geo.

Do **not** ask when a bare style code + single market clearly means `by-style-colors`.

---

## Output layout

Timestamp folder is always created once per run: `YYYY-MM-DD_HHmm`.

### Nested (default)

```
/tmp/cpa-snapshots/{timestamp}/{channel-slug}/{marketplace}/{language}/{url-slug}--{productCode}.json
```

### Flat (`--flat`)

```
/tmp/cpa-snapshots/{timestamp}/{varying-dims}.json
```

Only dimensions that vary within the run appear in the filename (in order):

`{channel}--{marketplace}--{language}--{url-slug}--{productCode}`

Omit constant dimensions. Product segment uses `pdpUrl` when present:

- `https://www.nike.com/t/book-2-sunburst-basketball-shoes-bSDIOe8x/FZ7013-500`
- -> `book-2-sunburst-basketball-shoes-bSDIOe8x--FZ7013-500`

Fallback: `{productCode}.json` only.

---

## Workflow

### Step 1: Parse request

Extract:

- Product identifier (style or style-color, optional list)
- Scope (geo, marketplace, all, or default US)
- Channel (default Nike.com)
- Layout: nested vs flat (user says "flat" -> `--flat`)
- Language override (all languages vs default only)

### Step 2: Load channel config

```bash
curl -sf "https://snkrs.prod.commerce.nikecloud.com/globalization/consumer_channels/v3/${CHANNEL_ID}"
```

Save to a temp file for marketplace/language resolution.

### Step 3: Build fetch pairs

Each pair is `{"marketplace":"US","language":"en","productCode":"FZ7013"}`.

**`by-marketplace`:** for each marketplace/language in scope, for each style-color code, add one pair.

**`by-style-colors`:** one marketplace/language, one pair with bare style code.

**`combined`:** for each marketplace/language in scope, one pair with bare style code.

Estimate max files: style-color pairs count directly; style-code pairs may expand (warn if scope is large).

### Step 4: Confirm if needed

If estimated or configured max > 100, **AskQuestion** before proceeding.

### Step 5: Run fetch script

```bash
SKILL_DIR="<path-to-this-skill>"
python3 "${SKILL_DIR}/scripts/fetch_cpa.py" \
  --channel-id "${CHANNEL_ID}" \
  --channel-slug "${CHANNEL_SLUG}" \
  --output-dir /tmp/cpa-snapshots \
  --max 100 \
  --pairs "$(cat /tmp/cpa-pairs.json)"
```

Add `--flat` when the user wants a single directory.

The script prints the run directory at start and one status line per file.

### Step 6: Report

Summarize:

- Run directory (`/tmp/cpa-snapshots/{timestamp}/...`)
- Files saved / skipped / errors
- Sample paths
- Debug URLs used (one example)

---

## Pair JSON schema

```json
[
  {
    "marketplace": "US",
    "language": "en",
    "productCode": "FZ7013"
  }
]
```

Optional per-pair overrides (multi-channel runs):

```json
{
  "marketplace": "US",
  "language": "en",
  "productCode": "FZ7013-500",
  "channelId": "82a74ac1-c527-4470-b7b0-fb5f3ef3c2e2",
  "channelSlug": "nike-app"
}
```

If omitted, use `--channel-id` / `--channel-slug` from CLI.

---

## Example prompts

| User says | Mode | Pairs |
|-----------|------|-------|
| "Fetch CPA for FZ7013-500" | by-style-colors scope default | US/en, `FZ7013-500` |
| "Fetch FZ7013 for APLA" | combined | APLA marketplaces, `FZ7013` each |
| "FZ7013-500 across EMEA" | by-marketplace | EMEA markets, `FZ7013-500` |
| "All colorways of FZ7013 in US" | by-style-colors | US/en, `FZ7013` |
| "Flat layout, FZ7013 US and JP" | combined + `--flat` | US/en + JP/ja, `FZ7013` |

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| HTTP 404 on debug URL | Product may not exist in that market/language |
| Empty array for style code | No colorways in that market; skip and report |
| SSO / auth error on debug host | User may need VPN; retry with `curl` from their machine |
| Duplicate skipped | File already exists in run dir; delete run folder to re-fetch |
