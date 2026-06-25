#!/bin/zsh

# =============================================================================
# Mamba Android Local Checks
# =============================================================================
# Run PRA checks locally before pushing to verify your changes.
#
# Usage:
#   ./local-checks.sh --prepush   # Fast checks (~30s): spotless, detekt, apiCheck, lint
#   ./local-checks.sh --fix       # Auto-fix common issues then verify (~1min)
#   ./local-checks.sh --pra       # Full PRA simulation (~15min)
#   ./local-checks.sh --help      # Show this help
#
# Agent Integration:
#   ./local-checks.sh --prepush --json    # Output JSON for programmatic use
#   ./local-checks.sh --prepush --agent   # Generate Goose fix prompt if issues found
# =============================================================================

source ~/.zshrc 2>/dev/null || true

set -o pipefail

# Configuration
SCRIPT_DIR="${0:A:h}"
PROJECT_ROOT="${SCRIPT_DIR}"
OUTPUT_DIR="${PROJECT_ROOT}/_pra-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE="${OUTPUT_DIR}/pra-result-${TIMESTAMP}.json"
BUILD_HEALTH_REPORT="${PROJECT_ROOT}/build/reports/dependency-analysis/build-health-report.txt"
BUILD_HEALTH_JSON="${PROJECT_ROOT}/build/reports/dependency-analysis/build-health-report.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Result tracking
declare -A RESULTS
declare -A LOG_FILES
OVERALL_SUCCESS=true
ISSUES_FOUND=()
BUILD_HEALTH_ISSUES=()

# Gradle optimization flags (as array for proper expansion)
GRADLE_OPTS=(--parallel --build-cache)

print_header() { echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n${BLUE}  $1${NC}\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ $1${NC}"; }

init_output() {
    mkdir -p "${OUTPUT_DIR}"
    # Keep only the 5 most recent result files
    ls -t "${OUTPUT_DIR}"/pra-result-*.json 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
}

# Run multiple gradle tasks in a single invocation (Gradle handles parallelism internally)
run_gradle_tasks() {
    local name="$1"
    local description="$2"
    shift 2
    local tasks=("$@")
    
    print_header "Running: ${description}"
    print_info "Tasks: ${tasks[*]}"
    print_info "Gradle opts: ${GRADLE_OPTS[*]}"
    
    local output_file="${OUTPUT_DIR}/${name}-${TIMESTAMP}.log"
    LOG_FILES[${name}]="${output_file}"
    local start_time=$(date +%s)
    
    if ./gradlew "${GRADLE_OPTS[@]}" "${tasks[@]}" 2>&1 | tee "${output_file}"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        RESULTS[${name}]="pass"
        print_success "${description} passed in ${duration}s"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        RESULTS[${name}]="fail"
        OVERALL_SUCCESS=false
        print_error "${description} FAILED after ${duration}s"
        
        # Parse which specific tasks failed
        local failed_tasks=$(grep "^> Task .* FAILED" "${output_file}" | sed 's/> Task //' | sed 's/ FAILED//')
        local errors=$(grep -E "(FAILURE|ERROR|error:|> Task .* FAILED)" "${output_file}" | head -30)
        
        # Determine fix commands based on failed tasks
        local fix_cmds=""
        if echo "${failed_tasks}" | grep -q "spotless"; then
            fix_cmds+="./gradlew spotlessApply; "
        fi
        if echo "${failed_tasks}" | grep -q "apiCheck\|kompare"; then
            fix_cmds+="./gradlew apiDump; "
        fi
        if echo "${failed_tasks}" | grep -q "checkSortDependencies"; then
            fix_cmds+="./gradlew sortDependencies; "
        fi
        if echo "${failed_tasks}" | grep -q "detekt"; then
            fix_cmds+="Fix detekt issues in source code (DO NOT use detektBaseline); "
        fi
        
        ISSUES_FOUND+=("{\"check\": \"${name}\", \"description\": \"${description}\", \"fix_command\": \"${fix_cmds:-See log file}\", \"log_file\": \"${output_file}\", \"errors\": \"$(echo "${errors}" | head -20 | sed 's/"/\\\\"/g' | tr '\n' '|')\"}")
        
        return 1
    fi
}

# Parse build health report for dependency issues
parse_build_health() {
    if [[ ! -f "${BUILD_HEALTH_REPORT}" ]]; then
        return 0
    fi
    
    local issues_count=$(grep -c "^Advice for" "${BUILD_HEALTH_REPORT}" 2>/dev/null || echo "0")
    
    if [[ "${issues_count}" -eq 0 ]] || [[ ! -s "${BUILD_HEALTH_REPORT}" ]]; then
        RESULTS[build_health]="pass"
        return 0
    fi
    
    print_warning "Found ${issues_count} module(s) with dependency issues"
    RESULTS[build_health]="fail"
    OVERALL_SUCCESS=false
    
    local current_module=""
    local advice_text=""
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^"Advice for" ]]; then
            if [[ -n "${current_module}" ]] && [[ -n "${advice_text}" ]]; then
                BUILD_HEALTH_ISSUES+=("{\"module\": \"${current_module}\", \"advice\": \"$(echo "${advice_text}" | sed 's/"/\\\\"/g' | tr '\n' '|')\"}")
            fi
            current_module=$(echo "$line" | sed 's/Advice for //')
            advice_text=""
        elif [[ -n "$line" ]]; then
            advice_text+="${line}\n"
        fi
    done < "${BUILD_HEALTH_REPORT}"
    
    if [[ -n "${current_module}" ]] && [[ -n "${advice_text}" ]]; then
        BUILD_HEALTH_ISSUES+=("{\"module\": \"${current_module}\", \"advice\": \"$(echo "${advice_text}" | sed 's/"/\\\\"/g' | tr '\n' '|')\"}")
    fi
    
    ISSUES_FOUND+=("{\"check\": \"build_health\", \"description\": \"Build Health (Dependency Analysis)\", \"fix_command\": \"Edit build.gradle.kts files per advice\", \"log_file\": \"${BUILD_HEALTH_REPORT}\", \"errors\": \"Found ${issues_count} modules with dependency issues\"}")
    
    print_info "Build Health Issues:"
    cat "${BUILD_HEALTH_REPORT}"
    
    return 1
}

# Generate JSON result file
generate_result_json() {
    local issues_json="["
    local first=true
    for issue in "${ISSUES_FOUND[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            issues_json+=","
        fi
        issues_json+="${issue}"
    done
    issues_json+="]"
    
    local build_health_json="["
    first=true
    for bh_issue in "${BUILD_HEALTH_ISSUES[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            build_health_json+=","
        fi
        build_health_json+="${bh_issue}"
    done
    build_health_json+="]"
    
    cat > "${RESULT_FILE}" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "project": "mamba-android",
  "project_path": "${PROJECT_ROOT}",
  "overall_success": ${OVERALL_SUCCESS},
  "checks": {
    "spotless": "${RESULTS[spotless]:-skipped}",
    "detekt": "${RESULTS[detekt]:-skipped}",
    "api_check": "${RESULTS[api_check]:-skipped}",
    "sort_dependencies": "${RESULTS[sort_dependencies]:-skipped}",
    "build_health": "${RESULTS[build_health]:-skipped}",
    "lint": "${RESULTS[lint]:-skipped}",
    "unit_tests": "${RESULTS[unit_tests]:-skipped}",
    "gradle_plugin": "${RESULTS[gradle_plugin]:-skipped}"
  },
  "issues": ${issues_json},
  "build_health_details": ${build_health_json},
  "fix_instructions": {
    "spotless": "./gradlew spotlessApply",
    "api_check": "./gradlew apiDump",
    "sort_dependencies": "./gradlew sortDependencies",
    "detekt": "Fix code issues directly - DO NOT use detektBaseline",
    "build_health": "Edit build.gradle.kts files per build-health-report.txt",
    "lint": "Fix Android lint issues in source code",
    "unit_tests": "Fix failing tests"
  }
}
EOF
    
    print_info "Results written to: ${RESULT_FILE}"
}

# Generate agent prompt for Goose
generate_agent_prompt() {
    if [[ "${OVERALL_SUCCESS}" == "true" ]]; then
        echo ""
        print_success "All checks passed! No fixes needed."
        return
    fi
    
    echo ""
    print_header "Agent Fix Instructions"
    echo -e "${CYAN}Copy the following to Goose to auto-fix issues:${NC}"
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────"
    
    echo "Please fix the PRA issues in the mamba-android project at ${PROJECT_ROOT}"
    echo ""
    echo "⚠️ IMPORTANT: DO NOT use detektBaseline to fix detekt issues. Fix the actual code instead."
    echo ""

    for issue in "${ISSUES_FOUND[@]}"; do
        local check=$(echo "$issue" | grep -o '"check": "[^"]*"' | cut -d'"' -f4)
        local fix_cmd=$(echo "$issue" | grep -o '"fix_command": "[^"]*"' | cut -d'"' -f4)
        local log_file=$(echo "$issue" | grep -o '"log_file": "[^"]*"' | cut -d'"' -f4)
        
        echo "## ${check} FAILED"
        echo "- Fix command: \`${fix_cmd}\`"
        echo "- Log file: ${log_file}"
        
        if [[ "${check}" == "build_health" ]]; then
            echo ""
            echo "### Build Health Issues"
            cat "${BUILD_HEALTH_REPORT}" 2>/dev/null || echo "Report not available"
        fi
        echo ""
    done
    
    echo "After fixing, run: ./local-checks.sh --prepush"
    echo "────────────────────────────────────────────────────────────────────────────"
}

# =============================================================================
# CHECK MODES
# =============================================================================

# --prepush: Fast pre-push checks (~30s)
run_prepush_checks() {
    print_info "Running pre-push checks (spotless + detekt + apiCheck + lint)"
    
    run_gradle_tasks "prepush" "Pre-push Checks" \
        spotlessCheck detekt apiCheck lint \
        -x :app:lintChinaDebug -x :app:lintChinaRelease
    
    # Map individual results
    RESULTS[spotless]=${RESULTS[prepush]:-pass}
    RESULTS[detekt]=${RESULTS[prepush]:-pass}
    RESULTS[api_check]=${RESULTS[prepush]:-pass}
    RESULTS[lint]=${RESULTS[prepush]:-pass}
}

# --pra: Full PRA simulation (~15min)
run_full_pra() {
    print_info "Running full PRA simulation (matches Jenkins pipeline)"
    
    # Static checks (same as Jenkins "Static Checks" stage)
    run_gradle_tasks "static" "Static Checks" \
        spotlessCheck checkSortDependencies apiCheck detekt \
        :nike-gradle-plugin:spotlessCheck buildHealth
    
    RESULTS[spotless]=${RESULTS[static]:-pass}
    RESULTS[sort_dependencies]=${RESULTS[static]:-pass}
    RESULTS[api_check]=${RESULTS[static]:-pass}
    RESULTS[detekt]=${RESULTS[static]:-pass}
    RESULTS[gradle_plugin]=${RESULTS[static]:-pass}
    
    # Parse build health for detailed advice
    parse_build_health
    
    # Lint checks (same as Jenkins "Lint" stage)
    run_gradle_tasks "lint" "Android Lint" \
        lint -x :app:lintChinaDebug -x :app:lintChinaRelease
    
    # Unit tests with coverage (same as Jenkins "Unit Tests" stage)
    run_gradle_tasks "unit_tests" "Unit Tests" \
        test jacocoCoverage -x :app:testChinaDebugUnitTest -x :app:testChinaReleaseUnitTest
    
    # Assemble (same as Jenkins "Assemble" stage)
    run_gradle_tasks "assemble" "Assemble APKs" \
        assembleWorld
}

# --fix: Auto-fix common issues then verify
run_auto_fix() {
    print_header "Running Auto-Fix"
    
    print_info "Applying automatic fixes..."
    ./gradlew "${GRADLE_OPTS[@]}" spotlessApply :nike-gradle-plugin:spotlessApply sortDependencies || true
    
    print_success "Auto-fix complete. Running verification..."
    echo ""
    
    run_prepush_checks
}

show_help() {
    cat << 'EOF'
Mamba Android Local Checks

Verify PRA operations locally before pushing.

Usage: ./local-checks.sh [MODE] [OPTIONS]

Modes:
  --prepush     Fast pre-push checks: spotless, detekt, apiCheck, lint (~30s)
  --fix         Auto-fix common issues then verify (~1min)
  --pra         Full PRA simulation - everything Jenkins runs (~15min)

Options:
  --json        Output JSON results (for programmatic use)
  --agent       Generate Goose prompt if issues found
  --help        Show this help

Examples:
  ./local-checks.sh --prepush          # Quick check before pushing
  ./local-checks.sh --fix              # Fix formatting/sorting issues
  ./local-checks.sh --prepush --agent  # Get Goose to fix failures
  ./local-checks.sh --pra              # Full CI simulation

What Each Mode Checks:
  --prepush:
    • spotlessCheck    - Code formatting
    • detekt           - Static analysis
    • apiCheck         - Binary compatibility
    • lint             - Android lint (excluding China variants)

  --pra:
    • All --prepush checks
    • checkSortDependencies
    • buildHealth (dependency analysis)
    • lint (Android lint)
    • test + jacocoCoverage (unit tests)
    • assembleWorld (build APKs)
    • :nike-gradle-plugin:spotlessCheck

Auto-Fix Commands:
  • Spotless:     ./gradlew spotlessApply
  • API changes:  ./gradlew apiDump
  • Dependencies: ./gradlew sortDependencies
  • Detekt:       Fix code directly (DO NOT use detektBaseline)
EOF
}

# =============================================================================
# MAIN
# =============================================================================

MODE=""
OUTPUT_JSON=false
SHOW_AGENT_PROMPT=false

for arg in "$@"; do
    case $arg in
        --prepush) MODE="prepush" ;;
        --fix) MODE="fix" ;;
        --pra) MODE="pra" ;;
        --json) OUTPUT_JSON=true ;;
        --agent) SHOW_AGENT_PROMPT=true ;;
        --help|-h) show_help; exit 0 ;;
        *) print_error "Unknown option: $arg"; show_help; exit 1 ;;
    esac
done

# Default to prepush if no mode specified
if [[ -z "${MODE}" ]]; then
    MODE="prepush"
fi

cd "${PROJECT_ROOT}"

if [[ ! -f "build.gradle.kts" ]]; then
    print_error "Not in mamba-android project root!"
    exit 1
fi

init_output

print_header "Mamba Android Local Checks"
print_info "Mode: ${MODE}"
print_info "Gradle opts: ${GRADLE_OPTS[*]}"

START_TIME=$(date +%s)

case $MODE in
    prepush) run_prepush_checks ;;
    fix) run_auto_fix ;;
    pra) run_full_pra ;;
esac

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

generate_result_json

if [[ "${OUTPUT_JSON}" == "true" ]]; then
    cat "${RESULT_FILE}"
else
    echo ""
    print_header "Summary"
    print_info "Total time: ${TOTAL_DURATION}s"
    
    if [[ "${OVERALL_SUCCESS}" == "true" ]]; then
        print_success "All checks passed!"
    else
        print_error "Some checks failed. See details above."
        
        if [[ "${SHOW_AGENT_PROMPT}" == "true" ]]; then
            generate_agent_prompt
        else
            echo ""
            print_info "Run with --agent flag to get Goose fix instructions"
            print_info "Or run: ./local-checks.sh --fix to auto-fix common issues"
        fi
    fi
    
    print_info "Full results: ${RESULT_FILE}"
fi

[[ "${OVERALL_SUCCESS}" == "true" ]] && exit 0 || exit 1
