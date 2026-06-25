#!/bin/bash

# mamba-build-snapshot.sh
# Full end-to-end QA delivery pipeline:
#   1. Publish Mamba snapshot to Artifactory
#   2. Create feature branch in Nike App Android
#   3. Update Mamba version in Depends.kt
#   4. Stage, commit, push (no PR)
#   5. Trigger Jenkins build via DIS
#   6. Poll until complete (20 min initial, then every 3 min)
#   7. Extract TestFairy link from build log
#   8. Add comment to Jira ticket
#   9. Transition ticket to QA
#  10. Unassign ticket
#
# Usage:
#   ./mamba-build-snapshot.sh <TICKET_KEY> [BRANCH_SLUG]
#
# Examples:
#   ./mamba-build-snapshot.sh NIKEAPPUI-237
#   ./mamba-build-snapshot.sh NIKEAPPUI-237 mamba-carousel-fix

set -euo pipefail

TICKET_KEY="${1:-}"
BRANCH_SLUG="${2:-}"

if [[ -z "$TICKET_KEY" ]]; then
  echo "Usage: $0 <TICKET_KEY> [BRANCH_SLUG]"
  echo "  TICKET_KEY: Jira ticket (e.g., NIKEAPPUI-237)"
  echo "  BRANCH_SLUG: Optional branch descriptor (e.g., mamba-carousel-fix)"
  exit 1
fi

TICKET_KEY="$(echo "$TICKET_KEY" | tr '[:lower:]' '[:upper:]')"

MAMBA_REPO="${MAMBA_REPO:-$HOME/mpe.app.mamba-android}"
NIKEAPP_REPO="${NIKEAPP_REPO:-$HOME/mpe.app.nikeapp-android}"
DEPENDS_FILE="buildSrc/src/main/kotlin/Depends.kt"
DEPENDS_LINE=223
JENKINS_INSTANCE="mobile-ci"
JENKINS_JOB_PATH="Consumer/Nike_App/Android/Dev/Omega-Android-Feature-Manual"
TESTFAIRY_WORLD_BASE="https://nike.testfairy.com/join/NikeApp-Android-Feature-World"

if [[ -n "$BRANCH_SLUG" ]]; then
  BRANCH_NAME="feature/${BRANCH_SLUG}-${TICKET_KEY}"
else
  BRANCH_NAME="feature/mamba-snapshot-${TICKET_KEY}"
fi

echo "============================================"
echo "Mamba Build Snapshot → QA Delivery Pipeline"
echo "============================================"
echo ""
echo "  Ticket:  $TICKET_KEY"
echo "  Branch:  $BRANCH_NAME"
echo ""

# ─────────────────────────────────────────────
# STEP 1: Publish Mamba Snapshot to Artifactory
# ─────────────────────────────────────────────
echo "▶ Step 1: Publishing Mamba snapshot to Artifactory..."

cd "$MAMBA_REPO"

MAMBA_PR_URL=$(gh pr view --json url -q '.url' 2>/dev/null || echo "")

printf 'Y\nY\n' | ./publishing.sh 2>&1 | tee /tmp/mamba_snapshot_build.log || {
  echo ""
  echo "✗ Publishing failed. Check credentials:"
  echo "  security find-generic-password -a \"$(id -un)\" -s \"artifactory\" -w"
  exit 1
}

VERSION=$(grep -oP '\d+\.\d+\.\d+-\d+-[a-f0-9]+-SNAPSHOT' /tmp/mamba_snapshot_build.log | head -1)

if [[ -z "$VERSION" ]]; then
  echo "✗ Could not extract snapshot version from build output"
  exit 1
fi

echo ""
echo "  ✓ Published: $VERSION"
echo ""

# ─────────────────────────────────────────────
# STEP 2: Create Feature Branch in Nike App
# ─────────────────────────────────────────────
echo "▶ Step 2: Creating feature branch in Nike App Android..."

cd "$NIKEAPP_REPO"
git checkout main
git pull origin main
git checkout -b "$BRANCH_NAME"

echo "  ✓ Branch: $BRANCH_NAME"
echo ""

# ─────────────────────────────────────────────
# STEP 3: Update Mamba Version
# ─────────────────────────────────────────────
echo "▶ Step 3: Updating Mamba version in Depends.kt..."

DEPENDS_FULL_PATH="${NIKEAPP_REPO}/${DEPENDS_FILE}"

if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "${DEPENDS_LINE}s/.*/        const val mamba = \"${VERSION}\"/" "$DEPENDS_FULL_PATH"
else
  sed -i "${DEPENDS_LINE}s/.*/        const val mamba = \"${VERSION}\"/" "$DEPENDS_FULL_PATH"
fi

UPDATED_LINE=$(sed -n "${DEPENDS_LINE}p" "$DEPENDS_FULL_PATH")
echo "  ✓ Line ${DEPENDS_LINE}: ${UPDATED_LINE}"
echo ""

# ─────────────────────────────────────────────
# STEP 4: Stage, Commit, Push
# ─────────────────────────────────────────────
echo "▶ Step 4: Committing and pushing..."

git add "$DEPENDS_FILE"
git commit -m "${TICKET_KEY}: Update Mamba to ${VERSION} snapshot"
git push --no-verify -u origin "$BRANCH_NAME"

echo "  ✓ Pushed: origin/$BRANCH_NAME"
echo ""

# ─────────────────────────────────────────────
# STEP 5: Trigger Jenkins Build
# ─────────────────────────────────────────────
echo "▶ Step 5: Triggering Jenkins build..."

source ~/.zshrc 2>/dev/null || true

TRIGGER_RESULT=$(dis call jenkins_trigger_build "{\"instance\": \"${JENKINS_INSTANCE}\", \"path\": \"${JENKINS_JOB_PATH}\", \"parameters\": {\"BRANCH\": \"origin/${BRANCH_NAME}\"}}" 2>&1 | grep '^{' | head -1)

if echo "$TRIGGER_RESULT" | grep -q '"triggered":true'; then
  echo "  ✓ Jenkins build triggered"
else
  echo "  ✗ Failed to trigger Jenkins build:"
  echo "    $TRIGGER_RESULT"
  exit 1
fi

echo ""

# ─────────────────────────────────────────────
# STEP 6: Poll Jenkins Until Complete
# ─────────────────────────────────────────────
echo "▶ Step 6: Waiting for Jenkins build (est. 20-30 min)..."
echo "  Initial wait: 20 minutes..."

sleep 1200

BUILD_NUMBER=""
BUILD_RESULT=""
POLL_COUNT=0
MAX_POLLS=20

while [[ $POLL_COUNT -lt $MAX_POLLS ]]; do
  BUILD_JSON=$(dis call jenkins_get_build "{\"instance\": \"${JENKINS_INSTANCE}\", \"path\": \"${JENKINS_JOB_PATH}\"}" 2>&1 | grep '^{' | head -1)

  BUILDING=$(echo "$BUILD_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content']['building'])" 2>/dev/null || echo "true")
  
  if [[ "$BUILDING" == "False" || "$BUILDING" == "false" ]]; then
    BUILD_NUMBER=$(echo "$BUILD_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content']['number'])" 2>/dev/null)
    BUILD_RESULT=$(echo "$BUILD_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['content']['result'])" 2>/dev/null)
    break
  fi

  POLL_COUNT=$((POLL_COUNT + 1))
  echo "  Still building... (poll $POLL_COUNT/$MAX_POLLS, waiting 3 min)"
  sleep 180
done

if [[ -z "$BUILD_NUMBER" ]]; then
  echo "  ✗ Build timed out after polling"
  exit 1
fi

if [[ "$BUILD_RESULT" != "SUCCESS" ]]; then
  echo "  ✗ Build #${BUILD_NUMBER} failed with result: $BUILD_RESULT"
  echo "  Console: https://mobile-ci.nike.com:8443/job/Consumer/job/Nike_App/job/Android/job/Dev/job/Omega-Android-Feature-Manual/${BUILD_NUMBER}/console"
  exit 1
fi

echo "  ✓ Build #${BUILD_NUMBER} succeeded"
echo ""

# ─────────────────────────────────────────────
# STEP 7: Extract TestFairy Link
# ─────────────────────────────────────────────
echo "▶ Step 7: Extracting TestFairy link..."

SEARCH_RESULT=$(dis call jenkins_search_build_log "{\"instance\": \"${JENKINS_INSTANCE}\", \"path\": \"${JENKINS_JOB_PATH}\", \"build_number\": \"${BUILD_NUMBER}\", \"pattern\": \"Build URL\"}" 2>&1 | grep '^{' | head -1)

TESTFAIRY_BUILD_ID=$(echo "$SEARCH_RESULT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('content', {}).get('matches', []):
    line = m['line']
    if 'projects/432/builds/' in line:
        print(line.split('builds/')[1].split('\\\\')[0].strip())
        break
" 2>/dev/null)

if [[ -z "$TESTFAIRY_BUILD_ID" ]]; then
  echo "  ✗ Could not extract TestFairy build ID"
  echo "  Check manually: https://mobile-ci.nike.com:8443/job/Consumer/job/Nike_App/job/Android/job/Dev/job/Omega-Android-Feature-Manual/${BUILD_NUMBER}/console"
  exit 1
fi

TESTFAIRY_URL="${TESTFAIRY_WORLD_BASE}?id=${TESTFAIRY_BUILD_ID}"
echo "  ✓ TestFairy: $TESTFAIRY_URL"
echo ""

# ─────────────────────────────────────────────
# STEP 8-10: Jira Operations (output for agent)
# ─────────────────────────────────────────────
echo "▶ Step 8-10: Jira operations..."
echo ""
echo "  The following Jira operations should be performed via Atlassian MCP:"
echo ""
echo "  TICKET: $TICKET_KEY"
echo "  TESTFAIRY_URL: $TESTFAIRY_URL"
echo "  MAMBA_PR: $MAMBA_PR_URL"
echo "  NIKEAPP_BRANCH: https://github.com/nike-internal/mpe.app.nikeapp-android/tree/${BRANCH_NAME}"
echo "  VERSION: $VERSION"
echo ""
echo "  Comment format:"
echo "  ---"
echo "  Test ready!"
echo ""
echo "  build here ->"
echo "  NikeApp-Android-Feature-World"
echo "  ${TESTFAIRY_URL}"
echo ""
if [[ -n "$MAMBA_PR_URL" ]]; then
echo "  PR -> ${MAMBA_PR_URL}"
echo ""
fi
echo "  nike app branch used for testing -> https://github.com/nike-internal/mpe.app.nikeapp-android/tree/${BRANCH_NAME}"
echo "  ---"
echo ""
echo "  Then: transition to QA, unassign ticket."
echo ""
echo "============================================"
echo "Pipeline complete!"
echo "============================================"
echo ""
echo "Summary:"
echo "  • Mamba version: $VERSION"
echo "  • Branch: $BRANCH_NAME"
echo "  • Jenkins build: #$BUILD_NUMBER (SUCCESS)"
echo "  • TestFairy: $TESTFAIRY_URL"
echo "  • Ticket: $TICKET_KEY"
echo ""
