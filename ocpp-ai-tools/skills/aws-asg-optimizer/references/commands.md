# AWS ASG Optimizer Reference

Detailed commands and analysis scripts for ASG optimization.

## AWS Authentication

### gimme-aws-creds Setup

If credentials are expired or missing, authenticate first:

```bash
# Check current identity (will error if expired)
aws sts get-caller-identity

# Refresh credentials via Okta SSO
gimme-aws-creds

# Select profile for the target environment
export AWS_PROFILE=<your-prod-profile>   # for prod
export AWS_PROFILE=<your-test-profile>   # for test

# Verify you're in the right account
aws sts get-caller-identity
```

### Troubleshooting Authentication

| Error | Cause | Solution |
|-------|-------|----------|
| `ExpiredToken` | Session token expired | Run `gimme-aws-creds` |
| `InvalidClientTokenId` | No credentials configured | Run `gimme-aws-creds` |
| `AccessDenied` | Wrong account or missing permissions | Check `AWS_PROFILE`, verify role |
| `SignatureDoesNotMatch` | Clock skew or corrupted creds | Sync system time, re-run `gimme-aws-creds` |

### gimme-aws-creds Errors

**KeyError: 'location'** - OAuth flow failed, Okta didn't redirect properly.

Causes and fixes:
1. **Okta session expired in browser** - Open https://nike.okta.com in browser, sign in, then retry
2. **Outdated gimme-aws-creds** - Update: `pip install --upgrade gimme-aws-creds`
3. **Config issue** - Check `~/.okta_aws_login_config` for correct `app_url` and `client_id`
4. **Network/VPN issue** - Ensure VPN is connected if required
5. **Browser auth required** - Try: `gimme-aws-creds --action-configure` to reconfigure

**Alternative: Use device authorization flow**
```bash
gimme-aws-creds --device
```
This opens a browser for authentication instead of using stored cookies.

**Clear cached Okta session and retry:**
```bash
rm -rf ~/.okta_aws_login_config.d/
gimme-aws-creds
```

**Check gimme-aws-creds version:**
```bash
gimme-aws-creds --version
pip show gimme-aws-creds
```

**"MFA factor does not meet authentication policies"** - The app requires a specific MFA type.

Solutions:
1. **Use WebAuthn/FIDO2 (hardware key or Touch ID)**:
   ```bash
   gimme-aws-creds --mfa-code webauthn
   ```
   Or update `~/.okta_aws_login_config`:
   ```ini
   preferred_mfa_type = webauthn
   ```

2. **Combine with device flow**:
   ```bash
   gimme-aws-creds --device --mfa-code webauthn
   ```

3. **Use browser-based auth entirely** - If CLI MFA keeps failing, authenticate through Okta dashboard:
   - Go to https://nike.okta.com
   - Find the AWS app tile and click it
   - This authenticates in browser with proper MFA
   - Some setups cache the session for CLI use afterward

4. **Check available MFA factors**:
   ```bash
   gimme-aws-creds --list-profiles
   ```

Common `preferred_mfa_type` values: `webauthn`, `push`, `token:software:totp`, `token:hardware`

### Profile Configuration

List available profiles:
```bash
cat ~/.aws/credentials | grep '^\[' | tr -d '[]'
```

Check which profile is active:
```bash
echo $AWS_PROFILE
aws configure list
```

## Complete CloudWatch Query Script

Save as `fetch-asg-metrics.sh` and run with: `./fetch-asg-metrics.sh ASG_NAME REGION`

```bash
#!/bin/bash
set -e

ASG_NAME="${1:?Usage: $0 ASG_NAME REGION}"
REGION="${2:?Usage: $0 ASG_NAME REGION}"
START_TIME=$(date -u -v-14d +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%SZ)
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "=== ASG Metrics for $ASG_NAME ($REGION) ==="
echo "Period: $START_TIME to $END_TIME"
echo ""

echo "--- GroupDesiredCapacity ---"
aws cloudwatch get-metric-statistics \
  --namespace AWS/AutoScaling \
  --metric-name GroupDesiredCapacity \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 3600 \
  --statistics Average Maximum Minimum \
  --region "$REGION" \
  --output table

echo ""
echo "--- GroupInServiceInstances ---"
aws cloudwatch get-metric-statistics \
  --namespace AWS/AutoScaling \
  --metric-name GroupInServiceInstances \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 3600 \
  --statistics Average Maximum Minimum \
  --region "$REGION" \
  --output table

echo ""
echo "--- GroupPendingInstances (scaling activity) ---"
aws cloudwatch get-metric-statistics \
  --namespace AWS/AutoScaling \
  --metric-name GroupPendingInstances \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 3600 \
  --statistics Average Maximum Sum \
  --region "$REGION" \
  --output table

echo ""
echo "--- CPUUtilization ---"
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 3600 \
  --statistics Average Maximum \
  --region "$REGION" \
  --output table
```

## Jenkinsfile Parsing

Extract ASG config from Groovy-based Jenkinsfile:

```bash
# Extract all ASG-related config per environment
grep -A 30 "deploymentEnvironment:" Jenkinsfile | \
  grep -E "(test_|prod_|minSize|maxSize|desiredCapacity|scaleUp|scaleDown|Threshold|Warmup)"
```

### Common Jenkinsfile ASG Parameters

| Parameter | Description | Impact |
|-----------|-------------|--------|
| `minSize` | Minimum instances always running | Cost floor, baseline capacity |
| `maxSize` | Maximum instances allowed | Capacity ceiling |
| `desiredCapacity` | Initial/target count on deploy | Starting point |
| `scaleUpAdjustment` | Instances added per scale-up event | Spike response speed |
| `scaleDownMinSize` | Floor during scale-down | Different from minSize in some configs |
| `scaleUpCPUThreshold` | CPU % triggering scale-up | Sensitivity to load |
| `scaleDownCPUThreshold` | CPU % triggering scale-down | Aggressiveness of scale-down |
| `estimatedInstanceWarmup` | Seconds before new instance handles traffic | Scale-up latency |

## Scaling Policy Types

### Simple Scaling
- Add/remove fixed number of instances
- Cooldown period between actions
- Can cause slow response to rapid changes

### Step Scaling
- Different adjustments for different metric ranges
- Example: +2 at 60% CPU, +4 at 80% CPU
- Better for variable load patterns

### Target Tracking
- Maintains metric at target value automatically
- Example: Keep average CPU at 50%
- AWS handles scale-up/down decisions

## Ceiling/Floor Detection Queries

### Check if hitting maxSize ceiling
```bash
# Get periods where DesiredCapacity equals maxSize
aws cloudwatch get-metric-statistics \
  --namespace AWS/AutoScaling \
  --metric-name GroupDesiredCapacity \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 300 \
  --statistics Maximum \
  --region "$REGION" \
  --query "Datapoints[?Maximum==\`$MAX_SIZE\`]" \
  --output table
```

### Get scaling activity history
```bash
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name "$ASG_NAME" \
  --region "$REGION" \
  --max-items 50 \
  --query "Activities[*].[StartTime,StatusCode,Description]" \
  --output table
```

## Cost Calculation

### Fetch Current On-Demand Pricing

The AWS Pricing API must be called from us-east-1:

```bash
# Get hourly rate for a specific instance type
INSTANCE_TYPE="m8g.xlarge"
HOURLY_RATE=$(aws pricing get-products \
  --service-code AmazonEC2 \
  --region us-east-1 \
  --filters "Type=TERM_MATCH,Field=instanceType,Value=$INSTANCE_TYPE" \
            "Type=TERM_MATCH,Field=location,Value=US East (N. Virginia)" \
            "Type=TERM_MATCH,Field=operatingSystem,Value=Linux" \
            "Type=TERM_MATCH,Field=tenancy,Value=Shared" \
            "Type=TERM_MATCH,Field=preInstalledSw,Value=NA" \
            "Type=TERM_MATCH,Field=capacitystatus,Value=Used" \
  --query 'PriceList[0]' --output text | jq -r '.terms.OnDemand[].priceDimensions[].pricePerUnit.USD')

echo "$INSTANCE_TYPE: \$$HOURLY_RATE/hour = \$$(echo "$HOURLY_RATE * 730" | bc)/month"
```

For other regions, change the `location` filter value (e.g., "US West (Oregon)").

### Savings Calculation
```
Monthly savings = (current_min - proposed_min) × hourly_rate × 730
```

## Performance Analysis

### Spike Response Time Formula
```
full_scale_time = ceil((max_capacity - current_capacity) / scale_up_adjustment) × warmup_seconds
```

### Recommended Warmup Buffer
For 5-minute warmup with 3-instance scale-up:
- Maintain `minSize` that can handle 5 minutes of traffic growth
- If traffic can grow 50% in 5 minutes, minSize should handle 1.5× baseline

### CPU Correlation Analysis
When analyzing CPU vs. instance count:
- High CPU (>70%) with instances at max → Need higher maxSize
- Low CPU (<30%) with instances at min → Potential to lower minSize
- High CPU during scale-up → Scale-up adjustment too low

## Instance Type Analysis

### Get Current Instance Type
```bash
# Get launch template ID from ASG
LT_ID=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "$ASG_NAME" \
  --region "$REGION" \
  --query 'AutoScalingGroups[0].LaunchTemplate.LaunchTemplateId' \
  --output text)

# Get instance type from launch template
aws ec2 describe-launch-template-versions \
  --launch-template-id "$LT_ID" \
  --versions '$Latest' \
  --region "$REGION" \
  --query 'LaunchTemplateVersions[0].LaunchTemplateData.InstanceType' \
  --output text
```

### Instance Type Reference (Graviton m8g family)
| Type | vCPU | RAM | Hourly | Monthly |
|------|------|-----|--------|---------|
| m8g.medium | 1 | 4 GB | ~$0.045 | ~$33 |
| m8g.large | 2 | 8 GB | ~$0.09 | ~$66 |
| m8g.xlarge | 4 | 16 GB | ~$0.18 | ~$131 |
| m8g.2xlarge | 8 | 32 GB | ~$0.36 | ~$263 |

### Calculate Peak vCPU Usage
```bash
# Get max CPU and calculate peak vCPU used
MAX_CPU=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" --end-time "$END_TIME" \
  --period 3600 --statistics Maximum \
  --region "$REGION" \
  --query 'max(Datapoints[*].Maximum)' --output text)

echo "Max CPU: $MAX_CPU%"
echo "On 4 vCPU instance: $(echo "$MAX_CPU * 4 / 100" | bc -l) vCPU peak"
```

### CPU Distribution Analysis
```bash
# How often do we hit different CPU levels?
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value="$ASG_NAME" \
  --start-time "$START_TIME" --end-time "$END_TIME" \
  --period 3600 --statistics Maximum \
  --region "$REGION" \
  --query 'Datapoints[*].Maximum' \
  --output json | jq -s 'add | {
    "under_20pct": [.[] | select(. < 20)] | length,
    "20_to_50pct": [.[] | select(. >= 20 and . < 50)] | length,
    "50_to_70pct": [.[] | select(. >= 50 and . < 70)] | length,
    "over_70pct": [.[] | select(. >= 70)] | length,
    "max_seen": max,
    "total_hours": length
  }'
```

### Right-Sizing Decision Matrix
| Avg CPU | Max CPU | Recommendation |
|---------|---------|----------------|
| < 15% | < 50% | Can likely downsize instance type |
| < 15% | > 50% | Reduce count, keep instance type |
| 15-40% | < 70% | Well-sized, optimize count only |
| > 40% | > 70% | Consider upsizing or more instances |

## Scheduled Actions

For predictable traffic patterns, consider scheduled scaling:

```bash
# View existing scheduled actions
aws autoscaling describe-scheduled-actions \
  --auto-scaling-group-name "$ASG_NAME" \
  --region "$REGION"

# Example: Increase minSize during business hours
aws autoscaling put-scheduled-action \
  --auto-scaling-group-name "$ASG_NAME" \
  --scheduled-action-name "business-hours-scale-up" \
  --recurrence "0 6 * * MON-FRI" \
  --min-size 12 \
  --desired-capacity 12 \
  --region "$REGION"
```

## Troubleshooting

### Scaling Not Happening
1. Check CloudWatch alarm state
2. Verify scaling policy is attached
3. Check for suspended processes: `aws autoscaling describe-auto-scaling-groups`
4. Review scaling activity for errors

### Instances Not Becoming Healthy
1. Check health check type (EC2 vs ELB)
2. Review health check grace period
3. Check target group health in ALB
4. Review instance logs for startup failures
