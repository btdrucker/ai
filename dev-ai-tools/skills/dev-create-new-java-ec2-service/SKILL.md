---
name: dev-create-new-java-ec2-service
description: >
  Create and deploy a new Java 21 Spring Boot EC2 service from the blueprint.
  Use when the user wants to create a new service, bootstrap a repo, scaffold
  a Java microservice, set up a new EC2-deployed Spring Boot application, or
  deploy a skeleton service to the Test waffle environment.
---

# Create New Java EC2 Service

## Related skills

- **`github`** -- GitHub operations for repo creation, PR workflows
- **`sdkman`** -- JDK version management (Java 21 setup for the new service)
- **`vscode-workspace`** -- workspace management (adding the new repo to the active workspace)

Bootstraps a new Java 21 / Spring Boot 3.x service from `discover.service.blueprint-java-springboot-mvc`, applies all required customizations for the Search team CI/CD pipeline (Jenkins + Vulcan + FAMI 4.0), deploys CloudFormation infrastructure, and brings the service up healthy in the Test waffle environment.

**Known working references:**
- `search.service.productcatalogeventcomposerv1`
- `search.service.wholesaleeventscomposerv1`

---

## Step 0: Reference Project Discovery (optional)

Ask the user: "Do you have an existing deployed service I should use as a reference for infrastructure config (Jenkinsfile, CF templates, security groups, IAM policies)? If so, which one?"

### If a reference project is provided

Clone or locate the reference repo and read the following files:
1. `Jenkinsfile` -- extract security groups, instance types, profiles, SignalFx config
2. `cloudformation/service-role-waffle.yaml` -- extract managed policy list
3. `cloudformation/*-test-loadbalancer.yaml` -- extract ALB listener ARN, VPC stack name, email, account mappings
4. `settings.gradle` -- verify Vulcan guard and Artifactory URLs
5. `build.gradle` -- note Spring Boot version, plugins, Gradle wrapper version

Present the extracted values to the user for confirmation (see Inputs table below).

### If no reference project is provided

Use the defaults listed in the "Derived values" table below. Present them to the user for confirmation -- the user must explicitly confirm or override each value since there is no reference to verify against.

---

## Inputs (gather from user before starting)

### Required (no defaults)

| Input | Example | Notes |
|-------|---------|-------|
| Service name | `productcatalogeventcomposerv1` | Used in repo name, IAM role, CF stacks |
| Jira ticket | `SAD-4074` | For branch naming |
| ALB path | `/search/product_catalog/v1` | Must be unique on the ALB |
| ALB priority | `1980` | Must not conflict; query existing rules |
| CODEOWNERS team | `@nike-internal/search-meili` | GitHub team handle |

### Derived values (from reference project if provided, otherwise use defaults)

**Full defaults table and reference extraction procedure:** see [REFERENCE.md](REFERENCE.md#reference-project-extraction-procedure).

Key derived values include: team prefix, AWS account IDs, ALB listener ARN, VPC stack name, security groups, IAM managed policies, FAMI version/architecture, instance types, pipeline profiles, SignalFx config, Spring Boot/Gradle versions, and Splunk index.

**USER GATE:** Present all derived values as a table and ask the user to confirm or override each before proceeding.

---

## Phase 1: Repository & Blueprint Setup

### 1. Create GitHub repo

```bash
gh repo create nike-internal/search.service.<serviceName> --private --clone
cd search.service.<serviceName>
```

### 2. Copy blueprint files (without its git history)

```bash
# Clone blueprint to a temp location, discard its .git
gh repo clone nike-internal/discover.service.blueprint-java-springboot-mvc /tmp/blueprint -- --depth 1
rm -rf /tmp/blueprint/.git
cp -a /tmp/blueprint/. .
```

### 3. Run placeholder replacement (what init.groovy does, minus the git steps)

The blueprint uses these placeholders in file names, directory names, and file contents:

| Placeholder | Replace with | Example |
|-------------|--------------|---------|
| `_app_` | service name (no version suffix) | `productcatalogeventcomposer` |
| `_appversion_` | version suffix | `v1` |
| `_nikedomain_` | domain name | `search` |
| `_githuborg_` | GitHub org | `nike-internal` |
| `_mainbranch_` | main branch name | `main` |

Execute the replacements:

```bash
SERVICE_NAME="<serviceName without version>"  # e.g., "productcatalogeventcomposer"
VERSION="v1"
DOMAIN="search"
ORG="nike-internal"
BRANCH="main"

# Rename directories containing placeholders
find . -path ./build -prune -o -name "*_app_*" -type d -depth -exec bash -c \
  'mv -f "$1" "${1/_app_/'"$SERVICE_NAME"'}"' -- {} \;

# Rename files containing placeholders
find . -path ./build -prune -o -name "*_app_*" -type f -exec bash -c \
  'mv "$1" "${1/_app_/'"$SERVICE_NAME"'}"' -- {} \;
find . -path ./build -prune -o -name "*_nikedomain_*" -type f -exec bash -c \
  'mv "$1" "${1/_nikedomain_/'"$DOMAIN"'}"' -- {} \;

# Replace placeholders in file contents
find . -not -path '*/\.*' -not -path './build/*' -type f -exec \
  perl -p -i -e "s/_app_/$SERVICE_NAME/g" {} +
find . -not -path '*/\.*' -not -path './build/*' -type f -exec \
  perl -p -i -e "s/_nikedomain_/$DOMAIN/g" {} +
find . -not -path '*/\.*' -not -path './build/*' -type f -exec \
  perl -p -i -e "s/_appversion_/$VERSION/g" {} +
find . -not -path '*/\.*' -not -path './build/*' -type f -exec \
  perl -p -i -e "s/_githuborg_/$ORG/g" {} +
find . -not -path '*/\.*' -not -path './build/*' -type f -exec \
  perl -p -i -e "s/_mainbranch_/$BRANCH/g" {} +
```

### 4. Clean up template-only files

```bash
rm -f init.groovy
rm -rf .github
rm -f README.md README_ARCHITECTURE.md
mv README_SERVICE.md README.md
```

### 5. Commit and push as initial commit

```bash
git add -A
git commit -m "Initial commit from blueprint"
git push -u origin main
```

### 6. Create feature branch

```bash
git checkout -b feature/<ticket>-bootstrap-<serviceName>
```

**USER GATE:** Confirm the repo was created successfully and the initial commit looks correct before proceeding to code customization.

---

## Phase 2: Code Customization

Apply all of the following changes. Each is required for successful deployment.

### Version verification

If a reference project was provided, read its `build.gradle` to extract:
- Spring Boot plugin version (e.g., `3.5.5`)
- Gradle wrapper version
- Plugin versions (spotbugs, pitest, etc.)

If no reference, use the defaults from REFERENCE.md. Either way, **confirm with user** before proceeding.

### Package rename (if target package differs from blueprint domain)
- Phase 1 already replaced `_nikedomain_` with the domain value (e.g., `search`), so after Phase 1 the package is `com.nike.<domain>`
- If the confirmed target package matches (e.g., `com.nike.search` and domain was `search`), no rename is needed
- If it differs, rename `com.nike.<domain>` -> `<confirmed target package>` in all source files and directories

### Application.java
- Ensure main method is `public static void main(String[] args)` (not package-private)
- Wrap any comments exceeding 120 chars (Checkstyle limit)

### build.gradle (critical deployment fixes)

Apply the JAR config, bootJar config, processResources filter, and Java 21 toolchain. **Full templates:** see [REFERENCE.md](REFERENCE.md#buildgradle-key-sections).

- Set Java toolchain to 21: `languageVersion = JavaLanguageVersion.of(21)`

### settings.gradle (Vulcan compatibility)

Wrap `dependencyResolutionManagement` in a `GradleVersion >= 6.8` guard and add `pluginManagement` for Nike Artifactory. **Full template:** see [REFERENCE.md](REFERENCE.md#settingsgradle-vulcan-compatible-universal).

### Log4j2 version token
- In `log4j2.xml` and `log4j2-npe.xml`: replace `${sys:releaseVersion:-unknown}` with `@releaseVersion@`

### application.yaml
- Set `info.app.domain` to `<confirmed Nike domain>` (from Step 0)
- Replace `${releaseVersion:unknown}` with `@releaseVersion@` (both `info.app.version` and `management.metrics.tags.app_version`)
- Set `management.otlp.metrics.export.enabled: false` (disabled for EC2/waffle; FAMI handles OTEL export. Profile-specific yamls can re-enable for NPE environments)

### Controller path
- Update `@RequestMapping` to match the ALB path (e.g., `search/product_catalog/v1`)
- Update integration test paths to match

### Code quality
- Update `gradle/code-quality.gradle` Pitest `targetClasses` to `<target package>.<subpackage>.*`

### Remove NPE/container artifacts (not needed for EC2)

The blueprint includes files for NPE (Kubernetes) deployments. Remove them entirely:

```bash
rm -f Dockerfile JenkinsfileNPE
rm -f npe_component_*.yaml
rm -f src/main/resources/log4j2-npe.xml
```

Also remove `management.otlp.metrics.export` from `application.yaml` and any profile-specific OTLP overrides (`application-test.yaml`, `application-prod.yaml`). On EC2 with FAMI 4.0, the OTel Java agent and `nike-splunk-otel-collector` handle all metric/trace export -- no app-level OTLP config is needed.

### Remove layer-specific blueprint READMEs

The blueprint generates boilerplate README.md files inside each package directory (domain/, application/, adapter/, infrastructure/). Remove them and write a single comprehensive README.md at the project root instead.

### Write project README

Replace the blueprint's placeholder README with a comprehensive one covering:
- Service purpose and business context (link to Jira epic and ADR)
- Architecture (clean architecture layers)
- Project structure
- Build and run instructions
- Deployment (Jenkins parameters, environments)
- Infrastructure (CF stacks)
- Observability (Splunk, SignalFx)
- Endpoints
- Current status

### Fix remaining discover -> search references

The blueprint uses "discover" as the default domain. After Phase 1 placeholder replacement, check for and fix any remaining "discover" references in:
- `quality-config.yaml` (domain, owner, team, email, organization)
- `api.yaml` (contact name, email)
- Any README files in source directories

### Other files
- `CODEOWNERS`: set to the team handle (confirmed in Step 0)
- `.sdkmanrc`: `java=21.0.11-amzn`
- Add `.sdkmanrc` to `.gitignore`

### Verify locally
```bash
./gradlew clean build -x integrationTest
./gradlew bootRun
# Confirm: localhost:8080/<path>/about returns JSON, localhost:8077/health returns UP
```

> **KNOWN ISSUE -- Vulcan plain JAR:** If `jar { enabled = false }` is missing, the deployed instance will fail with `no main manifest attribute, in /usr/local/springboot/app.jar`. The OTEL agent loads but Java exits immediately.

---

## Phase 3: Infrastructure (CloudFormation)

### Infrastructure verification

If a reference project was provided, read its CF templates to extract:
- **Managed policies** from `service-role-waffle.yaml`
- **ALB listener ARN** from `*-test-loadbalancer.yaml`
- **VPC stack name** (usually `akamai-facing-vpc-stack`)
- **Account ID mappings** (test/prod)
- **Email tag** value
- **Any service-specific IAM policies** (SQS, DynamoDB, etc.)

If no reference, use the defaults from REFERENCE.md.

**USER GATE:** Present the IAM policies and ALB config (from reference or defaults). Ask:
- "Are these managed policies correct for your new service, or do you need to add/remove any?"
- "Does your service need any additional IAM policies (SQS, DynamoDB, S3, etc.)?"
- "Is the ALB listener ARN correct? (This determines which load balancer your service sits behind)"

### Create templates in `cloudformation/`:

### IAM role (`service-role-waffle.yaml`)
- Role name: `iamr-<teamPrefix>-app-<serviceName>`
- Managed policies: use confirmed list from reference verification above
- Instance profile with same name

### Test ALB (`search-<serviceName>-test-loadbalancer.yaml`)
- Listener rule on confirmed ALB (ARN from reference verification)
- Path pattern: `/<albPath>*`
- Target group: name max 32 chars, port 8080, health check on port 8077 at `/health`
- Priority: must be unique (query existing rules first)
- Tags: use confirmed department/domain/email values

### Prod ALB (placeholder)
- Same structure, different account mappings -- leave as placeholder

### Deploy stacks

```bash
# IAM role (may need elevated permissions -- create change set if needed)
aws cloudformation create-stack --stack-name <teamPrefix>-<serviceName>-service-role \
  --template-body file://cloudformation/service-role-waffle.yaml \
  --capabilities CAPABILITY_NAMED_IAM --region us-east-1

# ALB listener rule + target group
aws cloudformation create-stack --stack-name <teamPrefix>-<serviceName>-loadbalancer \
  --template-body file://cloudformation/search-<serviceName>-test-loadbalancer.yaml \
  --region us-east-1
```

After ALB stack deploys, capture the target group ARN for the Jenkinsfile:
```bash
aws cloudformation describe-stacks --stack-name <teamPrefix>-<serviceName>-loadbalancer \
  --query "Stacks[0].Outputs" --region us-east-1
```

**USER GATE:** Confirm CF stack names and parameters before deploying.

> **KNOWN ISSUE -- IAM permissions:** If deploying the IAM stack fails with `iam:CreateRole` denied, create a change set and have someone with elevated permissions execute it.

---

## Phase 4: Jenkins Pipeline

### Pipeline verification

If a reference project was provided, read its `Jenkinsfile` and extract:
- **Pipeline profiles** (common, java, jdk, waffle, canary)
- **Security groups** for `testSearchWaffle` and `prodSearchWaffle`
- **Instance types** (test and prod)
- **Instance sizing** (min/max/desired for each environment)
- **FAMI bake config** (quarter, architecture)
- **SignalFx detector thresholds**
- **Pipeline library version** (e.g., `searchPipelinev1`)

If no reference, use the defaults from REFERENCE.md.

**USER GATE:** Present all values (from reference or defaults) as a table. Ask:
- "Are these security groups correct for your new service, or does it need additional ones (e.g., Redis, Kafka, specific DB)?"
- "Are the instance types and sizing appropriate, or does your service have different resource requirements?"
- "Is FAMI 4.0 ARM64 correct? (This determines the AMI base and instance family)"
- "Are the pipeline profiles correct, or does your service use different ones?"

### Jenkinsfile

Use the template in REFERENCE.md. Key fields to fill:
- `appName`: service name
- `iamRoleName`: `iamr-<teamPrefix>-app-<serviceName>`
- `testWaffleLoadBalancerTargetGroupArn`: from Phase 3 output
- Security groups: use confirmed SGs from reference verification above
- Instance types: use confirmed types
- Profiles: use confirmed profile list

### Jenkins job
- **Manual step:** Create the Jenkins pipeline job in BMX Jenkins
- Ask user: "Which Jenkins folder should this job live in?" (reference project may be in "google", "search", or another folder)
- Copy configuration from the reference project's Jenkins job
- Point to the new repo and branch

### Triggering a deploy

Build parameters for Test deployment:
- **RELEASE_TYPE:** `TEST_DEPLOY_ONLY`
- **DEPLOY_ENVIRONMENT:** `testSearchWaffle`

A plain build (push without parameters) only runs compile/test/quality -- it will NOT bake an AMI or deploy.

> **KNOWN ISSUE -- Rebuild vs Build:** "Rebuild" reuses the Jenkins workspace and may pick up stale JARs. Always use a fresh "Build with Parameters" for deployments.

---

## Phase 5: Deploy & Verify

1. Trigger Jenkins build with `TEST_DEPLOY_ONLY` / `testSearchWaffle`
2. Monitor pipeline: Build -> Quality -> AMI Bake -> Deploy -> ASG Health Check
3. Once ASG reports healthy, verify:

```bash
# Health (management port)
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["curl -s http://localhost:8077/health"]'

# About (app port)
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["curl -s http://localhost:8080/<albPath>/about"]'
```

4. Check Splunk: `index=np-app app=<serviceName>`
5. Confirm `version=` field shows build number (not `unknown`)

> **KNOWN ISSUE -- ASG stuck:** If the pipeline loops on "0 instances in TG reported healthy", check instance logs via SSM. Common causes: (1) missing `jar { enabled = false }`, (2) app crash on startup (check `/var/log/nike/springboot/springboot.log`), (3) `fc_nike-ec2-config.service` failed (missing SFX token).

---

## Phase 6: External Service Registration

### SignalFx tokens (required for APM/tracing)

**Ask the user to confirm** the following values before requesting tokens:

| Field | Default (from reference) | Confirm? |
|-------|--------------------------|----------|
| org | `Commerce` | Yes |
| aws accounts | `<confirmed test account ID>` | Yes |
| app groups | `Recommend` | Yes -- may differ by team |
| apps | `<serviceName>` | Auto |
| team distribution list | `<confirmed team email>` | Yes |

Request BOTH tokens via **#cop-signalfx** Slack channel:

1. **API token:** with confirmed org, account, app group, app name, token type: API
2. **TRACING token:** same fields but token type: TRACING

Provide the user with the exact message to paste into #cop-signalfx:
```
Please provision tokens for:
- org: <confirmed org>
- aws accounts: <confirmed account ID>
- app groups: <confirmed app group>
- apps: <serviceName>
- token type: API
- team distribution list: <confirmed email>

And a second request with token type: TRACING (same fields otherwise).
```

Without both tokens, `fc_nike-ec2-config.service` fails on boot and no traces are exported.

### After tokens are provisioned

Trigger an instance refresh or new deploy. The new instance will pick up the tokens on boot. Verify:
- `systemctl status fc_nike-ec2-config.service` shows `active (exited)`
- Traces appear in SignalFx APM after hitting the service endpoint

### Scan@Source

Automatic -- may take a few builds before it registers the new repo. Not a deployment blocker.

---

## Completion Checklist

- [ ] Repo created and branch pushed
- [ ] Local build passes
- [ ] IAM and ALB CF stacks deployed
- [ ] Jenkins job created and build triggered with correct parameters
- [ ] Service healthy on ALB (target group green)
- [ ] Splunk logs flowing with correct version
- [ ] SignalFx tokens provisioned and `fc_nike-ec2-config` succeeds
- [ ] PR created with full summary of blueprint deltas
