---
name: dev-update-popular-search-terms
description: Updates popular_search_terms.jsonl in search.service.searchtypeahead from a Jira ticket (e.g. SRPLT-985), opens a PR without merging, and -- after merge -- publishes to S3 via Jenkins and verifies via the typeahead API. Use when the user mentions popular search terms, typeahead terms, updating search terms from a SRPLT ticket, or the Popular Search Terms Upload Process.
---

# Update Popular Search Terms

## Related skills

- **`vscode-workspace`** -- ensures `search.service.searchtypeahead` is in the active workspace
- **`github`** -- GitHub operations gateway (MCP first, built-in second, CLI third)
- **`pr-create`** -- PR creation workflow

Automates the [Popular Search Terms Upload Process](https://confluence.nike.com/pages/viewpage.action?pageId=1289484831) for `search.service.searchtypeahead`.

**Target repo:** `search.service.searchtypeahead`
**Target file:** `popular_search_terms.jsonl` (repo root)
**Jenkins job:** `typeahead/search.service.searchtypeahead.searchTermsS3Upload`

This skill runs in three phases. Each phase has a distinct trigger phrase so work stops at safe checkpoints.

| Phase | Trigger phrase | Stops after |
|-------|----------------|-------------|
| 1 | "update popular search terms from SRPLT-XXX" | PR created (no merge) |
| 2 | "deploy popular search terms to test for SRPLT-XXX" | Test verified |
| 3 | "deploy popular search terms to prod for SRPLT-XXX" | Prod verified |

## Prerequisites

### Workspace

`search.service.searchtypeahead` must be open in the workspace. If missing, use the `vscode-workspace` skill to add it.

### Credentials

| System | Variables | Setup |
|--------|-----------|-------|
| Jira (read) | `JIRA_API_TOKEN`, optional `JIRA_BASE_URL` | Bearer token for `jira.nike.com`. The `jira` skill (`jira_get_issue`) is preferred. |
| Jenkins (publish) | `JENKINS_USER`, `JENKINS_API_TOKEN` | Generate at `https://searchscience.jenkins.bmx.nikecloud.com/user/<user>/configure`. Or store in `~/.netrc` for `searchscience.jenkins.bmx.nikecloud.com`. |
| AWS (manual fallback only) | via `gimme-aws-creds` | Only needed if Jenkins S3 publish fails. Profile: `iamr-search-tools`. |

## Script reference

All scripts live in this skill folder under `scripts/`:

| Script | Purpose |
|--------|---------|
| `parse-jira-jsonl.py` | Extract JSONL lines from Jira `{code:java}` block; supports `-m CA,CAN,US` to filter marketplaces |
| `merge-marketplaces.py` | Merge ticket lines into existing file by `marketplace` key |
| `validate-jsonl.py` | Schema-check JSONL files |
| `trigger-jenkins.sh` | Trigger and poll S3 publish job (`test` or `prod`); sends correct deploy flow param |
| `verify-typeahead.sh` | Hit typeahead API, parse `searchTerms[].displayText`, assert terms appear; outputs verify URLs |

Resolve `SKILL_DIR` as the directory containing this `SKILL.md` file.

---

## Phase 1: Edit and open PR

**Trigger:** user provides a Jira ticket key (e.g. `SRPLT-985`).

### Step 1: Fetch Jira ticket

Use the `jira` skill's `jira_get_issue` pattern with the ticket key. Capture:

- `key` (e.g. `SRPLT-985`)
- `summary` (for commit/PR title)
- `description` (contains the JSONL code block)

If MCP is unavailable, fetch via REST:

```bash
curl -sf \
  -H "Authorization: Bearer ${JIRA_API_TOKEN}" \
  "${JIRA_BASE_URL:-https://jira.nike.com}/rest/api/2/issue/SRPLT-985?fields=summary,description"
```

Save the description to a temp file for parsing.

### Step 2: Parse ticket JSONL

```bash
SKILL_DIR="<path-to-this-skill>"
python3 "${SKILL_DIR}/scripts/parse-jira-jsonl.py" \
  -i /tmp/jira-description.txt \
  -o /tmp/ticket-updates.jsonl
```

Or pipe description on stdin:

```bash
echo "${DESCRIPTION}" | python3 "${SKILL_DIR}/scripts/parse-jira-jsonl.py" -o /tmp/ticket-updates.jsonl
```

### Step 3: Merge into popular_search_terms.jsonl

Locate the typeahead repo and pull latest master before merging:

```bash
TYPEAHEAD_REPO=$(find "${WORKSPACE_ROOT:-.}" -maxdepth 2 -type d -name "search.service.searchtypeahead" | head -1)
cd "${TYPEAHEAD_REPO}"
git fetch origin master && git pull origin master
CURRENT="${TYPEAHEAD_REPO}/popular_search_terms.jsonl"
```

Merge (dry-run to stdout first):

```bash
python3 "${SKILL_DIR}/scripts/merge-marketplaces.py" \
  --current "${CURRENT}" \
  --updates /tmp/ticket-updates.jsonl \
  --summary
```

Write merged output:

```bash
python3 "${SKILL_DIR}/scripts/merge-marketplaces.py" \
  --current "${CURRENT}" \
  --updates /tmp/ticket-updates.jsonl \
  --output /tmp/popular_search_terms.merged.jsonl
```

### Step 4: Validate

```bash
python3 "${SKILL_DIR}/scripts/validate-jsonl.py" /tmp/popular_search_terms.merged.jsonl
python3 "${SKILL_DIR}/scripts/validate-jsonl.py" "${CURRENT}"
```

### Step 4b: Ensure consistent formatting

The merge script may produce minified JSON (no spaces inside braces/brackets).
The existing file uses a spaced style:

```
{ "marketplace": "US", "languages": [ { "language": "en", "searchTerms": [ "term1", "term2" ] } ] }
```

After merging, compare the formatting of new/replaced lines against surrounding
lines. If new lines are minified while the rest of the file uses spaces, reformat
them to match. The canonical style is:

- Space after `{` and before `}`
- Space after `[` and before `]`
- Space after `:`
- Space after `,`

Apply this to the merged output file before proceeding to the diff step. A simple
approach is to re-serialize each replaced line through Python's `json.dumps` with
`separators=(", ", ": ")` and wrap with `{ ... }` / `[ ... ]` spacing, or use a
sed/awk pass. Verify the result still passes `validate-jsonl.py` after reformatting.

### Step 5: Show diff and confirm

```bash
diff -u "${CURRENT}" /tmp/popular_search_terms.merged.jsonl || true
```

Present a per-marketplace summary (replaced vs appended). Use **AskQuestion** to confirm before writing.

If the user declines, stop without modifying the repo.

### Step 6: Branch, commit, push

Only after confirmation:

```bash
cd "${TYPEAHEAD_REPO}"
git fetch origin master
git checkout master && git pull origin master
git checkout -b "feature/${TICKET_KEY}-update-search-terms"
cp /tmp/popular_search_terms.merged.jsonl popular_search_terms.jsonl
git add popular_search_terms.jsonl
git commit -m "${TICKET_KEY}: ${SUMMARY}"
git push -u origin HEAD
```

**Push access:** The user must be a member of a GitHub team with write access to `search.service.searchtypeahead` (e.g. `search-admins`, `search-meili`, `search-gogol`, or `search-grid-dynamics`). If push fails with a permission error, stop and help the user identify the correct team to request access from.

**Dry-run mode:** When the user says "dry-run" or `--dry-run`, stop after Step 5 (show diff only). Do not branch, commit, or push.

### Step 7: Create PR (do NOT merge)

Follow the `pr-create` skill. Key rules:

- Base branch: `master`
- Title: `${TICKET_KEY}: ${SUMMARY}` (truncate if needed)
- Body must link Jira: `[${TICKET_KEY}](https://jira.nike.com/browse/${TICKET_KEY})`
- List changed marketplaces in the Changes section
- **Never merge the PR.** Stop and hand off to the user.

### Step 8: Report and stop

Print:

```
Phase 1 complete.

PR: <url>
Changed marketplaces: CA, CAN, US, ...

Next steps (manual):
1. Get at least one approving review on the PR in GitHub
2. Merge the PR to master
3. Then say: "deploy popular search terms to test for SRPLT-XXX"
```

---

## Phase 2: Publish to test

**Trigger:** user says PR is merged and wants test deploy.

**Precondition:** PR for the ticket must be merged to `master`.

### Step 1: Confirm PR merged

```bash
cd "${TYPEAHEAD_REPO}"
gh pr list --search "${TICKET_KEY}" --state merged --json number,title,url
```

If no merged PR found, stop and ask the user to merge first.

### Step 2: Trigger Jenkins S3 publish

**Jenkins job:** `typeahead/search.service.searchtypeahead.searchTermsS3Upload`
**Instance:** searchscience
**Jenkinsfile:** `Jenkinsfile_searchTermsS3publish`
**Pipeline config:** `@Library cop-pipeline-configuration@searchPipelinev1`

#### Jenkins parameters reference

The S3 publish job accepts these parameters:

| Parameter | Values | Purpose |
|-----------|--------|---------|
| `Flow` | `BRANCH_MATCHER` (default), `RELEASE`, `PRODUCTION`, `WAFFLE_ONLY` | Which deploy flow to execute |
| `Deploy_Environment` | `FLOW_DEFINED` (default), `test`, `prod` | Which environment(s) to target |

**IMPORTANT:** `Deploy_Environment` defaults to `FLOW_DEFINED` which loops over ALL
environments that define the selected flow. You MUST specify the exact environment
to avoid deploying to unintended targets (e.g. China environments added by the
common-s3 profile).

#### Environment-to-parameter mapping

| Target | Flow | Deploy_Environment |
|--------|------|--------------------|
| Test | `RELEASE` | `test` |
| Prod | `PRODUCTION` | `prod` |

**Note:** `testSearchWaffle` and `prodSearchWaffle` exist in the pipeline config
but have EMPTY deploy flows (no stages). The actual S3Publish steps are only
defined in `test` and `prod`.

#### Trigger test publish

```bash
python3 "${SKILL_DIR_BMX}/scripts/jenkins_api.py" \
  --action build \
  --service "search.service.searchtypeahead.searchTermsS3Upload" \
  --instance searchscience \
  --branch master \
  --params "Flow=RELEASE,Deploy_Environment=test"
```

Where `SKILL_DIR_BMX` is the ops-bmx skill directory.

On failure, print the build URL and stop. Do not proceed to verification.

#### Feature branch S3 publish (pre-merge testing)

On a **new** feature branch, the first build is always a "discovery" build --
Jenkins reads the Jenkinsfile to learn the parameters but does not execute any
deploy stages (all stages are skipped).

To publish from a feature branch before merge:

1. Trigger a plain build on the feature branch (no params) to let Jenkins discover
   the branch and register its parameters. This build will succeed but skip S3Publish.
2. Once that first build completes, trigger a **second** build with explicit
   parameters. Jenkins now knows the branch's parameterized job definition and
   will honor the params.

```bash
python3 "${SKILL_DIR_BMX}/scripts/jenkins_api.py" \
  --action build \
  --service "search.service.searchtypeahead.searchTermsS3Upload" \
  --instance searchscience \
  --branch "feature/${TICKET_KEY}-update-search-terms" \
  --params "Flow=RELEASE,Deploy_Environment=test"
```

### Step 3: Cycle test instances

The searchtypeahead service loads `popular_search_terms.jsonl` from S3 at startup.
After publishing, cycle instances so they pick up the new file.

**ASG naming pattern:** `search-searchtypeahead-master-test-v0XX` (blue/green, two ASGs)

```bash
# Find the ASGs
aws autoscaling describe-auto-scaling-groups \
  --region us-east-1 \
  --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'searchtypeahead')].AutoScalingGroupName" \
  --output text

# Start instance refresh on each ASG (launches new instances before terminating old)
aws autoscaling start-instance-refresh \
  --region us-east-1 \
  --auto-scaling-group-name "<ASG_NAME>" \
  --preferences '{"MinHealthyPercentage": 100, "MaxHealthyPercentage": 200, "InstanceWarmup": 120}'
```

Run `start-instance-refresh` for EACH ASG found (typically two for blue/green).

**Parameters explained:**
- `MinHealthyPercentage=100` -- never go below full capacity
- `MaxHealthyPercentage=200` -- allow launching new instances before terminating old
- `InstanceWarmup=120` -- wait 2 minutes for new instances to be ready

**Monitor progress:**

```bash
aws autoscaling describe-instance-refreshes \
  --region us-east-1 \
  --auto-scaling-group-name "<ASG_NAME>" \
  --query "InstanceRefreshes[0].{Status:Status,Percent:PercentageComplete}" \
  --output table
```

Wait for status `Successful` on all ASGs before verifying.

### Step 4: Verify test typeahead

```bash
"${SKILL_DIR}/scripts/verify-typeahead.sh" test "${TICKET_KEY}"
```

Or with a local file (no Jira token needed). Either the parsed ticket JSONL or the repo's full file works:

```bash
"${SKILL_DIR}/scripts/verify-typeahead.sh" test "${TICKET_KEY}" /tmp/ticket-updates.jsonl
"${SKILL_DIR}/scripts/verify-typeahead.sh" test "${TICKET_KEY}" "${TYPEAHEAD_REPO}/popular_search_terms.jsonl"
```

On any FAIL row, stop and investigate before prod.

#### Verification URLs

Build one verification URL per marketplace/language combination from the JSONL:

```
https://snkrs.test.commerce.nikecloud.com/search/suggestions/v1?country={marketplace}&language={language}&count=10
```

The `country` and `language` params must match the `marketplace` and `languages[].language` values in the JSONL file **exactly**. Mismatches (e.g. using `en` when the JSONL says `en-gb`) return an empty `searchTerms` array with no error.

When presenting results, include a table with columns: Marketplace, Language, New Terms, Status, Verify URL.

#### Response format

The API returns terms under `searchTerms[].displayText` (not `response.popularSearchTerms`):

```json
{
  "searchTerms": [
    { "id": "1", "displayText": "all conditions gear", "searchText": "all conditions gear" },
    { "id": "2", "displayText": "golf shoes", "searchText": "golf shoes" }
  ],
  "resourceType": "suggestion",
  "resourceVersion": "v2"
}
```

Custom (popular) terms appear first in the array, followed by any auto-generated suggestions.

### Step 5: Report and stop

```
Phase 2 complete. Test environment verified.

Next: say "deploy popular search terms to prod for SRPLT-XXX"
```

---

## Phase 3: Publish to prod

**Trigger:** user explicitly requests prod deploy after test verification.

**Gate:** Use **AskQuestion** before triggering prod:

> "Test verification passed. Proceed with production S3 publish and instance restart?"

If no, stop.

### Step 1: Trigger Jenkins prod publish

```bash
python3 "${SKILL_DIR_BMX}/scripts/jenkins_api.py" \
  --action build \
  --service "search.service.searchtypeahead.searchTermsS3Upload" \
  --instance searchscience \
  --branch master \
  --params "Flow=PRODUCTION,Deploy_Environment=prod"
```

### Step 2: Cycle prod instances

Same approach as test. ASG naming pattern: `search-searchtypeahead-master-prod-v0XX`

```bash
# Find the ASGs
aws autoscaling describe-auto-scaling-groups \
  --region us-east-1 \
  --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'searchtypeahead') && contains(AutoScalingGroupName, 'prod')].AutoScalingGroupName" \
  --output text

# Start instance refresh on each ASG
aws autoscaling start-instance-refresh \
  --region us-east-1 \
  --auto-scaling-group-name "<ASG_NAME>" \
  --preferences '{"MinHealthyPercentage": 100, "MaxHealthyPercentage": 200, "InstanceWarmup": 120}'
```

Run for EACH ASG found. Monitor with `describe-instance-refreshes` until `Successful`.

### Step 3: Verify prod typeahead

```bash
"${SKILL_DIR}/scripts/verify-typeahead.sh" prod "${TICKET_KEY}"
```

#### Verification URLs

Same pattern as test, but against prod:

```
https://snkrs.prod.commerce.nikecloud.com/search/suggestions/v1?country={marketplace}&language={language}&count=10
```

See Phase 2 notes for language code matching rules and response format details.

### Step 4: Report done

```
Phase 3 complete. Production popular search terms updated and verified.

Jenkins: <build url>
Ticket: https://jira.nike.com/browse/${TICKET_KEY}
```

Add a Jira comment via MCP `jira_add_comment` with the verification results table. Use this format for consistency between test and prod comments:

```
{env} deployment completed and verified on {date}.

All {N} marketplace/language combinations confirmed returning the updated popular search terms:

||Marketplace||Language||New Terms||Status||Verify URL||
|{marketplace}|{language}|{terms}|Pass|[API|{url}]|
```

Then transition the ticket to Done via MCP `jira_transition_issue`.

---

**Troubleshooting, JSONL schema, and follow-up work:** see [REFERENCE.md](REFERENCE.md).
