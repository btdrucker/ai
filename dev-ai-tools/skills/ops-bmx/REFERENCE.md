# Job Discovery

The script dynamically discovers jobs by searching Jenkins instances. Pass any
substring of the job name to `--service` and the script will find the best match
by recursively searching through folders.

## Instances

| Instance | URL |
|----------|-----|
| `productfeed` | https://productfeed.jenkins.bmx.nikecloud.com/ |
| `searchscience` | https://searchscience.jenkins.bmx.nikecloud.com/ |
| `smartsearch` | https://smartsearch.jenkins.bmx.nikecloud.com/ |

## How discovery works

1. The script searches each instance recursively (folders up to 3 levels deep)
2. All jobs whose name contains the `--service` value (case-insensitive) are collected
3. Results are ranked by:
   - **Match quality**: exact name match > ends-with match > substring match
   - **Job type**: multibranch pipelines preferred over other types
   - **Path depth**: shallower paths preferred
4. The best match is selected and its full path is used for API calls

## Speed tips

- Provide `--instance` alongside `--service` to search only that instance (much faster)
- Use `--action list --instance <name>` to browse all jobs on an instance
- Use the full job name (e.g. `search.service.kingpin-v2`) for unambiguous matches

## Folder structure

Jobs are often nested in folders. The script handles this transparently:

- **productfeed**: most jobs are top-level (`envoy`, `kirbyv2`, etc.)
- **searchscience**: most jobs are nested (`coresearch/`, `searchx/`, `rollupsv2/`, `typeahead/`, etc.)
- **smartsearch**: folder structure varies

---

# Pipeline Configuration

## How cop-pipeline works

The cop-pipeline system is a layered Jenkins shared library framework. A
service's `Jenkinsfile` is a thin configuration wrapper -- the actual build,
test, bake, and deploy logic lives in the shared libraries.

**Execution flow:**

```
Jenkinsfile
  |
  |-- @Library loads shared libraries (bootstrap, cicd-pipeline, config, steps)
  |
  |-- mergeConfiguration(parameterMap, config)
  |     |-- reads profile .groovy files from cop-pipeline-configuration
  |     |-- merges them in order (profiles first, then Jenkinsfile overrides)
  |     |-- produces a single merged config map
  |
  |-- pipelineFunction(mergedConfig)     e.g. ec2BlueGreenDeployPipeline()
        |-- PipelineProperties.createProperties()  --> Jenkins build parameters
        |-- orchestrates stages: checkout, build, test, bake, deploy
        |-- each stage delegates to cop-pipeline-step implementations
```

**Library layers (bottom-up):**

| Layer | Repo | Role |
|-------|------|------|
| Bootstrap | `cop-pipeline-bootstrap` | Entry point; loads the other 3 libraries. Handles dynamic version/branch resolution for config and steps. |
| Configuration | `cop-pipeline-configuration` | Team-specific profiles (`.groovy` files). One branch per team (e.g. `searchPipelinev1`). Defines `buildFlow`, `deployFlow`, `deploymentEnvironment` defaults. |
| Pipeline functions | `cicd-pipeline` | High-level orchestrators (`vars/*.groovy`). Each function defines stages and calls `PipelineProperties.createProperties()` to generate build parameters. |
| Steps | `cop-pipeline-step` | Atomic reusable steps (e.g. `ec2BlueGreenDeploy`, `bakePacker`, `gradleBuild`). Called by pipeline functions. |

**Configuration merge order** (`mergeConfiguration`):

1. Profile `.groovy` files -- loaded from the config repo in the order listed
   under the `profile` key. Each profile can set `buildFlow`,
   `deploymentEnvironment`, `deployFlow`, and other defaults.
2. Jenkinsfile inline config -- merged last, highest priority. Maps merge
   recursively (deep merge); scalars override.

The merged config drives everything: which environments exist, what flows
are available, ASG sizing, infrastructure settings, and which stages run.

## COP Pipeline Repos

| Repo | Branch pattern | Purpose |
|------|---------------|---------|
| `nike-cop-pipeline/cop-pipeline-configuration` | `@<teamBranch>` in `@Library` | Team-specific profiles and deploy environment defaults |
| `nike-cop-pipeline/cicd-pipeline` | (default branch) | Core pipeline shared library -- build, test, bake, deploy steps |
| `nike-cop-pipeline/cop-pipeline-step` | (default branch) | Reusable atomic pipeline step implementations |
| `nike-cop-pipeline/cop-pipeline-bootstrap` | (default branch) | Loads pipeline libs; `loadPipelines()` / `loadSharedConfiguration()` |

## Known Configuration Branches

These are referenced in Jenkinsfiles via `@Library(['cop-pipeline-configuration@<branch>'])`:

| Branch | Team | Services |
|--------|------|----------|
| `productfeedWaffleOnly` | Product Feeds | envoy, productfeedv2, collections, kirby, maestro, pf* |
| `searchPipelinev1` | Search Platform | productcatalogeventcomposer, and newer Search services |
| `searchscienceWaffleOnly` | Search Science | kingpin, searchservice, searchingest, concepts, rules, nav |

## Common Profile Paths

Profiles are referenced in the Jenkinsfile `config.profile` block and resolved
from the `cop-pipeline-configuration` repo at the specified branch:

| Profile path | Purpose |
|--------------|---------|
| `team/product-feed/common.groovy` | Product Feed team defaults |
| `team/product-feed/ec2-pipeline-defaults.groovy` | EC2 deploy pipeline defaults for PF |
| `team/product-feed/ec2-pipeline-canary-referee.groovy` | Canary deploy referee config |
| `stack/with-gradle-caching.groovy` | Enables Gradle build caching |

## Pipeline Functions

The function called at the bottom of the Jenkinsfile determines the deploy strategy:

| Function | What it does |
|----------|--------------|
| `ec2BlueGreenDeployPipeline(config)` | Build, bake AMI, deploy via blue-green ASG swap |
| `ec2DeployPipeline(config)` | Build, bake AMI, rolling deploy |
| `lambdaSamDeployPipeline(config)` | Build and deploy Lambda via SAM |
| `ecsDeployPipeline(config)` | Build container, deploy to ECS |
| `ecsTerraformPipeline(config)` | ECS deploy via Terraform |
| `terraformContainerPipeline(config)` | Generic Terraform container deploy |
| `npeDeployPipeline(config)` | Non-prod-only deploy pipeline |
| `buildOnlyPipeline(config)` | Build and test only -- no deploy |
| `perfTestPipeline(config)` | Performance testing (skipDefaults=true) |

## Parameter Resolution Source Chain

Used by the "Resolving build parameters" algorithm in SKILL.md.

| Repo | Key file | What to look for |
|------|----------|------------------|
| `cicd-pipeline` | `vars/<pipelineFunction>.groovy` | Extra params before `createProperties()` call (e.g. `BAKED_AMI_ID`, `IMAGE_TAG`) |
| `cicd-pipeline` | `src/com/nike/acid/helper/PipelineProperties.groovy` | Default param generation: `Flow`, `Deploy_Environment`, `Refresh_Parameters` |
| config repo | `resources/team/<team>/*.groovy` | Profile defaults: `buildFlow`, `deploymentEnvironment`, `deployFlow` keys |

All standard repos: `github.com/nike-cop-pipeline/<name>`

### `createProperties` signature

```groovy
createProperties(steps, config, pipelineParameters = null, skipDefaults = false, skipQMAParams = false)
```

- `pipelineParameters`: list of extra Jenkins parameters added by the specific pipeline function
- `skipDefaults`: if `true`, the 3 default params (`Refresh_Parameters`, `Flow`, `Deploy_Environment`) are NOT generated
- `skipQMAParams`: if `true`, QMA params are suppressed

QMA params (`AUTHOR`, `PR_TITLE`, `JIRA_TICKETS`, `CHANGE_REQUEST_ID`) are
auto-populated by the PRA dispatch system -- ignore for manual `--params` builds.

---

# Branch-to-Environment Conventions

## Multibranch Pipeline Behavior

BMX multibranch pipelines discover all branches in the GitHub repo. The
Jenkinsfile's deploy logic uses branch name to determine deployment scope:

| Branch pattern | Typical behavior |
|----------------|-----------------|
| `main` or `master` | Full pipeline: build -> test deploy -> prod deploy |
| `feature/*`, `bugfix/*`, other | Build and test deploy only (no prod) |
| PR branches | Build only (no deploy) |

**Key rule:** On most Search services, building `main`/`master` WILL deploy to
production. This is why the safety protocol in SKILL.md exists.

## Deployment Environment Structure (from Jenkinsfile)

```groovy
deploymentEnvironment: [
    test: [
        deploy: [ desiredCapacity: 1, maxSize: 1, minSize: 1, ... ],
        infrastructure: [ loadBalancer: [ ... ] ]
    ],
    prod: [
        deploy: [ desiredCapacity: N, maxSize: M, minSize: P, ... ],
        infrastructure: [ loadBalancer: [ ... ] ]
    ]
]
```

If `prod` is present and the branch matches, the pipeline deploys to production.

## AMI Bake and Share Flow

Some services use a two-stage deployment where the AMI is baked in one build
and deployed in a subsequent build:

1. **Bake stage** -- builds the application, creates an AMI, writes the AMI ID
   to `build/ami_info.txt` (or similar artifact path)
2. **AMI sharing** -- if the AMI was baked in the test account (554036784086) and
   needs to deploy to prod (832844619813), it must be shared cross-account first.
   This is typically handled by the pipeline automatically, but may require a
   separate step in some configurations.
3. **Deploy stage** -- uses the AMI ID from the bake stage to perform the
   blue-green or rolling deploy

When investigating a failed deploy, check:
- Did the bake stage succeed? (look for `ami_info.txt` in build artifacts)
- Was the AMI shared to the target account?
- Is the AMI ID still valid (not deregistered)?

---

# Multibranch Pipeline Build Strategies

When creating or troubleshooting a multibranch pipeline, the **Build Strategies**
section controls which discovered branches/PRs automatically trigger builds.

## Required strategies

Per BMX documentation, every multibranch pipeline needs **two** build strategies:

1. **Change Requests** -- triggers builds for pull requests
2. **Named Branches** -- triggers builds for named branches (e.g. `main`)

Without both, Jenkins will *discover* PRs and branches but not *build* them.

## XML config reference

The `<buildStrategies>` block lives inside `<jenkins.branch.BranchSource>`:

```xml
<buildStrategies>
  <jenkins.branch.buildstrategies.basic.ChangeRequestBuildStrategyImpl plugin="basic-branch-build-strategies@190.v343a_ee70d920">
    <ignoreUntrustedChanges>false</ignoreUntrustedChanges>
  </jenkins.branch.buildstrategies.basic.ChangeRequestBuildStrategyImpl>
  <jenkins.branch.buildstrategies.basic.NamedBranchBuildStrategyImpl plugin="basic-branch-build-strategies@190.v343a_ee70d920">
    <filters>
      <jenkins.branch.buildstrategies.basic.NamedBranchBuildStrategyImpl_-ExactNameFilter>
        <name>main</name>
        <caseSensitive>false</caseSensitive>
      </jenkins.branch.buildstrategies.basic.NamedBranchBuildStrategyImpl_-ExactNameFilter>
    </filters>
  </jenkins.branch.buildstrategies.basic.NamedBranchBuildStrategyImpl>
</buildStrategies>
```

## Common defect

If only `NamedBranchBuildStrategyImpl` is present (filtering to `main`), PRs
will be discovered but show `notbuilt` status. The fix is to add the
`ChangeRequestBuildStrategyImpl` strategy.

## Diagnosing "discovered but not built"

1. Fetch the pipeline config:
   ```bash
   python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
     --action get-config --service <name> > /tmp/config.xml
   ```
2. Check `<buildStrategies>` -- if `ChangeRequestBuildStrategyImpl` is missing,
   that's the problem.
3. Fix by adding the strategy and updating via Jenkins API or UI.
4. As a workaround, trigger the build manually:
   ```bash
   python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
     --action build --service <name> --branch PR-<N>
   ```

---

# Presenting Results

- `status` returns the last build's result, number, duration, and URL
- `history` returns an array of recent builds with the same fields
- `console` returns raw console text (can be very long -- consider piping through
  `tail` or searching for specific patterns)
- Build timestamps are Unix epoch milliseconds -- convert for display

---

# GitHub Webhook Proxy

GitHub Cloud has no direct network connectivity to BMX Jenkins inside the Nike
network. A proxy service routes webhook events from GitHub to Jenkins.

## Recommended proxy URL format

```
https://github.services.nike.com/github/event-proxy/v1/bmx/{bmx_name}
```

Where `{bmx_name}` is the subdomain of the BMX URL. Examples:

| Instance | Payload URL |
|----------|-------------|
| `searchscience` | `https://github.services.nike.com/github/event-proxy/v1/bmx/searchscience` |
| `productfeed` | `https://github.services.nike.com/github/event-proxy/v1/bmx/productfeed` |
| `smartsearch` | `https://github.services.nike.com/github/event-proxy/v1/bmx/smartsearch` |

## Legacy proxy

Some older repos still use `https://github-webhooks.baat-tools-prod.nikecloud.com/v1/<jenkins-webhook-url>`.
This still works but is not the current recommended format.

## Webhook setup

In the GitHub repo Settings > Webhooks:

- **Payload URL:** the proxy URL above
- **Content type:** `application/json`
- **SSL verification:** Enabled
- **Events:** Select "Let me select individual events" and choose:
  - Pull requests
  - Pushes

Do NOT select "Send me everything".

---

# Jenkins Web UI

Direct links to instances:

- Product Feed: https://productfeed.jenkins.bmx.nikecloud.com/
- Search Science: https://searchscience.jenkins.bmx.nikecloud.com/
- Smart Search: https://smartsearch.jenkins.bmx.nikecloud.com/

Job URL pattern: `https://<instance>.jenkins.bmx.nikecloud.com/job/<jobName>/job/<branch>/`
