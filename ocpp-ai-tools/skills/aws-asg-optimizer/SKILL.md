---
name: aws-asg-optimizer
description: Analyze AWS Auto Scaling Group metrics and recommend optimal min/max values. Use when optimizing ASG capacity, analyzing scaling behavior, reducing costs, or improving performance for EC2 auto scaling groups. Not for ECS, Lambda, Fargate, or Kubernetes-managed workloads.
---

# AWS ASG Optimizer

Analyzes CloudWatch metrics and Jenkinsfile configurations to recommend optimal Auto Scaling Group min/max values based on actual usage patterns.

## Guardrails

**READ-ONLY AWS Operations**: This skill MUST only perform read operations against AWS. 

Allowed commands (read-only):
- `aws cloudwatch get-metric-statistics`
- `aws cloudwatch list-metrics`
- `aws autoscaling describe-auto-scaling-groups`
- `aws autoscaling describe-scaling-activities`
- `aws autoscaling describe-policies`
- `aws pricing get-products`
- `aws sts get-caller-identity`
- Any `describe`, `get`, `list` operations

NEVER execute commands that modify AWS resources:
- `aws autoscaling update-auto-scaling-group`
- `aws autoscaling put-scaling-policy`
- `aws autoscaling put-scheduled-action`
- `aws cloudformation update-stack`
- Any `create`, `update`, `delete`, `put`, or `set` operations

**Configuration Changes**: Do NOT directly modify Jenkinsfile or CloudFormation templates. Instead:
1. Present analysis and recommendations to the user
2. Ask for confirmation before proposing specific changes
3. Show the exact diff/changes that would be needed
4. Let the user decide whether to apply the changes

## Prerequisites

- AWS CLI installed
- `gimme-aws-creds` configured for AWS authentication
- Access to CloudWatch metrics for the target ASG
- Project Jenkinsfile with ASG configuration

## Workflow

### Step 0: Authenticate to AWS

Before running any AWS commands, ensure valid credentials are available.

**Check current credentials:**
```bash
aws sts get-caller-identity
```

If you see `ExpiredToken` or `InvalidClientTokenId` errors, refresh credentials:

```bash
gimme-aws-creds
```

This will prompt for Okta authentication and populate `~/.aws/credentials` with temporary session tokens.

**Select the appropriate AWS profile** if multiple accounts are configured:
```bash
export AWS_PROFILE=<your-prod-profile>
# or
export AWS_PROFILE=<your-test-profile>
```

List available profiles with: `cat ~/.aws/credentials | grep '^\[' | tr -d '[]'`

**Verify access to the target account:**
```bash
aws sts get-caller-identity --query Account --output text
```

If you encounter auth errors, see `references/commands.md` for troubleshooting.

### Step 1: Extract Current Configuration from Jenkinsfile

Parse the project's Jenkinsfile to extract ASG settings per environment.

**ASG Naming Convention**: ASG names typically include a version suffix (e.g., `-v001`, `-v034`). The Jenkinsfile defines the base name, but deployed ASGs append a version number. To find the actual ASG name:

```bash
# List ASGs matching the base name pattern
aws autoscaling describe-auto-scaling-groups \
  --region REGION \
  --query "AutoScalingGroups[*].AutoScalingGroupName" \
  --output text | tr '\t' '\n' | grep -i "APP_NAME_PATTERN"
```

The highest version number is typically the active deployment. Multiple versions may exist during blue-green deployments.

```bash
grep -E "(minSize|maxSize|desiredCapacity|scaleUpAdjustment|scaleDownMinSize|scaleUpCPUThreshold|scaleDownCPUThreshold|estimatedInstanceWarmup)" Jenkinsfile
```

Document these values in a table:

| Environment | minSize | maxSize | desiredCapacity | scaleUpAdjustment | scaleDownMinSize | CPU Up | CPU Down | Warmup |
|-------------|---------|---------|-----------------|-------------------|------------------|--------|----------|--------|
| test_USEast1 | ? | ? | ? | ? | ? | ? | ? | ? |
| prod_USEast1 | ? | ? | ? | ? | ? | ? | ? | ? |

### Step 2: Query CloudWatch Metrics (2 Weeks)

Fetch 14 days of ASG metrics. Replace `ASG_NAME` and `REGION` with actual values.

**CRITICAL: Query ALL ASG Versions and Aggregate Data**

During blue-green deployments, multiple ASG versions exist simultaneously (e.g., v033 and v034). The newest ASG may only have a few days of data, while older versions contain the historical behavior you need for accurate analysis.

**Failure to aggregate across all ASG versions will produce incorrect recommendations** — for example, concluding the service "never hits minSize" when it actually does so regularly on the previous ASG version during off-peak hours.

1. Find all ASG versions that existed during the analysis period:
```bash
aws autoscaling describe-auto-scaling-groups \
  --region REGION \
  --query "AutoScalingGroups[*].AutoScalingGroupName" \
  --output text | tr '\t' '\n' | grep -i "APP_NAME_PATTERN"
```

2. Query EACH ASG version separately for the full 14-day window
3. Combine datapoints from all versions, filtering out zero values (scaled-down old versions)
4. Compute min/max/avg/p95 across the combined dataset
5. For ceiling/floor analysis, check ALL versions — a floor hit on v033 is still a floor hit for the service

**GroupDesiredCapacity** (shows what the ASG wanted to run):
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/AutoScaling \
  --metric-name GroupDesiredCapacity \
  --dimensions Name=AutoScalingGroupName,Value=ASG_NAME \
  --start-time $(date -u -v-14d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Average Maximum Minimum \
  --region REGION
```

**GroupInServiceInstances** (actual running instances):
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/AutoScaling \
  --metric-name GroupInServiceInstances \
  --dimensions Name=AutoScalingGroupName,Value=ASG_NAME \
  --start-time $(date -u -v-14d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average Maximum Minimum \
  --region REGION
```

**CPUUtilization** (for performance analysis):
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=ASG_NAME \
  --start-time $(date -u -v-14d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average Maximum p99 \
  --region REGION
```

**RequestCountPerTarget** (if ALB-based):
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCountPerTarget \
  --dimensions Name=TargetGroup,Value=TARGET_GROUP_ARN \
  --start-time $(date -u -v-14d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum Average Maximum \
  --region REGION
```

### Step 3: Analyze Ceiling/Floor Hits

Determine if the ASG is hitting configured limits. **Check ALL ASG versions** — the newest version may not have enough history to show overnight/weekend patterns.

**Ceiling Hit Detection** (maxSize constraint):
- If `GroupDesiredCapacity == maxSize` for sustained periods (>15 min), the ASG wants more capacity but is capped
- Check corresponding CPU during these periods—high CPU indicates performance impact

**Floor Hit Detection** (minSize constraint):
- Query ALL ASG versions for `Minimum == minSize` to find floor hits
- Count hours where `Average == minSize` (at floor for full hour) vs hours that touched minSize
- If floor is never hit across ANY version, minSize may be too high (cost opportunity)
- If floor IS hit regularly (especially overnight), the current minSize is working correctly

### Step 4: Scaling Policy Analysis

Evaluate the asymmetric scaling behavior:

| Metric | Typical Pattern | Risk |
|--------|-----------------|------|
| Scale Up by N | 3-6 instances | Too low = slow response to spikes |
| Scale Down by N | 1-3 instances | Too aggressive = thrashing |
| Warmup Time | 300s (5 min) | Scale-up adds latency before relief |

**Critical Calculation**: Time to handle spike
```
Time to full capacity = (maxSize - current) / scaleUpAdjustment * warmup_time
```

Example: From 9 to 30 instances, scaling 3 at a time with 5-min warmup:
```
(30-9) / 3 * 5 = 35 minutes to reach full capacity
```

#### scaleUpAdjustment Trade-offs

**Too High (e.g., 6+ instances)**:
- ✅ Faster response to traffic spikes
- ❌ Overshoot: adds more capacity than needed, then CPU drops
- ❌ Triggers immediate scale-down, causing thrashing cycle
- ❌ Example pattern: 10 → 16 → 15 → 14 → 13 → 12 → 11 → 10 → 16 (repeat)

**Too Low (e.g., 1-2 instances)**:
- ✅ Gradual, stable scaling
- ❌ Slow response: may take multiple scale-up events to handle spike
- ❌ High CPU sustained while waiting for capacity

**Detecting Thrashing**:
Review scaling activity for patterns like:
```bash
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name ASG_NAME \
  --region REGION \
  --max-items 50 \
  --query "Activities[*].[StartTime,Description]" \
  --output table
```

Signs of thrashing:
- Rapid alternation between scale-up and scale-down events
- Scale-up by N followed by N individual scale-down events
- Multiple scaling cycles within the same hour

**Tuning Guidance**:
| Observed Pattern | Recommendation |
|------------------|----------------|
| Frequent overshoot + slow scale-down | Reduce scaleUpAdjustment (e.g., 6 → 3) |
| Slow spike response, sustained high CPU | Increase scaleUpAdjustment or raise minSize |
| Stable scaling, no thrashing | Current setting is appropriate |

**Ideal scaleUpAdjustment** should match the typical gap between minSize and average capacity. If service runs at 12-16 and minSize is 9, scaling by 3-4 reaches normal range in one step without overshoot.

### Step 5: Instance Type Analysis

Evaluate whether the instance type is appropriate for the workload, or if right-sizing could reduce costs.

**Get current instance type:**
```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names ASG_NAME \
  --region REGION \
  --query 'AutoScalingGroups[0].LaunchTemplate.LaunchTemplateId' \
  --output text | xargs -I {} aws ec2 describe-launch-template-versions \
  --launch-template-id {} --versions '$Latest' \
  --region REGION \
  --query 'LaunchTemplateVersions[0].LaunchTemplateData.InstanceType' \
  --output text
```

**Analyze CPU utilization relative to instance size:**

| Instance Type | vCPU | If Avg CPU is... | Assessment |
|---------------|------|------------------|------------|
| *.xlarge | 4 | < 15% | Potentially oversized |
| *.xlarge | 4 | 15-50% | Well-sized |
| *.xlarge | 4 | > 50% | Consider upsizing or more instances |
| *.large | 2 | < 25% | Potentially oversized |
| *.large | 2 | 25-60% | Well-sized |
| *.large | 2 | > 60% | Consider upsizing |

**Key calculation — Can we downsize?**
```
Peak vCPU used = (Max CPU % / 100) × current vCPU
If peak vCPU used < smaller instance vCPU → downsize is safe
```

Example: 64% max CPU on m8g.xlarge (4 vCPU) = 2.56 vCPU peak
- m8g.large (2 vCPU): 2.56 > 2 → would saturate during peaks ❌
- m8g.xlarge (4 vCPU): 2.56 < 4 → handles peaks ✓

**Count vs Type Trade-offs:**

| Optimization | When to Use | Savings | Risk |
|--------------|-------------|---------|------|
| Reduce instance count | Low avg CPU, peaks well below capacity | ~$100-400/mo per instance | Low - can scale back up |
| Downsize instance type | Low avg AND low peak CPU | ~50% per instance | Medium - may hit limits |
| Both | Very low utilization across all metrics | Highest | Higher - less headroom |

**Prefer reducing count over changing type when:**
- Peak CPU would exceed 70% of smaller instance's capacity
- Memory requirements are unknown (JVM heap, caching)
- Faster rollback needed (count changes are instant)
- Savings are similar between approaches

**Consider changing instance type when:**
- Peak CPU is well below 50% of current capacity
- Memory usage is confirmed low
- Consistent low utilization over weeks/months
- Significant cost difference vs count reduction

### Step 6: Generate Recommendations

#### Recommendation Framework

**Priority 1: Performance (Handle Traffic Spikes)**
- minSize should handle baseline + initial spike buffer
- Rule: `minSize >= p95_desired_capacity_during_normal_hours`
- Rationale: 5-minute warmup means scaling cannot react instantly

**Priority 2: Cost Optimization**
- Only after performance is ensured
- Look for over-provisioned minSize during sustained low-traffic
- Consider time-based scheduled actions for predictable patterns

#### Analysis Template

```markdown
## ASG Analysis: [ASG_NAME]

### Current Configuration
- Environment: [ENV]
- minSize: [X], maxSize: [Y], desiredCapacity: [Z]
- Scale Up: [N] instances when CPU > [X]%
- Scale Down: when CPU < [X]%, floor at [N] instances
- Instance Warmup: [X] seconds

### 2-Week Metrics Summary (Aggregated Across All ASG Versions)
| Metric | Min | Avg | Max | p99 |
|--------|-----|-----|-----|-----|
| DesiredCapacity | ? | ? | ? | ? |
| InServiceInstances | ? | ? | ? | ? |
| CPUUtilization | ? | ? | ? | ? |

### Capacity Distribution by Level

**IMPORTANT**: Always start from minSize and include every level, even if hours = 0. This reveals whether minSize is actually being utilized or if it's set too low.

| Level | Hours | Percentage | Visual |
|-------|-------|------------|--------|
| 9 (min) | ? | ?% | █ |
| 10 | ? | ?% | ██ |
| 11 | ? | ?% | ███ |
| 12 | ? | ?% | ████████ |
| 15 | ? | ?% | ██████ |
| 18 | ? | ?% | ███ |
| 21 | ? | ?% | █ |
| 24+ | ? | ?% | |

If minSize row shows 0 hours, the ASG never scales down that far — consider whether minSize could be raised.
If minSize row shows significant hours, the floor IS being used — keep minSize as-is to preserve cost savings.

### Ceiling/Floor Analysis (Aggregated Across All ASG Versions)
- Times at maxSize: [count/duration]
- Hours at minSize (full hour): [count] across [which ASG versions]
- Hours that touched minSize: [count]
- CPU during ceiling hits: [avg]%

### Scaling Behavior Analysis
- Current scaleUpAdjustment: [N]
- Thrashing detected: [Yes/No]
- Typical pattern: [e.g., "10 → 16 → gradual decline to 10 → repeat"]
- Recommendation: [Keep current / Reduce to N / Increase to N]

### Instance Type Analysis
- Instance type: [e.g., m8g.xlarge]
- vCPU per instance: [N]
- Current instance count: [N]
- Total vCPU capacity: [N × vCPU]
- Peak vCPU used: [Max CPU % × vCPU] = [N] vCPU
- Assessment: [Oversized / Well-sized / Undersized]

| Right-sizing Option | Change | Monthly Cost | Savings |
|---------------------|--------|--------------|---------|
| Current | [N] × [type] | $[X] | - |
| Reduce count | [N] × [type] | $[X] | $[X]/mo |
| Downsize type | [N] × [type] | $[X] | $[X]/mo |

Recommendation: [Reduce count / Downsize type / Keep current] — [rationale]

### Recommendations

#### Option A: Performance-Optimized
- minSize: [X] (based on p95 normal traffic)
- maxSize: [Y] (headroom for spikes + 20%)
- Rationale: [explanation]
- Cost Impact: [Use delta-based calculation — show actual additional instance-hours based on time below new min, NOT naive full-month calculation]

#### Option B: Cost-Optimized  
- minSize: [X] (based on sustained low-traffic floor)
- maxSize: [Y]
- Rationale: [explanation]
- Risk: [spike handling capability]
- Cost Savings: [Use delta-based calculation — show actual saved instance-hours based on time at old min that would now be lower]

#### Recommendation
[Choose Option A/B based on: traffic patterns, business criticality, budget]

#### Proposed Changes
[Show exact Jenkinsfile or CloudFormation changes needed - DO NOT apply directly]
[Ask user: "Would you like me to prepare these changes for your review?"]
```

## Best Practices

### Industry Guidelines

1. **Buffer for Warmup**: Since instances take ~5 minutes to warm up, maintain enough capacity to absorb traffic spikes during scale-up
2. **Asymmetric Scaling**: Scale up aggressively (3-6 at a time), scale down conservatively (1-2 at a time) to prevent thrashing
3. **Headroom**: maxSize should be 20-50% above observed peak to handle unexpected surges
4. **Multi-Metric Policies**: Combine CPU and request-based scaling for better responsiveness

### Warning Signs

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Sustained max capacity | maxSize too low | Increase maxSize |
| High CPU during scaling | Scale-up too slow | Increase scaleUpAdjustment |
| Frequent scale up/down cycles | Thresholds too close | Widen CPU threshold gap |
| Never scaling down | minSize too high or scaleDownMinSize | Review floor settings |

### Cost Estimation

Fetch current pricing for the instance type (requires us-east-1 region):
```bash
aws pricing get-products \
  --service-code AmazonEC2 \
  --region us-east-1 \
  --filters "Type=TERM_MATCH,Field=instanceType,Value=INSTANCE_TYPE" \
            "Type=TERM_MATCH,Field=location,Value=US East (N. Virginia)" \
            "Type=TERM_MATCH,Field=operatingSystem,Value=Linux" \
            "Type=TERM_MATCH,Field=tenancy,Value=Shared" \
            "Type=TERM_MATCH,Field=preInstalledSw,Value=NA" \
            "Type=TERM_MATCH,Field=capacitystatus,Value=Used" \
  --query 'PriceList[0]' --output text | jq -r '.terms.OnDemand[].priceDimensions[].pricePerUnit.USD'
```

#### Delta-Based Cost Impact Calculation

**Do NOT use naive calculations** like `(new_min - old_min) × hourly_rate × 730 hours`. This vastly overstates the cost impact.

**Correct approach**: Calculate cost based on the actual time the ASG runs below the proposed new minimum, using the historical capacity distribution data.

**Formula for raising minSize from `old_min` to `new_min`:**

```
Additional monthly cost = Σ (for each capacity level L where old_min ≤ L < new_min):
                          hours_at_level_L × (new_min - L) × hourly_rate × (730 / analysis_period_hours)
```

**Example**: Raising minSize from 9 to 12 where the ASG typically runs at 12-16 instances:

| Capacity Level | Hours in 2 weeks | Additional Instances Needed | Cost Impact |
|----------------|------------------|----------------------------|-------------|
| 9 (old min)    | 5 hours          | 3 (to reach 12)            | 5 × 3 × rate |
| 10             | 8 hours          | 2 (to reach 12)            | 8 × 2 × rate |
| 11             | 12 hours         | 1 (to reach 12)            | 12 × 1 × rate |
| 12+            | 311 hours        | 0 (already at or above)    | $0          |

```
Total additional instance-hours in 2 weeks = (5×3) + (8×2) + (12×1) = 15 + 16 + 12 = 43 instance-hours
Monthly projection = 43 × (730 / 336) = ~93 instance-hours/month
Monthly cost increase = 93 × hourly_rate
```

**Key insight**: If the ASG rarely drops below the new minimum, the cost increase is minimal. In this example, the ASG only spent 25 hours (7.4% of the time) below capacity level 12, so raising minSize to 12 costs far less than 3 full instances.

**Use the Capacity Distribution table** from Step 5 to calculate this. The table shows hours at each capacity level, which directly feeds into this formula.

#### Cost Impact Reporting Template

When presenting cost impact, show:
1. **Naive estimate** (for context): `(new_min - old_min) × rate × 730` — label this as "if always at minimum"
2. **Actual estimate** (use this): Delta calculation based on historical capacity distribution
3. **Percentage of naive**: Shows how much the actual cost differs from worst-case

Example output:
```
Cost Impact Analysis (raising minSize 9 → 12):
- Worst-case (always at old min): +$XXX/month (3 instances × 730 hours)
- Actual estimate: +$YY/month (based on 7.4% time below level 12)
- Cost efficiency: Actual is only ZZ% of worst-case estimate
```

## Example Output

For an ASG with these 2-week observations:
- DesiredCapacity: min=9, avg=14, max=45, p99=38
- CPU during max: 65%
- Hits maxSize (50): 3 times, total 45 minutes
- At minSize (9): 40% of nighttime hours (~134 hours)
- Capacity distribution: 9→5hrs, 10→8hrs, 11→12hrs, 12-16→275hrs, 17+→36hrs
- Instance type: m5.large @ $0.096/hour

**Recommendation**:
- Raise maxSize from 50 to 60 (ceiling being hit during spikes)
- Keep minSize at 9 (adequate for off-peak, allows scale-down savings)
- Consider scheduled action: minSize=12 during business hours (6am-10pm)

**Cost Impact Example** (if raising minSize from 9 to 12):
```
Capacity Distribution Analysis:
- Hours at 9:  5 hrs  → need +3 instances = 15 instance-hours
- Hours at 10: 8 hrs  → need +2 instances = 16 instance-hours  
- Hours at 11: 12 hrs → need +1 instance  = 12 instance-hours
- Hours at 12+: 311 hrs → no change       = 0 instance-hours

Total additional instance-hours (2 weeks): 43 hours
Monthly projection: 43 × (730/336) = ~93 instance-hours
Monthly cost increase: 93 × $0.096 = ~$9/month

Compare to naive calculation: 3 instances × 730 hours × $0.096 = $210/month
Actual cost is only 4.3% of worst-case estimate!
```

This demonstrates why delta-based cost calculation matters — the service already runs at 12+ capacity 93% of the time, so raising the floor has minimal cost impact while providing faster spike response.
