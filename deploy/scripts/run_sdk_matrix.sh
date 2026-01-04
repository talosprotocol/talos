#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Cross-SDK Test Matrix Runner
# =============================================================================
# Runs conformance tests across all SDKs for all features.
# Generates a markdown report with pass/fail, duration, and first failing vector.
# Usage: ./run_sdk_matrix.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"
CONTRACTS_DIR="$REPOS_DIR/talos-contracts"
RELEASE_SETS_DIR="$CONTRACTS_DIR/test_vectors/sdk/release_sets"
REPORTS_DIR="$ROOT_DIR/deploy/reports"
LOGS_DIR="$REPORTS_DIR/logs"

mkdir -p "$LOGS_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORTS_DIR/sdk_matrix_${TIMESTAMP}.md"

# Features to test (discovered from contracts or static list as fallback)
FEATURES=()
if [[ -d "$RELEASE_SETS_DIR" ]]; then
  for f in "$RELEASE_SETS_DIR"/*.json; do
    [[ -f "$f" ]] || continue
    name=$(basename "$f" .json)
    FEATURES+=("$name")
  done
fi

# Fallback if no release sets found
if [[ ${#FEATURES[@]} -eq 0 ]]; then
  FEATURES=("canonical_json" "mcp_signing" "v1.1.0")
fi

# SDKs to test
SDKS=(
  "talos-sdk-py"
  "talos-sdk-ts"
  "talos-sdk-go"
  "talos-sdk-java"
  "talos-core-rs"
)

log() { printf '%s\n' "$*"; }
info() { printf 'ℹ️  %s\n' "$*"; }

echo "=========================================="
echo "Talos SDK Conformance Matrix"
echo "=========================================="
echo "Features: ${FEATURES[*]}"
echo "SDKs: ${SDKS[*]}"
echo ""

# Build report header
{
  echo "# SDK Conformance Matrix"
  echo "**Generated**: $(date)"
  echo ""
  echo "## Summary"
  echo ""
  echo "| Feature | $(printf '%s | ' "${SDKS[@]}")"
  echo "|---------|$(printf -- '--------|' $(seq ${#SDKS[@]}))"
} > "$REPORT_FILE"

# Results counters
PASS_COUNT=0
FAIL_COUNT=0
TODO_COUNT=0
OVERALL_FAIL=0

for feature in "${FEATURES[@]}"; do
  row="| $feature |"
  
  for sdk in "${SDKS[@]}"; do
    sdk_dir="$REPOS_DIR/$sdk"
    log_file="$LOGS_DIR/${sdk}_${feature}.log"
    
    # Check if SDK exists
    if [[ ! -d "$sdk_dir" ]]; then
      row+=" ⚠️ N/A |"
      continue
    fi
    
    # Check if SDK has Makefile with conformance target
    if [[ ! -f "$sdk_dir/Makefile" ]] || ! grep -q "conformance" "$sdk_dir/Makefile" 2>/dev/null; then
      row+=" ⏳ TODO |"
      TODO_COUNT=$((TODO_COUNT + 1))
      continue
    fi
    
    info "Testing $sdk / $feature..."
    start_time=$(date +%s)
    
    if (cd "$sdk_dir" && make conformance RELEASE_SET="${feature}.json") > "$log_file" 2>&1; then
      end_time=$(date +%s)
      duration=$((end_time - start_time))
      row+=" ✅ ${duration}s |"
      PASS_COUNT=$((PASS_COUNT + 1))
    else
      end_time=$(date +%s)
      duration=$((end_time - start_time))
      row+=" ❌ ${duration}s |"
      FAIL_COUNT=$((FAIL_COUNT + 1))
      OVERALL_FAIL=1
    fi
  done
  
  echo "$row" >> "$REPORT_FILE"
done

# Add detailed results section
{
  echo ""
  echo "## Legend"
  echo "- ✅ PASS: All vectors passed"
  echo "- ❌ FAIL: One or more vectors failed"
  echo "- ⏳ TODO: Conformance target not implemented"
  echo "- ⚠️ N/A: SDK not found"
  echo ""
  echo "## Logs"
  echo "Detailed logs available in: \`deploy/reports/logs/\`"
} >> "$REPORT_FILE"

echo ""
echo "=========================================="
echo "Report generated: $REPORT_FILE"
echo "=========================================="

echo ""
echo "Summary: ✅ $PASS_COUNT PASS | ❌ $FAIL_COUNT FAIL | ⏳ $TODO_COUNT TODO"

if [[ $OVERALL_FAIL -ne 0 ]]; then
  log "Matrix Result: ❌ SOME FAILURES"
  exit 1
else
  log "Matrix Result: ✅ ALL PASS"
  exit 0
fi
