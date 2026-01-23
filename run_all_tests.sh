#!/usr/bin/env bash
# =============================================================================
# Talos Interop-Grade Test Orchestrator
# =============================================================================
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Defaults
MODE="unit"
CHANGED_ONLY=false
CHANGED_MODE="workspace"
KEEP_GOING=false
CI_BASE="origin/main"

show_help() {
    echo "Usage: ./run_all_tests.sh [options]"
    echo ""
    echo "Options:"
    echo "  --ci              Run standard CI suite (smoke + unit + coverage)"
    echo "  --full            Run everything (smoke + unit + integration + coverage)"
    echo "  --unit            Run unit tests (default)"
    echo "  --coverage        Run unit tests and generate coverage reports"
    echo "  --changed         Only run repos affected by recent changes"
    echo "  --changed-mode M  Discovery mode: staged | workspace | ci (default: workspace)"
    echo "  --keep-going      Continue running other repos even if one fails"
    echo "  --help            Show this help"
}

# Parse flags
while [[ $# -gt 0 ]]; do
    case $1 in
        --ci) MODE="ci"; shift ;;
        --full) MODE="full"; shift ;;
        --unit) MODE="unit"; shift ;;
        --coverage) MODE="coverage"; shift ;;
        --changed) CHANGED_ONLY=true; shift ;;
        --changed-mode) CHANGED_MODE="$2"; shift 2 ;;
        --keep-going) KEEP_GOING=true; shift ;;
        --help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# 1. Discover Manifests
echo "🔍 Discovering repos..."
MANIFEST_PATHS=()

# Search top-level components (e.g., ./core/.agent/test_manifest.yml)
# and components in deploy/repos/ (e.g., ./deploy/repos/sdk-go/.agent/test_manifest.yml)
while IFS= read -r -d '' file; do
    MANIFEST_PATHS+=("$file")
done < <(find . -maxdepth 5 -name "test_manifest.yml" -print0)

# Deduplicate and filter (in case MaxDepth 3 caught things it shouldn't)
MANIFESTS=()
for p in "${MANIFEST_PATHS[@]}"; do
    # Only allow manifests that are in a .agent directory
    if [[ "$p" != *"/.agent/test_manifest.yml" ]]; then continue; fi
    # Exclude known noisy directories or submodules nested deep
    if [[ "$p" == *"/node_modules/"* || "$p" == *"/submodules/"* || "$p" == *"/target/"* ]]; then
        continue
    fi
    MANIFESTS+=("$p")
done

if [[ ${#MANIFESTS[@]} -eq 0 ]]; then
    echo "❌ No test manifests found."
    exit 1
fi

# 2. Filter by changes if requested
RUN_REPOS=()
if [[ "$CHANGED_ONLY" == "true" ]]; then
    echo "🎯 Filter: Changed files ($CHANGED_MODE)"
    DIFF_FILES=""
    case $CHANGED_MODE in
        staged)
            DIFF_FILES=$(git diff --cached --name-only)
            ;;
        workspace)
            DIFF_FILES=$(git diff HEAD --name-only; git ls-files --others --exclude-standard)
            ;;
        ci)
            BASE=$(git merge-base "$CI_BASE" HEAD 2>/dev/null || echo "main")
            DIFF_FILES=$(git diff "$BASE" --name-only)
            ;;
    esac

    for m in "${MANIFESTS[@]}"; do
        # dirname m is .agent, dirname dirname is repo_dir
        # We need relative path from root
        REPO_DIR=$(dirname "$(dirname "$m")" | sed 's|^\./||')
        # Check if any changed file starts with REPO_DIR (prefix match)
        # Using grep -E and anchoring to start of line to avoid partial matches like 'core' matching 'core-sdk'
        if echo "$DIFF_FILES" | grep -Eq "^$REPO_DIR(/|$)"; then
            RUN_REPOS+=("$m")
        fi
    done
    
    if [[ ${#RUN_REPOS[@]} -eq 0 ]]; then
        echo "✅ No repos affected by changes. Skipping."
        exit 0
    fi
else
    RUN_REPOS=("${MANIFESTS[@]}")
fi

# 3. Execution
echo "🚀 Running tests for ${#RUN_REPOS[@]} repos..."
FAILED_REPOS=()

for m in "${RUN_REPOS[@]}"; do
    REPO_DIR=$(dirname "$(dirname "$m")")
    # Extract repo_id from manifest
    REPO_ID=$(grep "repo_id:" "$m" | awk -F'"' '{print $2}' | sed 's/ //g')
    [[ -z "$REPO_ID" ]] && REPO_ID=$(basename "$REPO_DIR")

    echo -e "\n📦 [$REPO_ID] ($REPO_DIR)"
    
    TEST_CMD=""
    case $MODE in
        ci) TEST_CMD="--ci" ;;
        full) TEST_CMD="--full" ;;
        unit) TEST_CMD="--unit" ;;
        coverage) TEST_CMD="--coverage" ;;
    esac

    (cd "$REPO_DIR" && bash scripts/test.sh "$TEST_CMD")
    EXIT_CODE=$?

    if [[ $EXIT_CODE -ne 0 ]]; then
        echo "❌ [$REPO_ID] Failed with exit code $EXIT_CODE"
        FAILED_REPOS+=("$REPO_ID")
        [[ "$KEEP_GOING" == "false" ]] && break
    else
        echo "✅ [$REPO_ID] Passed"
    fi
done

# 4. Coverage Coordination
if [[ "$MODE" == "ci" || "$MODE" == "full" || "$MODE" == "coverage" ]]; then
    echo -e "\n📊 Enforcing coverage thresholds..."
    REPO_IDS_STR=""
    for m in "${RUN_REPOS[@]}"; do
        RID=$(grep "repo_id:" "$m" | awk -F'"' '{print $2}' | sed 's/ //g')
        REPO_IDS_STR="$REPO_IDS_STR $RID"
    done
    
    python3 scripts/coverage_coordinator.py --repos $REPO_IDS_STR
    EXIT_CODE=$?
    if [[ $EXIT_CODE -ne 0 ]]; then
        echo "❌ Coverage validation failed."
        exit 1
    fi
fi

# 5. Final Result
if [[ ${#FAILED_REPOS[@]} -gt 0 ]]; then
    echo -e "\n❌ Some tests failed: ${FAILED_REPOS[*]}"
    exit 1
fi

echo -e "\n✨ All tests passed!"
exit 0
