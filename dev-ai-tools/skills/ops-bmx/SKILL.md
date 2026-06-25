---
name: ops-bmx
description: >
  BMX Jenkins operations for Search Engineering -- trigger builds, check build
  status, view console output, and inspect build history. Understands the
  cop-pipeline configuration system and enforces safety guardrails for
  production deployments. Use when the user wants to build, deploy, check CI
  status, trigger a Jenkins job, or investigate a build failure.
---

# BMX Jenkins Operations

Interact with Search Engineering BMX Jenkins instances via the REST API.

**Service mapping, pipeline profiles, and branch conventions:** see [REFERENCE.md](REFERENCE.md).

## Related skills

- **`github`** -- GitHub operations gateway (clone repos, PRs, etc.)
- **`search-kb`** -- identify which service to operate on and its deployment context
- **`search-sdlc`** -- branching strategy and environment promotion rules
- **`git`** -- commit and push changes that will trigger builds

## Authentication

Resolve `SKILL_DIR` as the directory containing this `SKILL.md` file.

### Username

Stored in `${SKILL_DIR}/tokens/username.txt`.

Override: set the `JENKINS_USER` environment variable (takes precedence over file).

Fallback: `~/.cursor/skills/ops-bmx/tokens/username.txt`

If missing, the script exits with an error and suggests the value from `git config user.email`.

**Agent behavior when username.txt is missing:**

1. Run `git config user.email` to discover the likely username
2. Ask the user: "Your git email is `<email>`. Is this also your Jenkins username?"
3. If confirmed, write it to `${SKILL_DIR}/tokens/username.txt`
4. If not, ask for the correct username and write that instead

### API Tokens

Each BMX instance requires its own token file: `${SKILL_DIR}/tokens/<instance>_token.txt`

Override: set the `JENKINS_TOKEN` environment variable (takes precedence; applies to all instances).

Fallback: `~/.cursor/skills/ops-bmx/tokens/<instance>_token.txt`

Available instances: `productfeed`, `searchscience`, `smartsearch`

**If a token file is missing**, tell the user:

1. Go to `https://<instance>.jenkins.bmx.nikecloud.com/user/<username>/configure`
   (or: Profile dropdown -> Security -> API Token section)
2. Click "Add new Token", give it a name, click "Generate"
3. Copy the token immediately -- it is only shown once
4. Paste it into the chat

Then write the token to `${SKILL_DIR}/tokens/<instance>_token.txt`.

### If authentication fails (401/403)

The token may have been revoked or expired. Guide the user through regenerating
it using the steps above.

---

## Instance selection

The team's primary Jenkins instances are **productfeed** and **searchscience**.

**Always confirm which Jenkins instance you are operating against before running
any command.** Even when the instance can be derived from context (e.g. from the
`--service` mapping or the repo the user is working in), state it explicitly:

> "This will run against the **productfeed** Jenkins instance. Correct?"

If unclear, ask the user to choose -- always present the primary instances first:

> "Which BMX instance? (`productfeed`, `searchscience`, or other: `smartsearch`)"

When using `--service`, the script searches Jenkins instances for a matching
job (recursing into folders). Provide `--instance` as a hint to search that
instance first (much faster). When using `--action list`, `--job-path`, or
`--action create-job`, the `--instance` flag is required.

---

## Running commands

### Check build status

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action status --service envoy
```

### View build history

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action history --service envoy --count 10
```

### Get console output

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action console --service envoy --build 343
```

### Fetch a build artifact

```bash
# Get the baked AMI ID (always use this, never grep console for ami- strings)
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action artifact --service envoy --branch main \
  --artifact-path ami_info.txt

# List all artifacts for a build
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action artifact --service envoy --branch main --build 42
```

### List all jobs on an instance

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action list --instance productfeed
```

### Trigger a branch build

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action build --service envoy --branch master
```

### Trigger a PR build

PR builds and branch builds are different jobs in Jenkins multibranch pipelines.
To trigger a PR build, use `--branch PR-<number>` (not the feature branch name).

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action build --service envoy --branch PR-42
```

**When to use which:**
- `--branch feature/my-change` triggers a **branch build** (may deploy to test)
- `--branch PR-42` triggers a **PR build** (build and test only, no deploy)

If the user asks to "kick off the PR build" or "trigger CI for the PR", always
use `--branch PR-<number>`. If they ask to "build the branch" or "deploy to
test", use the branch name.

### Trigger a parameterized build

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action build --service searchtypeahead.searchTermsS3Upload \
  --instance searchscience --branch master \
  --params "Deploy_Environment=test,Flow=RELEASE"
```

Uses `buildWithParameters` instead of `build`. Pass comma-separated KEY=VALUE pairs.

**You MUST resolve parameters before using `--params`.** See the next section.

---

## Resolving build parameters

**Before using `--params` on any build trigger**, resolve the exact parameter
names and valid values by tracing the pipeline source code. Never guess.

### Step 1: Read the Jenkinsfile

Variable names differ per project, so read the actual code. Extract:

- **Config repo and branch.** Three `@Library` patterns exist:
  - `cop-pipeline-configuration@<branch>` in `@Library` directly
  - `@Library` has only `cop-pipeline-bootstrap`; config loaded via
    `loadSharedConfiguration('<branch>')` or `loadPipelines('<ver>', '<branch>')`
  - A separate config repo entirely (e.g. `gcde-pipeline-configuration`)
- **The config map** passed to `mergeConfiguration()` and the pipeline function.
  Look for these **map keys** (fixed by the framework, not the author):
  - `profile` -- paths to `.groovy` profile files in the config repo
  - `buildFlow` -- additional Flow choices if present
  - `deploymentEnvironment` -- environment overrides (especially `deployFlow`)
- **The pipeline function call** at the bottom (e.g. `ec2BlueGreenDeployPipeline(...)`,
  `lambdaSamDeployPipeline(...)`)

### Step 2: Check out source repos

You need the config repo (at the right branch) and `cicd-pipeline`. Before
cloning, ask:

> "I need to check out these repos to resolve build parameters:
> - `<config-repo>` (branch: `<branch>`)
> - `cicd-pipeline`
>
> Default: `/tmp/<repo-name>`. Override?"

- Default to `/tmp/<repo-name>`; reuse if already cloned at the right branch
- Wrong branch: `git fetch origin <branch> && git checkout <branch>`
- Use `--depth 1 --branch <branch>` for speed
- Standard repos: `github.com/nike-cop-pipeline/<name>`
- Non-standard config repo: ask the user for its GitHub URL

### Step 3: Read profiles and pipeline function source

**(a) Profiles:** For each path under the `profile` key, read
`resources/<path>` in the config repo. Extract `buildFlow` keys,
`deploymentEnvironment` keys, and `deployFlow` keys within each environment.

**(b) Pipeline function:** Read `cicd-pipeline/vars/<functionName>.groovy`.
Look for:
- A `*PipelineParameters` variable before `createProperties()` -- these are
  extra params (e.g. `BAKED_AMI_ID`, `IMAGE_TAG`). Always read the source.
- The `createProperties()` call args -- if `skipDefaults` (4th arg) is `true`,
  the 3 default params below are NOT generated.

### Step 4: Compute final parameters

Unless `skipDefaults=true`, `PipelineProperties.createProperties()` (in
`cicd-pipeline/src/com/nike/acid/helper/PipelineProperties.groovy`) generates:

- `Refresh_Parameters` (choice): `No` / `Yes`
- `Flow` (choice): `BRANCH_MATCHER` (default) + all `buildFlow` keys +
  all `deployFlow` keys from every `deploymentEnvironment` (deduplicated)
- `Deploy_Environment` (choice): `FLOW_DEFINED` (default) +
  all `deploymentEnvironment` keys + any `supportedEnvironments` entries

Plus: pipeline-specific params from Step 3b, and any `customBuildParameters`
entries (prefixed with `CUSTOM_`).

Merge rules: profiles merge in `profile` key order; Jenkinsfile config merges
last (highest priority); maps merge recursively; scalars override. An
environment with empty `deployFlow` maps still appears in `Deploy_Environment`
but runs zero stages for that flow.

### Step 5: Present to user

List all parameters with valid choices. Flag which Flow values deploy to
which environments. Warn on production flows.

---

## Build trigger safety protocol

**CRITICAL: Follow this protocol every time a user asks to trigger a build.**

### Step 1: Resolve build parameters

Follow the "Resolving build parameters" algorithm above. Never guess
parameter names.

Common mistakes: `Flow` not `Build_Flow`/`Deploy_Flow`.
`Deploy_Environment` not `DeployEnvironment`/`Environment`. These names come
from `PipelineProperties.createProperties()` and are universal across
cop-pipeline functions.

### Step 2: Initialize parameters on new branches

Jenkins only creates build parameters after a branch's Jenkinsfile has been
parsed by at least one build. If the branch has **never been built**
(shows "N/A" for Last Success/Failure in Jenkins, or `--action status`
returns no builds), a parameterized build (`--params`) will fail with
HTTP 500.

**To initialize parameters on a never-built branch:**

1. Trigger a plain build (no `--params`):
   ```bash
   python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
     --action build --service <name> --branch <branch>
   ```
2. Monitor via `--action status` or the Jenkins UI until the build starts
   its first stage (meaning the Jenkinsfile was parsed and parameters were
   registered).
3. Abort the build in the Jenkins UI (it will otherwise run the default
   `BRANCH_MATCHER` flow, which you may not want).
4. Now trigger the parameterized build with `--params`.

Tell the user: "This branch hasn't been built yet, so I need to kick off
a quick initialization build first. Once it starts, abort it in the Jenkins
UI, then I'll trigger the real build with parameters."

### Step 3: Determine if this is a production deployment

A build deploys to production if ALL of these are true:

- The branch matches the production branch pattern (typically `main`/`master`)
- The config has a prod environment under `deploymentEnvironment`
- The pipeline function is a deploy pipeline (e.g. `ec2BlueGreenDeployPipeline`,
  `lambdaSamDeployPipeline`, `npeDeployPipeline`)

### Step 4: Warn on production deployments

If the build WILL deploy to production:

**ALWAYS** warn the user explicitly:

> **WARNING: This build will deploy to PRODUCTION.**
>
> Service: `<service>`
> Branch: `<branch>`
> Pipeline: `<pipeline function>`
> Prod config: `<ASG sizes, instance type, etc.>`
>
> Do you want to proceed?

**NEVER** trigger a production build without explicit user confirmation.

### Step 5: Check for AMI dependencies (EC2 pipelines)

EC2 pipelines (`ec2BlueGreenDeployPipeline`, `ec2DeployPipeline`) use a
two-stage flow: a build flow that bakes the AMI (e.g. `RELEASE`) and a
deploy flow that uses it (e.g. `PRODUCTION`). The `PRODUCTION` buildFlow
typically only runs `['Prepare', 'Smart Share']` -- it does NOT bake.

**When the user wants a PRODUCTION deploy, you MUST find an existing AMI.**

**ALWAYS use the `artifact` action** to get the baked application AMI.
NEVER grep the console output for `ami-` strings -- console output contains
foundation/base AMI IDs that look similar but are NOT the baked application
AMI and will cause auth failures during Smart Share.

1. Fetch the baked AMI from the build artifact:
   ```bash
   python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
     --action artifact --service <name> --branch <branch> \
     --artifact-path ami_info.txt
   ```
   This returns lines like `us-east-1: ami-05fc14cf2178ab1b7`.
   Pick the region matching the target deploy environment.

   For richer metadata (arch, name, tags), use the JSON artifact:
   ```bash
   python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
     --action artifact --service <name> --branch <branch> \
     --artifact-path .pipeline/ami/ami_info.json
   ```
2. If an AMI exists, pass it as `BAKED_AMI_ID=<ami-id>` in `--params`.
3. If no AMI artifact exists (no prior RELEASE build, or AMI
   expired/deregistered), tell the user they need **two builds**:
   - First: `Flow=RELEASE` to build, bake AMI, and Smart Share it
   - Second: `Flow=PRODUCTION` with `BAKED_AMI_ID=<ami-id>` from step 1
4. Present this two-stage flow and confirm before proceeding.

### Step 6: Present parameters and confirm

Present all resolved parameters, service name, branch, and what the build
will do. Ask the user to confirm before proceeding.

### Step 7: Trigger and report

After confirmation, trigger the build and provide the Jenkins URL for monitoring.

---

## Tearing down deployments

To tear down an EC2 deployment, delete its CloudFormation stack using the
AWS CLI. You need credentials for the target AWS account.

### EC2 stack naming convention

Stack names are generated by `BlueGreenDeploy.buildStackName()` in
`cop-pipeline-step`. The formula is:

```
{teamPrefix}-{appName}-{sanitizedBranch}-{cloudEnvironment}-v{NNN}
```

- `teamPrefix`: from `parameterMap.teamPrefix` (e.g. `search`)
- `appName`: from `parameterMap.appName`
- `sanitizedBranch`: branch name with special chars (`/`, `^`, `+`, `.`,
  `\\`) stripped. For tag-based builds (`main`/`master`), the branch
  segment is omitted: `{teamPrefix}-{appName}-{cloudEnvironment}-v{NNN}`
- `cloudEnvironment`: from the deploy environment config (e.g. `test`, `prod`)
- `v{NNN}`: version suffix incremented per deploy (e.g. `v001`, `v002`)
- If `deploy.cloudformationStackName` is set, it overrides the entire name
- Truncated to 128 characters max

**Examples:**

| Branch | Stack name |
|--------|-----------|
| `main` | `search-myapp-prod-v001` |
| `feature/FOO-123` | `search-myapp-featureFOO-123-prod-v001` |

**Find the exact stack name** from the Jenkins console output:

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action console --service <name> --branch <branch> --build <N> \
  | grep 'Creating a new stack\|cfnUpdate.*stack'
```

### Delete the stack

```bash
aws cloudformation delete-stack \
  --stack-name <full-stack-name> \
  --region <region>
```

Monitor deletion:

```bash
aws cloudformation wait stack-delete-complete \
  --stack-name <full-stack-name> \
  --region <region>
```

The user must be authenticated to the correct AWS account before running
these commands. If they aren't, remind them to assume the appropriate role.

**Common account/region pairs (from profiles):**

| Environment | Account | Region |
|-------------|---------|--------|
| test (commerce) | `233367263614` | `us-east-1` |
| testSearchWaffle | `554036784086` | `us-east-1` |
| prod (commerce) | `538734628834` | `us-east-1` |
| prodSearchWaffle | `832844619813` | `us-east-1` |
| prodWest (commerce) | `538734628834` | `us-west-2` |
| prodSearchWaffleWest | `832844619813` | `us-west-2` |

---

## Pipeline configuration repos

All repos live under the `nike-cop-pipeline` GitHub org:

| Repo | GitHub URL | Purpose |
|------|-----------|---------|
| `cop-pipeline-configuration` | `https://github.com/nike-cop-pipeline/cop-pipeline-configuration` | Team profiles, deploy env defaults (branch per team) |
| `cicd-pipeline` | `https://github.com/nike-cop-pipeline/cicd-pipeline` | Pipeline functions (`ec2BlueGreenDeployPipeline`, etc.) and `PipelineProperties.createProperties()` |
| `cop-pipeline-step` | `https://github.com/nike-cop-pipeline/cop-pipeline-step` | Reusable atomic pipeline step implementations (`BlueGreenDeploy`, `Qma`, etc.) |
| `cop-pipeline-bootstrap` | `https://github.com/nike-cop-pipeline/cop-pipeline-bootstrap` | Loads pipeline libs; `loadPipelines()` / `loadSharedConfiguration()` |

### How team configuration works

The `cop-pipeline-configuration` repo uses **branches** to isolate team configs.
Each Jenkinsfile declares its config branch in the `@Library` annotation:

```groovy
@Library(['cop-pipeline-bootstrap','cop-pipeline-configuration@searchPipelinev1']) _
```

The branch name after `@` (e.g. `searchPipelinev1`) determines which set of
groovy profiles are available. Team-specific profiles live under
`resources/team/<teamname>/` in that branch.

For Search Engineering, the config branch is `searchPipelinev1` and profiles
are at `resources/team/search/*.groovy`. Key profiles:

| Profile | Purpose |
|---------|---------|
| `common.groovy` | Shared tags, cost center, email for all Search services |
| `gradle-java.groovy` | Java build config (Gradle image, build commands) |
| `jdk21-otel-dt.groovy` | JDK 21 package requirements (OpenJDK 21, OTEL, Splunk) |
| `double-alb-search-waffle-deploy.groovy` | EC2 deploy config for waffle environments (test/prod) with dual ALB support |
| `ec2-waffle-deploy.groovy` | Single-ALB EC2 waffle deploy |
| `lambda-deploy-waffle.groovy` | Lambda deploy config for waffle |

The deploy profiles define `userData` maps per environment. The key field for
Spring Boot apps is **`ENV_OPTS`**, which passes JVM args including
`-Dspring.profiles.active=<profiles>`. Jenkinsfiles can override `userData`
per deployment environment via `mergeConfiguration()`:

```groovy
testSearchWaffle: [
    deploy: [
        userData: [
            ENV_OPTS: "-Dspring.profiles.active=test,myprofile"
        ]
    ]
]
```

### Cloning pipeline repos

Clone to `/tmp/<repo-name>` by default. **When the user is working on
Jenkinsfile changes or pipeline configuration**, proactively offer to clone
relevant repos:

> "I'll need the cop-pipeline source to verify the configuration. OK to clone
> these to `/tmp/`?"

Use the `github` skill's `gh repo clone` pattern to clone from the
`nike-cop-pipeline` org. For the configuration repo, pass the team's branch:

| Repo | Clone target | Branch |
|------|-------------|--------|
| `cop-pipeline-configuration` | `/tmp/cop-pipeline-configuration` | `searchPipelinev1` (Search team) |
| `cicd-pipeline` | `/tmp/cicd-pipeline` | default |
| `cop-pipeline-step` | `/tmp/cop-pipeline-step` | default |
| `cop-pipeline-bootstrap` | `/tmp/cop-pipeline-bootstrap` | default (rarely needed) |

Pass `-- --branch <branch>` after the clone target to check out a specific
branch. Reuse existing clones if already present. If on the wrong branch:
`git fetch origin <branch> && git checkout <branch>`.

---

## Creating a new multibranch pipeline

Use the `get-config` action to fetch an existing job's XML as a template, modify
it for the new service, then use `create-job` to create it.

### Get an existing job's config as a template

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action get-config --service envoy > /tmp/template.xml
```

### Create a new job from XML

```bash
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action create-job --instance productfeed \
  --job-name mynewservice --config-file /tmp/mynewservice.xml

# Create under a folder (e.g. google, .net/lambda):
python3 "${SKILL_DIR}/scripts/jenkins_api.py" \
  --action create-job --instance searchscience \
  --folder google --job-name mynewservice --config-file /tmp/mynewservice.xml
```

### Agent workflow for creating pipelines

When the user asks to create a new multibranch pipeline:

1. Ask which existing job to use as a template (or pick the most similar one)
2. Fetch its config with `get-config`
3. Modify the XML:
   - Update `<repository>` to the new GitHub repo name
   - Update `<repositoryUrl>` accordingly
   - Update `<description>` if provided
   - Generate a new UUID for the `<id>` field
   - Keep credentials, branch discovery traits, and other settings from the template
4. Present the key differences to the user for confirmation
5. Create the job with `create-job`
6. Report the new job URL

---

## Arguments reference

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--action` | Yes | -- | `list`, `status`, `build`, `console`, `history`, `artifact`, `get-config`, `create-job` |
| `--service` | For most | -- | Job name or search term -- the script discovers it across all instances (use `--instance` to speed up search) |
| `--instance` | For list/create/job-path; optional hint for others | -- | `productfeed`, `searchscience`, `smartsearch`. Also speeds up `--service` discovery when provided |
| `--branch` | No | `main` | Branch name -- use the raw name (e.g. `feature/foo`); the script URL-encodes it automatically. Falls back to `master` if `main` not found |
| `--build` | No | `lastBuild` | Build number for console action |
| `--count` | No | `10` | Number of builds for history action |
| `--job-path` | No | -- | Raw job path (alternative to `--service` for get-config) |
| `--job-name` | For create | -- | Name for the new job |
| `--config-file` | No | stdin | Path to XML config file for create-job |
| `--folder` | No | -- | Parent folder path for create-job (e.g. `google` or `.net/lambda`) |
| `--artifact-path` | No | -- | Relative path to artifact file (for artifact action; omit to list all artifacts). Defaults to `lastSuccessfulBuild` when `--build` is not set |
| `--params` | No | -- | Comma-separated KEY=VALUE pairs for parameterized builds (uses `buildWithParameters`) |

## Output formats

| Action | Format |
|--------|--------|
| `list`, `status`, `build`, `history` | JSON to stdout |
| `console` | Plain text (raw Jenkins console log) |
| `artifact` | Raw artifact content (text/JSON), or JSON list when `--artifact-path` is omitted |
| `get-config` | XML (Jenkins job configuration) |
| `create-job` | JSON to stdout |
