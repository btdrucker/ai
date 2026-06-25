# Reference Templates

Templates and patterns for creating a new Java EC2 service. Replace all `{{placeholder}}` values with actual service-specific values.

## Value Source Legend

Each placeholder and hardcoded value in these templates originates from one of three sources:

| Tag | Meaning | Action |
|-----|---------|--------|
| **[USER]** | Must be provided by the user | Ask directly |
| **[REF]** | Extracted from reference project, or use default if no reference | If reference provided: read + confirm. If no reference: present default + confirm. |
| **[UNIVERSAL]** | Fixed/standard across all search services | Use as-is (no confirmation needed) |

---

## Jenkinsfile Template

```groovy
#!groovy
@Library(['cop-pipeline-bootstrap','cop-pipeline-configuration@searchPipelinev1']) _
loadPipelines()

def parameterMap = [
        appName : "{{appName}}",
        iamRoleName : "iamr-{{teamPrefix}}-app-{{appName}}",
        teamName: "{{teamName}}",
        teamPrefix: "{{teamPrefix}}",
        version: '${project.version}',

        prodInstanceType: 'm7g.large',
        prodWaffleDesiredInstanceSize:  1,
        prodWaffleMinInstanceSize: 1,
        prodWaffleMaxInstanceSize: 1,

        testInstanceType: 'm7g.large',
        testDesiredInstanceSize:  1,
        testMinInstanceSize: 1,
        testMaxInstanceSize: 1,

        testWaffleLoadBalancerTargetGroupArn: '{{testTargetGroupArn}}',

        signalfx: [
                detectorType: 'sl1',
                minTrafficThreshold: '0',
                responseP95: '100',
                response400Percent: '20',
                response500Percent: '20',
                minEC2HostCount: '1',
        ]
]

def config = [
    profile: [
        common: "team/search/common.groovy",
        java  : "team/search/gradle-java.groovy",
        jdk21 : "team/search/jdk21-otel-dt.groovy",
        waffle: "team/search/double-alb-search-waffle-deploy.groovy",
        debug : "true",
        canary: "team/search/canary-waffle-prod-enabled.groovy"
    ],
    bake: [
            mavenMetadataUrl: '',
            amiSelection: ['osversion': '', 'quarter': '4.0', 'weeksback': '', 'architecture': 'arm64']
    ],
    deploymentEnvironment: [
                        prodWest: [
                                "deployFlow": [
                                        PRODUCTION: [],
                                        RELEASE: []
                                ]
                        ],
                        test: [
                                "deployFlow": [
                                        PRODUCTION: [],
                                        RELEASE: []
                                ]
                        ],
                        prod: [
                                "deployFlow": [
                                        PRODUCTION: [],
                                        RELEASE: []
                                ]
                        ],
                        testSearchWaffle: [
                                deploy: [
                                  securityGroups: [
                                      'sg-0b7f2cfe419ac7fe6', // core-internal-alb-security-group
                                      'sg-04282f8a02b76b54c', // search-test-sg-app-int
                                      'sg-0cd67d18f543c3b6c', // core-test-sg-app-internalApp
                                      {{additionalSecurityGroups}}
                                  ]
                                ]
                        ],
                        prodSearchWaffle: [
                                    deploy: [
                                       securityGroups: [
                                          'sg-0191862adbf9639fb', // core-test-sg-app-internal
                                          'sg-07ea2e5bb92a54b39', // core-test-sg-app-internalApp
                                          'sg-0f4f1184a62a4e438'  // search-test-sg-app-int
                                       ]
                                    ]
                       ],
                       prodSearchWaffleWest: [
                               deploy: [
                                   desiredCapacity: 1,
                                   maxSize: 3,
                                   minSize: 1,
                               ]
                       ]
    ]
]

node {
    config = mergeConfiguration(config, parameterMap)
}

ec2BlueGreenDeployPipeline(
    config
)
```

### Placeholder reference

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{{appName}}` | **[USER]** | `productcatalogeventcomposerv1` |
| `{{teamName}}` | **[REF]** | `Search` |
| `{{teamPrefix}}` | **[REF]** | `search` |
| `{{testTargetGroupArn}}` | Phase 3 CF output | `arn:aws:elasticloadbalancing:us-east-1:554036784086:targetgroup/...` |
| `{{additionalSecurityGroups}}` | **[USER]** -- service-specific SGs (optional) | `'sg-04f76ef6717d1a318', // redis-client` |

### Values to verify from reference project

| Value in template | Source | Notes |
|-------------------|--------|-------|
| `teamName: "Search"` | **[REF]** | Confirm with user |
| `teamPrefix: "search"` | **[REF]** | Confirm with user |
| `prodInstanceType: 'm7g.large'` | **[REF]** | Confirm -- may differ for prod |
| `testInstanceType: 'm7g.large'` | **[REF]** | Confirm -- match FAMI architecture |
| Instance sizing (all `1`) | **[REF]** | Confirm for prod; skeleton uses 1 |
| Security groups (testSearchWaffle) | **[REF]** | Read from ref Jenkinsfile, confirm |
| Security groups (prodSearchWaffle) | **[REF]** | Read from ref Jenkinsfile, confirm |
| Pipeline profiles (common, java, jdk21, waffle, canary) | **[REF]** | Read from ref, confirm |
| `amiSelection quarter: '4.0'` | **[REF]** | FAMI version -- confirm |
| `amiSelection architecture: 'arm64'` | **[REF]** | Confirm |
| SignalFx thresholds | **[REF]** | Reasonable defaults; confirm |
| `@Library` version (`searchPipelinev1`) | **[REF]** | Confirm pipeline library |
| `cop-pipeline-bootstrap` | **[UNIVERSAL]** | Standard bootstrap library |
| `ec2BlueGreenDeployPipeline` | **[UNIVERSAL]** | Standard deploy pipeline |
| `version: '${project.version}'` | **[UNIVERSAL]** | Gradle version injection |

### Build parameters for Test deployment [UNIVERSAL]

| Parameter | Value |
|-----------|-------|
| RELEASE_TYPE | `TEST_DEPLOY_ONLY` |
| DEPLOY_ENVIRONMENT | `testSearchWaffle` |

---

## CloudFormation: IAM Role (`service-role-waffle.yaml`)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: >
  IAM role and instance profile for {{appName}} EC2 service
Resources:
  IAMRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: iamr-{{teamPrefix}}-app-{{appName}}
      ManagedPolicyArns:
        - !Sub "arn:aws:iam::${AWS::AccountId}:policy/iamr-search-team-ManagedServiceRolePolicyS3V5-jwt"
        - !Sub "arn:aws:iam::${AWS::AccountId}:policy/iamr-search-team-ManagedServiceRolePolicyS3V5-app"
        - !Sub "arn:aws:iam::${AWS::AccountId}:policy/iamr-search-team-ManagedServiceRolePolicyElasticSearchV8-search"
        - !Sub "arn:aws:iam::${AWS::AccountId}:policy/Nike-Cerberus-Allow-AssumeRole"
        - !Sub 'arn:aws:iam::${AWS::AccountId}:policy/idnSSMPolicy'
        - !Sub "arn:aws:iam::${AWS::AccountId}:policy/iamr-search-team-ManagedServiceRolePolicySSMConsole-search"
        - !Sub "arn:aws:iam::${AWS::AccountId}:policy/iamr-search-team-ManagedServiceRolePolicyOscarTokenGenerationV1-search"
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      Path: "/"
      Tags:
        - Key: 'nike-application'
          Value: '{{appName}}'
        - Key: 'nike-department'
          Value: 'Search and Recommendations'
        - Key: 'nike-domain'
          Value: 'Search'
  OscarTagResourcesPolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: oscar-tag-resources-policy
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action:
              - tag:GetResources
            Resource: "*"
      Roles:
        - Ref: IAMRole
  ServiceInstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      Path: "/"
      InstanceProfileName: iamr-{{teamPrefix}}-app-{{appName}}
      Roles:
        - Ref: IAMRole
```

### Values to verify from reference project

| Value in template | Source | Notes |
|-------------------|--------|-------|
| Managed policy list (7 policies) | **[REF]** | Read from ref CF, confirm with user -- may need additions/removals |
| `nike-department` tag | **[REF]** | Confirm (e.g., "Search and Recommendations") |
| `nike-domain` tag | **[REF]** | Confirm (e.g., "Search") |
| Role naming pattern `iamr-search-app-*` | **[REF]** | Confirm prefix matches team convention |
| `AssumeRolePolicyDocument` (ec2 only) | **[UNIVERSAL]** | Standard EC2 assume-role |
| `OscarTagResourcesPolicy` | **[UNIVERSAL]** | Required for all services |

### Additional IAM policies

Ask the user: "Does your service need any additional IAM policies beyond the base set (SQS, DynamoDB, S3, Kinesis, etc.)?" Add service-specific policies below `ServiceInstanceProfile` as needed. Pattern:

```yaml
  CustomPolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: {{appName}}-custom-policy
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action:
              - <service>:<action>
            Resource:
              - !Sub "arn:${AWS::Partition}:<service>:*:${AWS::AccountId}:<resource>"
      Roles:
        - Ref: IAMRole
```

---

## CloudFormation: Test ALB (`search-{{appName}}-test-loadbalancer.yaml`)

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: >
  Search {{appName}} target group and listener rule. Stack name: search-{{appName}}-loadbalancer
Parameters:
  Name:
    Type: String
    Default: 'search-{{appName}}-targetgroup'
    Description: 'Name tag value (shows up in the AWS console)'
  Email:
    Type: String
    Default: 'Lst-Digitaltech.core.search@nike.com'
    Description: 'Email value for tags'
  NikeApplication:
    Type: String
    Default: 'search-{{appName}}'
    Description: 'Nike Tagging Policy'
  NikeDepartment:
    Type: String
    Default: 'Search and Recommendations'
    Description: 'Nike Tagging Policy'
  NikeDomain:
    Type: String
    Default: 'Search'
    Description: 'Nike Tagging Policy'
  LoadBalancerListenerARN:
    Type: String
    Description: ALB listener ARN for apps-core-internal-alb
    Default: 'arn:aws:elasticloadbalancing:us-east-1:554036784086:listener/app/apps-core-internal-alb/f6b0ee56a43c2d9d/f9744eecaa215739'
  VpcStackName:
    Type: String
    Description: VPC stack name
    Default: 'akamai-facing-vpc-stack'

Mappings:
  '554036784086':
    Env:
      Name: test
  '832844619813':
    Env:
      Name: prod

Resources:

  ListenerRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn: !Ref LoadBalancerListenerARN
      Priority: {{priority}}
      Conditions:
        - Field: path-pattern
          PathPatternConfig:
            Values:
              - '{{albPath}}*'
      Actions:
        - TargetGroupArn: !Ref TargetGroup
          Type: forward

  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: '{{targetGroupName}}'
      Port: 8080
      Protocol: HTTP
      VpcId:
        Fn::ImportValue:
          !Sub "${VpcStackName}-VPCID"
      HealthCheckEnabled: true
      HealthCheckPath: /health
      HealthCheckPort: "8077"
      HealthCheckProtocol: "HTTP"
      HealthCheckIntervalSeconds: 30
      HealthyThresholdCount: 5
      UnhealthyThresholdCount: 5
      Matcher:
        HttpCode: 200-299
      TargetGroupAttributes:
        - Key: 'deregistration_delay.timeout_seconds'
          Value: '60'
      Tags:
        - Key: 'Name'
          Value: !Ref NikeApplication
        - Key: 'email'
          Value: !Ref Email
        - Key: 'nike-application'
          Value: !Ref NikeApplication
        - Key: 'nike-department'
          Value: !Ref NikeDepartment
        - Key: 'nike-domain'
          Value: !Ref NikeDomain
        - Key: 'nike-environment'
          Value: !FindInMap [!Ref 'AWS::AccountId', Env, Name]

Outputs:
  TargetGroupArn:
    Description: ARN of the target group (use in Jenkinsfile)
    Value: !Ref TargetGroup
    Export:
      Name: !Sub "${AWS::StackName}-TargetGroupArn"
```

### Placeholder reference

| Placeholder | Source | Constraints | Example |
|-------------|--------|-------------|---------|
| `{{priority}}` | **[USER]** | Unique integer on the ALB listener; query existing rules first | `1980` |
| `{{albPath}}` | **[USER]** | Starts with `/`, trailing `*` is added in template | `/search/product_catalog/v1` |
| `{{targetGroupName}}` | **[USER]** | Max 32 characters | `productcatalogeventcomposerv1` |

### Values to verify from reference project

| Value in template | Source | Notes |
|-------------------|--------|-------|
| `LoadBalancerListenerARN` default | **[REF]** | Read from ref CF, confirm -- this is the ALB |
| `VpcStackName` default | **[REF]** | Usually `akamai-facing-vpc-stack`; confirm |
| `Email` default | **[REF]** | Team DL; confirm |
| Account ID mappings (554036784086, 832844619813) | **[REF]** | Confirm test/prod account IDs |
| `NikeDepartment` default | **[REF]** | Confirm |
| `NikeDomain` default | **[REF]** | Confirm |
| Health check port `8077` | **[UNIVERSAL]** | Spring Boot management port |
| Health check path `/health` | **[UNIVERSAL]** | Actuator health endpoint |
| App port `8080` | **[UNIVERSAL]** | Spring Boot default |
| `deregistration_delay.timeout_seconds: 60` | **[UNIVERSAL]** | Standard for graceful shutdown |

---

## build.gradle Key Sections

All patterns below are **[UNIVERSAL]** -- they apply to every Java EC2 service regardless of reference project. The only values to verify from the reference are plugin versions (Spring Boot, spotbugs, pitest) and Gradle wrapper version.

### JAR configuration (required -- prevents Vulcan packaging the wrong artifact)

```gradle
jar {
    enabled = false
}

bootJar {
    dependsOn versionInfo
    getArchiveBaseName().set(artifactId)
    getArchiveVersion().set(releaseVersion as String)
    doNotTrackState("Disable incremental build to avoid MD5 hash issues")
    reproducibleFileOrder = true
    preserveFileTimestamps = false
}
```

### Build-time version token replacement

```gradle
processResources {
    dependsOn versionInfo
    def resolvedVersion = releaseVersion.toString()
    filesMatching(['application.yaml', 'application-*.yaml', 'log4j2*.xml']) {
        filter { line -> line.replace('@releaseVersion@', resolvedVersion) }
    }
}
```

### Java toolchain

```gradle
java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}
```

---

## settings.gradle (Vulcan-compatible) [UNIVERSAL]

The Vulcan version guard and Artifactory URLs are standard across all services. The only value that varies is `rootProject.name` which is set via `artifactId` in `gradle.properties`.

```gradle
import org.gradle.util.GradleVersion

pluginManagement {
    repositories {
        maven {
            url 'https://artifactory.nike.com/artifactory/java-development-virtual'
        }
    }
}

rootProject.name = artifactId

if (GradleVersion.current() >= GradleVersion.version("6.8")) {
    dependencyResolutionManagement {
        repositoriesMode.set(RepositoriesMode.PREFER_SETTINGS)
        repositories {
            maven {
                url 'https://artifactory.nike.com/artifactory/maven-virtual'
            }
            if (providers.gradleProperty("useMavenLocal").isPresent()) {
                mavenLocal()
            }
        }
    }
}
```

---

## Known Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Vulcan plain JAR | `no main manifest attribute, in app.jar` -- app exits immediately on EC2 | Add `jar { enabled = false }` in `build.gradle` |
| Version shows `unknown` | Splunk/about endpoint shows `version=unknown` | Use `@releaseVersion@` tokens + `processResources` filter |
| FAMI 4.0 OTEL agent conflict | App starts but no traces exported | FAMI 4.0 includes its own OTEL agent; do NOT bundle a separate one |
| Missing SignalFx tokens | `fc_nike-ec2-config.service` fails; no OTEL env vars set | Request both API + TRACING tokens via #cop-signalfx before first deploy |
| Cloud-init userdata | Instances launch but nothing runs | Ensure AMI bake completed and Vulcan produced the correct RPM |
| `OTLP_METRICS_EXPORT` without `NPE_HOST_IP` | App crashes on startup with connection refused | Set `management.otlp.metrics.export.enabled: false` in application.yaml |
| Target group name > 32 chars | CF stack creation fails | Shorten the target group name (abbreviate if needed) |
| Checkstyle line length | Build fails on long lines | Max 120 chars; wrap comments and imports |
| `settings.gradle` breaks Vulcan | Vulcan runs Gradle 4.10 internally which doesn't support `dependencyResolutionManagement` | Wrap in `GradleVersion >= 6.8` guard |
| NPE artifacts left in place | Dockerfile, JenkinsfileNPE, npe_component_*.yaml, log4j2-npe.xml clutter the repo | Remove all NPE files -- EC2 services don't use them |
| OTLP export config on EC2 | `NPE_HOST_IP` unresolvable; app may fail or silently drop metrics | Remove `management.otlp.metrics.export` section; FAMI collector handles export |
| Scan@Source 404 | Pipeline logs SCM error on first few builds | Automatic resolution -- SCM Data Refresh picks up the repo eventually |
| ASG health check timeout | Pipeline waits indefinitely for healthy instance | Check `/var/log/nike/springboot/springboot.log` via SSM for startup errors |

---

## Useful Commands

### Check existing ALB priorities [REF -- use confirmed ALB ARN]

```bash
aws elbv2 describe-rules \
  --listener-arn "{{confirmedAlbListenerArn}}" \
  --query "Rules[].Priority" --output text --region us-east-1
```

Use the ALB listener ARN confirmed with the user in Step 0. Default: `arn:aws:elasticloadbalancing:us-east-1:554036784086:listener/app/apps-core-internal-alb/f6b0ee56a43c2d9d/f9744eecaa215739`

### Verify instance health via SSM

```bash
INSTANCE_ID=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "{{appName}}-*" \
  --query "AutoScalingGroups[0].Instances[0].InstanceId" \
  --output text --region us-east-1)

aws ssm send-command --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["curl -s http://localhost:8077/health && echo && curl -s http://localhost:8080/{{albPathNoLeadingSlash}}/about"]' \
  --region us-east-1
```

### Splunk query [REF -- confirm index with user]

```
index={{splunkIndex}} app={{appName}} | head 20
```

Default `splunkIndex` is `np-app` (non-prod). Confirm with user.

---

## AWS Account Reference [REF -- confirm with user]

These are the known Search team accounts. Verify from the reference project's CF mappings.

| Account | ID | Usage |
|---------|-----|-------|
| Test Waffle | `554036784086` | Non-production testing |
| Prod Waffle | `832844619813` | Production |

## ALB Reference [REF -- confirm with user]

Read the `LoadBalancerListenerARN` default from the reference project's test-loadbalancer CF template.

| Resource | ARN |
|----------|-----|
| apps-core-internal-alb (test) | `arn:aws:elasticloadbalancing:us-east-1:554036784086:listener/app/apps-core-internal-alb/f6b0ee56a43c2d9d/f9744eecaa215739` |

---

## Reference Project Extraction Procedure

### If user provides a reference project

#### Step 1: Locate or clone the reference repo

```bash
# If in workspace
ls /path/to/workspace/search.service.<referenceProject>/

# If not, clone it
gh repo clone nike-internal/search.service.<referenceProject> /tmp/<referenceProject>
```

#### Step 2: Extract values

Read the following files and extract the annotated values:

| File | Values to extract |
|------|-------------------|
| `Jenkinsfile` | teamName, teamPrefix, instance types, sizing, security groups (all environments), pipeline profiles, @Library version, FAMI config, SignalFx thresholds |
| `cloudformation/service-role-waffle.yaml` | Managed policy ARN list, tag values (department, domain), role naming pattern |
| `cloudformation/*-test-loadbalancer.yaml` | ALB listener ARN, VPC stack name, email, account ID mappings, department/domain tags |
| `build.gradle` | Spring Boot version, plugin versions, Gradle wrapper version |
| `settings.gradle` | Artifactory URLs (should be standard), any project-specific config |
| `gradle.properties` | `group`, `artifactId`, `version` pattern |

#### Step 3: Present to user

Format all extracted **[REF]** values as a confirmation table:

```
I extracted the following configuration from <referenceProject>. Please confirm
or override each value for your new service:

| Setting                  | Value from reference           | Use for new service? |
|--------------------------|--------------------------------|----------------------|
| Team prefix              | search                         | Y/N (override: ___)  |
| Test instance type       | m7g.large                      | Y/N (override: ___)  |
| FAMI version             | 4.0 ARM64                      | Y/N (override: ___)  |
| Security groups (test)   | sg-0b7f..., sg-042..., sg-0cd..| Y/N (add: ___)       |
| IAM managed policies     | [7 policies listed]            | Y/N (add/remove: ___)|
| ALB listener ARN         | arn:aws:...                    | Y/N                  |
| ...                      | ...                            | ...                  |
```

### If NO reference project is provided

Use the defaults hardcoded in the templates above (drawn from `wholesaleeventscomposerv1`). Present them the same way:

```
No reference project provided. I'll use the following defaults (based on
standard Search team configuration). Please confirm or override each:

| Setting                  | Default value                  | Use for new service? |
|--------------------------|--------------------------------|----------------------|
| Team prefix              | search                         | Y/N (override: ___)  |
| Test instance type       | m7g.large                      | Y/N (override: ___)  |
| FAMI version             | 4.0 ARM64                      | Y/N (override: ___)  |
| Security groups (test)   | sg-0b7f..., sg-042..., sg-0cd..| Y/N (add: ___)       |
| IAM managed policies     | [7 policies listed]            | Y/N (add/remove: ___)|
| ALB listener ARN         | arn:aws:...                    | Y/N                  |
| ...                      | ...                            | ...                  |
```

### Step 4: Proceed only after confirmation

Do NOT generate templates or deploy infrastructure until the user confirms all **[REF]** values. If the user overrides any value, use their provided value instead.
