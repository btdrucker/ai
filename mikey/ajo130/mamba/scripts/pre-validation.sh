#!/bin/zsh

# Validation script. Runs all checks in parallel and exits with a non-zero code on failure.

# Workaround for SourceTree / other Git GUI users (https://community.atlassian.com/t5/Bitbucket-questions/SourceTree-Hook-failing-because-paths-don-t-seem-to-be-set/qaq-p/274792)
source ~/.zshrc

echo "Running pre-push checks..."

TEMP_OUTPUT=$(mktemp)
./gradlew detekt apiCheck checkSortDependencies spotlessCheck \
    --parallel --daemon --continue 2>&1 | tee "$TEMP_OUTPUT"
GRADLE_EXIT=${pipestatus[1]}

DETEKT_RESULT="PASSED"
API_CHECK_RESULT="PASSED"
SORT_DEPS_RESULT="PASSED"
SPOTLESS_RESULT="PASSED"

grep -qE ":detekt FAILED" "$TEMP_OUTPUT" && DETEKT_RESULT="FAILED"
grep -qE ":apiCheck FAILED|:kompare FAILED" "$TEMP_OUTPUT" && API_CHECK_RESULT="FAILED"
grep -qE ":checkSortDependencies FAILED" "$TEMP_OUTPUT" && SORT_DEPS_RESULT="FAILED"
grep -qE "spotless.*FAILED" "$TEMP_OUTPUT" && SPOTLESS_RESULT="FAILED"

DETEKT_FILES=""
SPOTLESS_FILES=""
API_CHECK_MODULES=""
SORT_DEPS_MODULES=""

if [ "$DETEKT_RESULT" = "FAILED" ]; then
    DETEKT_FILES=$(grep -v "^e: " "$TEMP_OUTPUT" | grep -oE "/[^ ]+\.kt:[0-9]+:[0-9]+" | sed "s|$(pwd)/||" | sort -u)
fi
if [ "$SPOTLESS_RESULT" = "FAILED" ]; then
    SPOTLESS_FILES=$(grep "format violations" -A 1 "$TEMP_OUTPUT" | grep -oE "src/[^ ]+\.(kt|java|kts)" | sort -u)
fi
if [ "$API_CHECK_RESULT" = "FAILED" ]; then
    API_CHECK_MODULES=$(grep -oE ":[^ ]+:(apiCheck|kompare) FAILED" "$TEMP_OUTPUT" | sed 's/:\(apiCheck\|kompare\) FAILED//' | sort -u)
fi
if [ "$SORT_DEPS_RESULT" = "FAILED" ]; then
    SORT_DEPS_MODULES=$(grep -oE ":[^ ]+:checkSortDependencies FAILED" "$TEMP_OUTPUT" | sed 's/:checkSortDependencies FAILED//' | sort -u)
fi

rm -f "$TEMP_OUTPUT"

if [ $GRADLE_EXIT -ne 0 ] && [ "$DETEKT_RESULT" = "PASSED" ] && [ "$API_CHECK_RESULT" = "PASSED" ] && [ "$SORT_DEPS_RESULT" = "PASSED" ] && [ "$SPOTLESS_RESULT" = "PASSED" ]; then
    DETEKT_RESULT="SKIPPED"
    API_CHECK_RESULT="SKIPPED"
    SORT_DEPS_RESULT="SKIPPED"
    SPOTLESS_RESULT="SKIPPED"
fi

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

colorize() {
    case "$1" in
        PASSED)  echo "${GREEN}PASSED${NC}" ;;
        FAILED)  echo "${RED}FAILED${NC}" ;;
        SKIPPED) echo "${YELLOW}SKIPPED${NC}" ;;
    esac
}

echo ""
echo "========== Pre-Push Results =========="
echo "  detekt:                $(colorize $DETEKT_RESULT)"
echo "  apiCheck:              $(colorize $API_CHECK_RESULT)"
echo "  checkSortDependencies: $(colorize $SORT_DEPS_RESULT)"
echo "  spotlessCheck:         $(colorize $SPOTLESS_RESULT)"
echo "======================================"

if [ $GRADLE_EXIT -ne 0 ]; then
    if [ "$DETEKT_RESULT" = "SKIPPED" ]; then
        echo ""
        echo "${RED}Gradle failed before tasks could run.${NC} Check the output above for configuration or dependency errors."
        echo ""
        echo "${RED}Push blocked.${NC}"
        exit 1
    fi

    if [ -n "$DETEKT_FILES" ]; then
        echo ""
        echo "  detekt failures:"
        echo "$DETEKT_FILES" | while read -r f; do echo "    $f"; done
    fi
    if [ -n "$SPOTLESS_FILES" ]; then
        echo ""
        echo "  spotless failures:"
        echo "$SPOTLESS_FILES" | while read -r f; do echo "    $f"; done
    fi
    if [ -n "$API_CHECK_MODULES" ]; then
        echo ""
        echo "  apiCheck failures:"
        echo "$API_CHECK_MODULES" | while read -r m; do echo "    $m"; done
    fi
    if [ -n "$SORT_DEPS_MODULES" ]; then
        echo ""
        echo "  checkSortDependencies failures:"
        echo "$SORT_DEPS_MODULES" | while read -r m; do echo "    $m"; done
    fi
    echo ""
    echo "To fix:"
    [ "$DETEKT_RESULT" = "FAILED" ] && echo "  detekt:                Fix code issues manually"
    [ "$API_CHECK_RESULT" = "FAILED" ] && echo "  apiCheck:              Run: ./gradlew apiDump"
    [ "$SORT_DEPS_RESULT" = "FAILED" ] && echo "  checkSortDependencies: Run: ./gradlew sortDependencies"
    [ "$SPOTLESS_RESULT" = "FAILED" ] && echo "  spotlessCheck:         Run: ./gradlew spotlessApply"
    echo ""
    echo "${RED}Push blocked.${NC} Fix the failures above, commit, and push again."
    exit 1
fi

echo ""
echo "${GREEN}All checks passed!${NC}"
