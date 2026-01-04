#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Operations Script Audit
# =============================================================================
# Enumerates all operational entrypoints (start, test, makefile) for each repo.
# Generates a report in deploy/reports/ops_script_inventory_<timestamp>.md.
# Fails if any repo lacks a canonical 'scripts/start.sh'.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"
REPORTS_DIR="$ROOT_DIR/deploy/reports"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
REPORT_FILE="$REPORTS_DIR/ops_script_inventory_${TIMESTAMP}.md"

mkdir -p "$REPORTS_DIR"

# Source common helpers
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

# Header
{
  echo "# Operations Script Inventory"
  echo "**Date**: $(date)"
  echo "**Run ID**: $TIMESTAMP"
  echo ""
  echo "| Repository | Canonical \`scripts/start.sh\` | Root \`start.sh\` | \`scripts/test.sh\` | Makefile Targets |"
  echo "|------------|--------------------------|-----------------|-------------------|------------------|"
} > "$REPORT_FILE"

overall_fail=0

for repo in "${COMMON_REPOS[@]}"; do
  repo_dir="$REPOS_DIR/$repo"
  
  if [[ ! -d "$repo_dir" ]]; then
    warn "Repo $repo not found at $repo_dir, skipping."
    continue
  fi

  # Check scripts
  has_canonical_start="❌"
  has_root_start="❌"
  has_test="❌"
  makefile_targets=""

  if [[ -f "$repo_dir/scripts/start.sh" ]]; then
    has_canonical_start="✅"
  fi

  if [[ -f "$repo_dir/start.sh" ]]; then
    has_root_start="✅"
  fi

  if [[ -f "$repo_dir/scripts/test.sh" ]]; then
    has_test="✅"
  fi

  if [[ -f "$repo_dir/Makefile" ]]; then
    # Extract PHONY targets or simple targets
    makefile_targets=$(grep -E "^[a-zA-Z0-9_-]+:" "$repo_dir/Makefile" | cut -d: -f1 | tr '\n' ', ' | sed 's/, $//')
    if [[ -z "$makefile_targets" ]]; then
        makefile_targets="(Makefile present but no obvious targets)"
    fi
  else
    makefile_targets="(no Makefile)"
  fi

  # Report row
  echo "| $repo | $has_canonical_start | $has_root_start | $has_test | $makefile_targets |" >> "$REPORT_FILE"

  # Validation logic
  if [[ "$has_canonical_start" == "❌" ]]; then
    error "$repo is missing canonical 'scripts/start.sh'"
    overall_fail=1
  fi
done

echo "" >> "$REPORT_FILE"
echo "## Summary" >> "$REPORT_FILE"

if [[ $overall_fail -ne 0 ]]; then
  echo "**Status**: ❌ FAILED - Missing canonical entrypoints." >> "$REPORT_FILE"
  log "Audit FAILED. See report: $REPORT_FILE"
  exit 1
else
  echo "**Status**: ✅ PASSED" >> "$REPORT_FILE"
  log "Audit PASSED. See report: $REPORT_FILE"
  exit 0
fi
