#!/usr/bin/env bash
# pre-push-fix.sh
# Auto-fix common Gradle pre-push hook failures for Nike Android repos.
#
# Usage:
#   pre-push-fix.sh [repo-type]
#
# repo-type: auto (default) | nikeapp | mamba | productwall

set -euo pipefail

REPO_TYPE="${1:-auto}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

detect_repo_type() {
  case "$(basename "$ROOT")" in
    mpe.app.nikeapp-android) echo "nikeapp" ;;
    mpe.app.mamba-android) echo "mamba" ;;
    mpe.feature.productwall) echo "productwall" ;;
    *)
      if [[ -f "./local-checks.sh" ]]; then
        echo "mamba"
      elif [[ -f "./gradlew" ]]; then
        echo "nikeapp"
      else
        echo "unknown"
      fi
      ;;
  esac
}

if [[ "$REPO_TYPE" == "auto" ]]; then
  REPO_TYPE="$(detect_repo_type)"
fi

echo "pre-push-fix: repo=${REPO_TYPE} root=${ROOT}"

fix_common() {
  if [[ -x "./gradlew" ]]; then
    echo "Running spotlessApply..."
    ./gradlew spotlessApply --daemon --quiet || ./gradlew spotlessApply --daemon
    if git diff --quiet; then
      echo "No spotless changes"
    else
      echo "Spotless applied changes — review and stage"
      git add -u
    fi
  fi
}

case "$REPO_TYPE" in
  mamba)
    if [[ -x "./local-checks.sh" ]]; then
      echo "Running local-checks.sh --fix..."
      ./local-checks.sh --fix || true
    else
      fix_common
      if [[ -x "./gradlew" ]]; then
        echo "Running checkSortDependencies..."
        ./gradlew checkSortDependencies --daemon --quiet || ./gradlew checkSortDependencies --daemon || true
      fi
    fi
    ;;
  nikeapp|productwall|unknown)
    fix_common
    ;;
esac

echo "pre-push-fix: done"
