# Update Popular Search Terms -- Reference

Detailed reference content for the `update-popular-search-terms` skill.

## Troubleshooting

### Jira code block not found

The ticket description must contain a `{code:java}...{code}` block with one JSON object per line. Ask the reporter to fix the ticket format.

### Duplicate marketplace in ticket

`parse-jira-jsonl.py` rejects duplicate `marketplace` keys. Only one line per marketplace in the ticket block.

### New marketplace appended

If `merge-marketplaces.py` reports `appended (new)`, confirm with the user that adding a new marketplace is intentional.

### Jenkins auth failure

```bash
export JENKINS_USER=<nt-username>
export JENKINS_API_TOKEN=<token-from-jenkins-configure-page>
```

Or add to `~/.netrc`:

```
machine searchscience.jenkins.bmx.nikecloud.com
login <nt-username>
password <api-token>
```

### Jenkins job fails

Check build console at the URL printed by `trigger-jenkins.sh`. Common causes: AWS role assumption, S3 permissions, stale workspace checkout.

### Typeahead verification fails after instance cycling

- Confirm the ASG has cycled all instances (check AWS EC2 console for new launch times)
- Allow 2-5 minutes for new instances to load S3 file
- Re-run `verify-typeahead.sh`
- Check S3 object directly:
  - Test: `s3://nike-commerce-test-app-internal/applications/search/autocompleteingest/popular_search_terms.jsonl`
  - Prod: `s3://nike-commerce-prod-app-internal/applications/search/autocompleteingest/popular_search_terms.jsonl`
- Fallback: redeploy the service via the main Jenkins pipeline (blue/green deploy), which replaces instances with fresh ones that load from S3 on startup

### Manual S3 fallback (Jenkins down)

Only when Jenkins is unavailable. See Confluence runbook:

1. Download current file from S3 console
2. Apply the same merge locally using `merge-marketplaces.py`
3. Upload back to the same S3 key
4. Start an instance refresh on the searchtypeahead ASG
5. Verify with `verify-typeahead.sh`

For prod S3 upload, use AppStream/VDI route per Confluence.

### AWS credentials (manual fallback)

```bash
gimme-aws-creds --profile iamr-search-tools
```

Commerce test account: `233367263614`. Commerce prod requires VDI/AppStream.

---

## JSONL schema

Each line is one JSON object:

```json
{ "marketplace": "US", "languages": [ { "language": "en", "searchTerms": [ "term one", "term two" ] } ] }
```

| Field | Type | Rules |
|-------|------|-------|
| `marketplace` | string | ISO country/market code (e.g. `US`, `CA`, `CAN`, `GB`) |
| `languages` | array | At least one entry |
| `languages[].language` | string | BCP-47-ish code (e.g. `en`, `en-gb`, `fr`, `es-419`) |
| `languages[].searchTerms` | array | At least one non-empty string |

---

## Follow-up work

- [ ] **`scripts/instance-refresh.sh`**: Automate ASG instance refresh via AWS CLI (`aws autoscaling start-instance-refresh`) once IAM roles and CLI access patterns are confirmed. Until then, Phase 2/3 use manual AWS console steps above.
