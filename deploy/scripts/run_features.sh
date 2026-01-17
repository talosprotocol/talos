#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Feature-Specific Test Runner (Contract-Driven)
# =============================================================================
# Discovers features from contracts release sets and runs conformance tests.
# Usage: ./run_features.sh <feature>
# Features: ratchet, canonical-json, mcp-signing
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONTRACTS_DIR="$ROOT_DIR/contracts"
RELEASE_SETS_DIR="$CONTRACTS_DIR/test_vectors/sdk/release_sets"
REPORTS_DIR="$ROOT_DIR/deploy/reports"
LOGS_DIR="$REPORTS_DIR/logs"

mkdir -p "$LOGS_DIR"

# Feature to release set mapping
declare -A FEATURE_MAP=(
  ["ratchet"]="v1.1.0.json"
  ["canonical-json"]="canonical_json.json"
  ["mcp-signing"]="mcp_signing.json"
)

# SDKs that support conformance testing
CONFORMANCE_SDKS=(
  "talos-sdk-py"
  "talos-sdk-ts"
  "talos-sdk-go"
  "talos-sdk-java"
)

log() { printf '%s\n' "$*"; }
info() { printf 'ℹ️  %s\n' "$*"; }
warn() { printf '⚠  %s\n' "$*"; }
error() { printf '✖  %s\n' "$*" >&2; }

usage() {
  echo "Usage: $0 <feature>"
  echo ""
  echo "Available features:"
  for feature in "${!FEATURE_MAP[@]}"; do
    echo "  - $feature → ${FEATURE_MAP[$feature]}"
  done
  echo ""
  echo "Discovers from: $RELEASE_SETS_DIR"
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

FEATURE="$1"

# Validate feature
if [[ -z "${FEATURE_MAP[$FEATURE]:-}" ]]; then
  error "Unknown feature: $FEATURE"
  echo ""
  echo "Available features:"
  for f in "${!FEATURE_MAP[@]}"; do
    echo "  - $f"
  done
  exit 1
fi

RELEASE_SET="${FEATURE_MAP[$FEATURE]}"
RELEASE_SET_PATH="$RELEASE_SETS_DIR/$RELEASE_SET"

# Check if release set exists
if [[ ! -f "$RELEASE_SET_PATH" ]]; then
  warn "Release set not found: $RELEASE_SET_PATH"
  warn "Feature '$FEATURE' may not have vectors yet."
  # Create placeholder directory if needed
  mkdir -p "$RELEASE_SETS_DIR"
fi

echo "=========================================="
echo "Talos Feature Test: $FEATURE"
echo "=========================================="
echo "Release Set: $RELEASE_SET"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORTS_DIR/feature_${FEATURE}_${TIMESTAMP}.md"

{
  echo "# Feature Test Report: $FEATURE"
  echo "**Date**: $(date)"
  echo "**Release Set**: $RELEASE_SET"
  echo ""
  echo "| SDK | Status | Duration | Notes |"
  echo "|-----|--------|----------|-------|"
} > "$REPORT_FILE"

overall_fail=0

for sdk in "${CONFORMANCE_SDKS[@]}"; do
  sdk_path=$(python3 "$ROOT_DIR/deploy/submodules.py" --name "$sdk" --field new_path) || {
      warn "Skipping $sdk (path not found)"
      continue
  }
  sdk_dir="$ROOT_DIR/$sdk_path"
  log_file="$LOGS_DIR/${sdk}_${FEATURE}.log"
  
  if [[ ! -d "$sdk_dir" ]]; then
    warn "$sdk: Not found"
    echo "| $sdk | ⚠️ SKIP | - | Not found |" >> "$REPORT_FILE"
    continue
  fi
  
  # Check if SDK has conformance target
  if ! grep -q "conformance" "$sdk_dir/Makefile" 2>/dev/null; then
    warn "$sdk: No conformance target in Makefile"
    echo "| $sdk | ⚠️ SKIP | - | No conformance target |" >> "$REPORT_FILE"
    continue
  fi
  
  info "Running $FEATURE conformance for $sdk..."
  start_time=$(date +%s)
  
  if (cd "$sdk_dir" && make conformance RELEASE_SET="$RELEASE_SET") > "$log_file" 2>&1; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    info "✓ $sdk passed (${duration}s)"
    echo "| $sdk | ✅ PASS | ${duration}s | - |" >> "$REPORT_FILE"
  else
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    error "✗ $sdk failed (${duration}s)"
    # Extract first error from log
    first_error=$(grep -m1 "FAIL\|Error\|error:" "$log_file" 2>/dev/null || echo "See log")
    echo "| $sdk | ❌ FAIL | ${duration}s | ${first_error:0:50} |" >> "$REPORT_FILE"
    overall_fail=1
  fi
done

# Run interop if feature is ratchet
if [[ "$FEATURE" == "ratchet" && "${RUN_INTEROP:-1}" == "1" ]]; then
  echo ""
  info "Running interop tests..."
  interop_log="$LOGS_DIR/interop_${FEATURE}.log"
  
  if (cd "$CONTRACTS_DIR" && REPOS_DIR="$REPOS_DIR" make interop) > "$interop_log" 2>&1; then
    info "✓ Interop passed"
    echo "" >> "$REPORT_FILE"
    echo "## Interop" >> "$REPORT_FILE"
    echo "- Status: ✅ PASS" >> "$REPORT_FILE"
  else
    error "✗ Interop failed"
    echo "" >> "$REPORT_FILE"
    echo "## Interop" >> "$REPORT_FILE"
    echo "- Status: ❌ FAIL" >> "$REPORT_FILE"
    overall_fail=1
  fi
fi

echo ""
echo "Report: $REPORT_FILE"
echo ""

if [[ $overall_fail -ne 0 ]]; then
  log "Feature Test Result: ❌ FAILED"
  exit 1
else
  log "Feature Test Result: ✅ PASSED"
  exit 0
fi
