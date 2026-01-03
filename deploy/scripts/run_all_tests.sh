#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Master Test Runner
# =============================================================================
# Runs tests across all repositories using canonical entrypoints.
# Usage: ./run_all_tests.sh [--with-live] [--skip-build] [--only <repo>]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"
REPORTS_DIR="$ROOT_DIR/deploy/reports"
LOGS_DIR="$REPORTS_DIR/logs"

mkdir -p "$LOGS_DIR"

# Defaults
WITH_LIVE=false
SKIP_BUILD=false
ONLY_REPO=""
REPORT_FILE="$REPORTS_DIR/test_report_$(date +%Y%m%d_%H%M%S).md"
RUN_ID="$(date +%Y%m%d_%H%M%S)"

log() { printf '%s\n' "$*"; }
info() { printf 'ℹ️  %s\n' "$*"; }
warn() { printf '⚠  %s\n' "$*"; }
error() { printf '✖  %s\n' "$*" >&2; }

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-live) WITH_LIVE=true; shift ;;
    --skip-build) SKIP_BUILD=true; shift ;;
    --only) ONLY_REPO="${2:-}"; shift 2 ;;
    --report) REPORT_FILE="${2:-}"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

export TALOS_ENV="test"
export TALOS_RUN_ID="$RUN_ID"
export TALOS_SKIP_BUILD="$SKIP_BUILD"

{
  echo "# Test Report ($RUN_ID)"
  echo "**Date**: $(date)"
  echo "**With Live**: $WITH_LIVE"
  echo ""
  echo "| Repository | Status | Test Script | Log |"
  echo "|------------|--------|-------------|-----|"
} > "$REPORT_FILE"

REPOS=(
  "talos-contracts"
  "talos-core-rs"
  "talos-sdk-py"
  "talos-sdk-ts"
  "talos-gateway"
  "talos-audit-service"
  "talos-mcp-connector"
  "talos-dashboard"
)

overall_fail=0

run_test() {
    local repo="$1"
    local repo_dir="$REPOS_DIR/$repo"
    local test_script="$repo_dir/scripts/test.sh"
    local log_file="$LOGS_DIR/$repo.test.log"

    if [[ -n "$ONLY_REPO" && "$repo" != "$ONLY_REPO" ]]; then
        return 0
    fi

    echo "Running tests for $repo..."
    
    if [[ ! -f "$test_script" ]]; then
        warn "Test script missing: $test_script"
        echo "| $repo | ⚠️ SKIP | Missing Script | -" >> "$REPORT_FILE"
        return 0
    fi

    if (cd "$repo_dir" && bash "$test_script") > "$log_file" 2>&1; then
        info "✓ $repo passed"
        echo "| $repo | ✅ PASS | \`scripts/test.sh\` | [View Log](logs/$(basename "$log_file")) |" >> "$REPORT_FILE"
    else
        error "✗ $repo failed"
        echo "| $repo | ❌ FAIL | \`scripts/test.sh\` | [View Log](logs/$(basename "$log_file")) |" >> "$REPORT_FILE"
        overall_fail=1
    fi
}

# 1. Run Unit Tests
info "== Unit Tests =="
for repo in "${REPOS[@]}"; do
    run_test "$repo"
done

# 2. Live Integration Tests
if [[ "$WITH_LIVE" == "true" ]]; then
    info "== Live Integration =="
    echo "" >> "$REPORT_FILE"
    echo "## Live Integration" >> "$REPORT_FILE"
    
    # We assume stop_all.sh and start_all.sh are available
    info "Restarting services..."
    "$SCRIPT_DIR/stop_all.sh"
    "$SCRIPT_DIR/start_all.sh"
    
    # Run integration checks (if any specific script exists)
    # For now, we assume simple health checks in start_all are sufficient for "setup" validation
    # Real integration tests would go here.
    
    if "$SCRIPT_DIR/test_integration.sh" > "$LOGS_DIR/integration.log" 2>&1; then
        info "✓ Integration tests passed"
        echo "- Integration Tests: ✅ PASS" >> "$REPORT_FILE"
    else
        error "Integration tests failed"
        echo "- Integration Tests: ❌ FAIL" >> "$REPORT_FILE"
        overall_fail=1
    fi
    
    # Cleanup
    "$SCRIPT_DIR/stop_all.sh"
fi

echo ""
if [[ $overall_fail -ne 0 ]]; then
    log "Final Result: ❌ FAILED"
    exit 1
else
    log "Final Result: ✅ PASSED"
    exit 0
fi
