#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos v4.0 Master Test Runner
# =============================================================================
# Usage: ./run_all_tests.sh [--with-live] [--skip-build] [--only <repo>] [--report <path>]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$(cd "$SCRIPT_DIR/../repos" && pwd)"
REPORTS_DIR="$SCRIPT_DIR/../reports"
LOGS_DIR="$REPORTS_DIR/logs"

WITH_LIVE=false
SKIP_BUILD=false
ONLY_REPO=""
REPORT_FILE="$REPORTS_DIR/test_report_$(date +%Y%m%d_%H%M%S).md"

# Generate RUN_ID (cross-platform)
RUN_ID="$(
  if command -v uuidgen >/dev/null 2>&1; then
    uuidgen | tr '[:upper:]' '[:lower:]'
  else
    python3 -c "import uuid; print(str(uuid.uuid4()))"
  fi
)"

GATEWAY_PID=""
DASHBOARD_PID=""
DB_PATH="/tmp/talos_test_${RUN_ID}.db"

# =============================================================================
# Usage
# =============================================================================
usage() {
  cat <<EOF
Talos v4.0 Master Test Runner

Usage: $0 [OPTIONS]

Options:
  --with-live      Start Gateway + Dashboard for live integration tests
  --skip-build     Skip build steps (useful for CI caching)
  --only <repo>    Test single repo only
  --report <path>  Custom report file path
  -h, --help       Show this help

Repos tested (in order):
  1. talos (root)
  2. talos-contracts
  3. talos-core-rs
  4. talos-sdk-py
  5. talos-sdk-ts
  6. talos-gateway
  7. talos-audit-service
  8. talos-mcp-connector
  9. talos-dashboard

EOF
}

# =============================================================================
# Parse arguments
# =============================================================================
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-live) WITH_LIVE=true; shift ;;
    --skip-build) SKIP_BUILD=true; shift ;;
    --only) ONLY_REPO="${2:-}"; shift 2 ;;
    --report) REPORT_FILE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

# =============================================================================
# Create directories
# =============================================================================
mkdir -p "$LOGS_DIR"

# =============================================================================
# Prerequisite checks
# =============================================================================
check_prereqs() {
  local missing=0
  echo "Checking prerequisites..."
  
  for bin in bash python3 node npm curl; do
    if command -v "$bin" >/dev/null 2>&1; then
      echo "  ✓ $bin"
    else
      echo "  ✗ Missing: $bin"
      missing=1
    fi
  done
  
  if command -v rg >/dev/null 2>&1; then
    echo "  ✓ rg (ripgrep)"
  else
    echo "  ⚠ Missing: rg (ripgrep) - boundary checks may skip"
  fi
  
  if command -v cargo >/dev/null 2>&1; then
    echo "  ✓ cargo (Rust toolchain)"
  else
    echo "  ⚠ Missing: cargo (Rust toolchain) - talos-core-rs will be skipped"
  fi
  
  [[ $missing -eq 0 ]] || { echo "Error: Missing required prerequisites"; exit 1; }
}

# =============================================================================
# Cleanup trap
# =============================================================================
cleanup() {
  echo ""
  echo "Cleaning up..."
  if [[ -n "${DASHBOARD_PID}" ]]; then
    kill "${DASHBOARD_PID}" 2>/dev/null || true
    echo "  Stopped Dashboard (PID: $DASHBOARD_PID)"
  fi
  if [[ -n "${GATEWAY_PID}" ]]; then
    kill "${GATEWAY_PID}" 2>/dev/null || true
    echo "  Stopped Gateway (PID: $GATEWAY_PID)"
  fi
  if [[ -f "$DB_PATH" ]]; then
    rm -f "$DB_PATH" 2>/dev/null || true
    echo "  Removed test DB: $DB_PATH"
  fi
}
trap cleanup EXIT INT TERM

# =============================================================================
# Wait for HTTP endpoint
# =============================================================================
wait_http_ok() {
  local url="$1"
  local tries="${2:-30}"
  local sleep_s="${3:-1}"
  for i in $(seq 1 "$tries"); do
    if curl -sf "$url" >/dev/null 2>&1; then
      return 0
    fi
    echo "  Waiting for $url... ($i/$tries)"
    sleep "$sleep_s"
  done
  return 1
}

# =============================================================================
# Repo list (contract-first order, including root)
# =============================================================================
REPOS=(
  "talos:$ROOT_DIR"
  "talos-contracts:$REPOS_DIR/talos-contracts"
  "talos-core-rs:$REPOS_DIR/talos-core-rs"
  "talos-sdk-py:$REPOS_DIR/talos-sdk-py"
  "talos-sdk-ts:$REPOS_DIR/talos-sdk-ts"
  "talos-gateway:$REPOS_DIR/talos-gateway"
  "talos-audit-service:$REPOS_DIR/talos-audit-service"
  "talos-mcp-connector:$REPOS_DIR/talos-mcp-connector"
  "talos-dashboard:$REPOS_DIR/talos-dashboard"
)

# =============================================================================
# Export shared environment
# =============================================================================
export TALOS_ENV="test"
export TALOS_RUN_ID="$RUN_ID"
export TALOS_DB_PATH="$DB_PATH"
if [[ "$SKIP_BUILD" == "true" ]]; then
  export TALOS_SKIP_BUILD="true"
fi

# =============================================================================
# Initialize report
# =============================================================================
{
  echo "# Talos v4.0 Test Report"
  echo ""
  echo "| Field | Value |"
  echo "|-------|-------|"
  echo "| RUN_ID | \`$RUN_ID\` |"
  echo "| Date | $(date -Iseconds) |"
  echo "| With Live | $WITH_LIVE |"
  echo "| Skip Build | $SKIP_BUILD |"
  echo ""
} > "$REPORT_FILE"

# =============================================================================
# Run prerequisite checks
# =============================================================================
check_prereqs

# =============================================================================
# Boundary gate (fast fail before repo tests)
# =============================================================================
echo ""
echo "=========================================="
echo "Running Boundary Gate..."
echo "=========================================="
{
  echo "## Boundary Gate"
  echo ""
} >> "$REPORT_FILE"

if [[ -f "$SCRIPT_DIR/check_boundaries.sh" ]]; then
  if bash "$SCRIPT_DIR/check_boundaries.sh" >"$LOGS_DIR/check_boundaries.log" 2>&1; then
    echo "  ✓ Boundary checks passed"
    echo "- check_boundaries: **PASS**" >> "$REPORT_FILE"
  else
    echo "  ✗ Boundary checks failed"
    echo "- check_boundaries: **FAIL**" >> "$REPORT_FILE"
    echo ""
    echo "Log tail:"
    tail -n 20 "$LOGS_DIR/check_boundaries.log" || true
    exit 1
  fi
else
  echo "  ⚠ check_boundaries.sh not found, skipping"
  echo "- check_boundaries: **SKIP** (script not found)" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# =============================================================================
# Run per-repo tests (aggregate failures, don't stop)
# =============================================================================
echo ""
echo "=========================================="
echo "Running Repo Tests..."
echo "=========================================="

overall_fail=0
{
  echo "## Repo Results"
  echo ""
  echo "| Repo | Status | Log |"
  echo "|------|--------|-----|"
} >> "$REPORT_FILE"

for entry in "${REPOS[@]}"; do
  repo="${entry%%:*}"
  repo_dir="${entry#*:}"
  
  # Skip if --only specified and doesn't match
  if [[ -n "$ONLY_REPO" && "$repo" != "$ONLY_REPO" ]]; then
    continue
  fi
  
  log_file="$LOGS_DIR/$repo.log"
  
  # Determine test script location
  if [[ "$repo" == "talos" ]]; then
    test_script="$repo_dir/scripts/test.sh"
  else
    test_script="$repo_dir/scripts/test.sh"
  fi
  
  echo ""
  echo "--- $repo ---"
  
  if [[ ! -f "$test_script" ]]; then
    echo "  ⚠ scripts/test.sh not found, skipping"
    echo "| $repo | **SKIP** | (no test.sh) |" >> "$REPORT_FILE"
    continue
  fi
  
  echo "  Running tests..."
  
  if (cd "$repo_dir" && bash "$test_script") >"$log_file" 2>&1; then
    echo "  ✓ PASS"
    echo "| $repo | ✅ PASS | [log](logs/$repo.log) |" >> "$REPORT_FILE"
  else
    echo "  ✗ FAIL"
    echo "| $repo | ❌ FAIL | [log](logs/$repo.log) |" >> "$REPORT_FILE"
    overall_fail=1
    echo "  Log tail:"
    tail -n 10 "$log_file" 2>/dev/null || true
  fi
done

echo "" >> "$REPORT_FILE"

# =============================================================================
# Live integration tests (opt-in only)
# =============================================================================
if [[ "$WITH_LIVE" == "true" ]]; then
  echo ""
  echo "=========================================="
  echo "Running Live Integration Tests..."
  echo "=========================================="
  
  {
    echo "## Live Integration"
    echo ""
  } >> "$REPORT_FILE"
  
  # Start Gateway (no pipe to tee - direct file redirect)
  echo "Starting Gateway..."
  (
    cd "$REPOS_DIR/talos-gateway"
    uvicorn main:app --port 8080 --host 127.0.0.1
  ) >"$LOGS_DIR/integration_gateway.log" 2>&1 &
  GATEWAY_PID=$!
  echo "  Gateway PID: $GATEWAY_PID"
  
  # Wait for Gateway readiness
  if wait_http_ok "http://localhost:8080/api/gateway/status" 45 1; then
    echo "  ✓ Gateway ready"
    echo "- gateway_ready: **PASS**" >> "$REPORT_FILE"
  else
    echo "  ✗ Gateway failed to start"
    echo "- gateway_ready: **FAIL**" >> "$REPORT_FILE"
    echo ""
    echo "Gateway log tail:"
    tail -n 40 "$LOGS_DIR/integration_gateway.log" || true
    exit 1
  fi
  
  # Start Dashboard
  echo "Starting Dashboard..."
  (
    cd "$REPOS_DIR/talos-dashboard"
    npm run dev -- --port 3000
  ) >"$LOGS_DIR/integration_dashboard.log" 2>&1 &
  DASHBOARD_PID=$!
  echo "  Dashboard PID: $DASHBOARD_PID"
  
  # Brief wait for Dashboard startup
  sleep 3
  echo "  ✓ Dashboard started"
  echo "- dashboard_started: **PASS**" >> "$REPORT_FILE"
  
  # Run integration script
  echo "Running integration tests..."
  if [[ -f "$SCRIPT_DIR/test_integration.sh" ]]; then
    if bash "$SCRIPT_DIR/test_integration.sh" >"$LOGS_DIR/test_integration.log" 2>&1; then
      echo "  ✓ Integration tests passed"
      echo "- integration: **PASS**" >> "$REPORT_FILE"
    else
      echo "  ✗ Integration tests failed"
      echo "- integration: **FAIL**" >> "$REPORT_FILE"
      echo ""
      echo "Integration log tail:"
      tail -n 40 "$LOGS_DIR/test_integration.log" || true
      overall_fail=1
    fi
  else
    echo "  ⚠ test_integration.sh not found"
    echo "- integration: **SKIP** (script not found)" >> "$REPORT_FILE"
  fi
  
  echo "" >> "$REPORT_FILE"
fi

# =============================================================================
# Final status
# =============================================================================
echo ""
echo "=========================================="
if [[ $overall_fail -ne 0 ]]; then
  echo "RESULT: FAILED"
  echo "See logs in: $LOGS_DIR"
  echo "See report: $REPORT_FILE"
  exit 1
else
  echo "RESULT: ALL CHECKS PASSED"
  echo "Report: $REPORT_FILE"
  exit 0
fi
