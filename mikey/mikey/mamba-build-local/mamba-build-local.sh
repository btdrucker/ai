#!/bin/bash

# mamba-build-local.sh
# Build Mamba Android locally and update consumer app dependency
#
# Usage:
#   ./mamba-build-local.sh
#
# Configuration:
#   Set environment variables before running:
#   - MAMBA_REPO_PATH: Path to Mamba Android repo (required)
#   - CONSUMER_REPO_PATH: Path to consumer app repo (required)
#   - DEPENDS_FILE_PATH: Relative path to dependency file (default: buildSrc/src/main/kotlin/Depends.kt)
#   - DEPENDS_LINE_NUMBER: Line number to update (default: 223)
#
# Workflow:
#   1. Run ./publishing.sh --local in mamba repo
#   2. Extract generated version from output
#   3. Update consumer app dependency file
#   4. Verify success

set -e

# Configuration (set via environment or modify here)
MAMBA_REPO_PATH="${MAMBA_REPO_PATH:-.}"
CONSUMER_REPO_PATH="${CONSUMER_REPO_PATH:-.}"
DEPENDS_FILE_PATH="${DEPENDS_FILE_PATH:-buildSrc/src/main/kotlin/Depends.kt}"
DEPENDS_LINE_NUMBER="${DEPENDS_LINE_NUMBER:-223}"

# Construct full paths
DEPENDS_FILE="${CONSUMER_REPO_PATH}/${DEPENDS_FILE_PATH}"

echo "Mamba Build Local"
echo "================="
echo ""
echo "Configuration:"
echo "  Mamba repo: $MAMBA_REPO_PATH"
echo "  Consumer repo: $CONSUMER_REPO_PATH"
echo "  Dependency file: $DEPENDS_FILE"
echo "  Line number: $DEPENDS_LINE_NUMBER"
echo ""

# Step 1: Verify repos exist
if [[ ! -d "$MAMBA_REPO_PATH" ]]; then
  echo "Error: Mamba repo not found at $MAMBA_REPO_PATH"
  exit 1
fi

if [[ ! -d "$CONSUMER_REPO_PATH" ]]; then
  echo "Error: Consumer repo not found at $CONSUMER_REPO_PATH"
  exit 1
fi

if [[ ! -f "$DEPENDS_FILE" ]]; then
  echo "Error: Dependency file not found at $DEPENDS_FILE"
  exit 1
fi

echo "Step 1: Running ./publishing.sh --local in mamba repo..."
echo ""

# Step 2: Run publishing.sh --local
# This will prompt for credentials interactively
cd "$MAMBA_REPO_PATH"
./publishing.sh --local 2>&1 | tee /tmp/mamba_build.log || {
  echo ""
  echo "Error: Build failed"
  exit 1
}

echo ""
echo "Step 2: Extracting version from build output..."

# Step 3: Parse version from build log
# Look for lines like: "Artifact: com.nike.capabilities.shop:glue:47.0.0-20260528-e3a83867-LOCAL"
# Extract first artifact version which represents the mamba version
VERSION=$(grep -oP 'Artifact: com\.nike\.[^:]+:[^:]+:\K[0-9]+\.[0-9]+\.[0-9]+-[0-9]+-[a-f0-9]+-LOCAL' /tmp/mamba_build.log | head -1)

if [[ -z "$VERSION" ]]; then
  echo "Error: Could not extract version from build output"
  echo "Expected format: X.Y.Z-YYYYMMDD-HASH-LOCAL"
  exit 1
fi

echo "  Generated version: $VERSION"
echo ""

# Step 4: Update dependency file
echo "Step 3: Updating dependency file line $DEPENDS_LINE_NUMBER..."

# Create backup
cp "$DEPENDS_FILE" "${DEPENDS_FILE}.backup"

# Update the line using sed
# Platform-specific: macOS requires '' argument, Linux doesn't
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' "${DEPENDS_LINE_NUMBER}s/.*/        const val mamba = \"${VERSION}\"/" "$DEPENDS_FILE"
else
  sed -i "${DEPENDS_LINE_NUMBER}s/.*/        const val mamba = \"${VERSION}\"/" "$DEPENDS_FILE"
fi

# Verify the update
NEW_VALUE=$(sed -n "${DEPENDS_LINE_NUMBER}p" "$DEPENDS_FILE")
echo "  New value: $NEW_VALUE"
echo ""

# Step 5: Confirm success
if [[ "$NEW_VALUE" == *"$VERSION"* ]]; then
  echo "✅ Success!"
  echo ""
  echo "Summary:"
  echo "  • Built: $VERSION"
  echo "  • Updated: $DEPENDS_FILE:$DEPENDS_LINE_NUMBER"
  echo "  • Backup: ${DEPENDS_FILE}.backup"
  echo ""
  echo "Next steps:"
  echo "  1. Run gradle sync in IDE"
  echo "  2. Invalidate IDE cache if needed"
  echo "  3. Test your changes with the local build"
  echo ""
  exit 0
else
  echo "❌ Error: Update verification failed"
  echo "  Expected: $VERSION"
  echo "  Got: $NEW_VALUE"
  # Restore backup
  mv "${DEPENDS_FILE}.backup" "$DEPENDS_FILE"
  exit 1
fi

