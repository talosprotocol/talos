#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Boundary Purity Gate
# =============================================================================
# Fails if consumer repos re-implement contract logic or use forbidden patterns.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOS_DIR="$(cd "$SCRIPT_DIR/../repos" && pwd)"
VIOLATIONS=0

echo "Running boundary purity checks..."
echo ""

# =============================================================================
# Helper: Check for forbidden patterns in repo
# =============================================================================
check_no_pattern() {
  local repo="$1"
  local pattern="$2"
  local scope="$3"
  local description="$4"
  
  local target_dir="$REPOS_DIR/$repo/$scope"
  
  if [[ ! -d "$target_dir" ]]; then
    return 0
  fi
  
  if rg -q --hidden --no-ignore -S \
    --glob '!**/node_modules/**' \
    --glob '!**/dist/**' \
    --glob '!**/build/**' \
    --glob '!**/out/**' \
    --glob '!**/.next/**' \
    --glob '!**/.venv/**' \
    --glob '!**/venv/**' \
    --glob '!**/tests/**' \
    --glob '!**/__tests__/**' \
    --glob '!**/test/**' \
    --glob '!**/*.test.*' \
    --glob '!**/*.spec.*' \
    --glob '!**/.github/**' \
    --glob '!**/scripts/**' \
    --glob '!**/docs/**' \
    "$pattern" "$target_dir" 2>/dev/null; then
    echo "  ✗ VIOLATION: $repo - $description"
    rg -n --hidden --no-ignore -S \
      --glob '!**/node_modules/**' \
      --glob '!**/dist/**' \
      --glob '!**/build/**' \
      --glob '!**/out/**' \
      --glob '!**/.next/**' \
      --glob '!**/.venv/**' \
      --glob '!**/venv/**' \
      --glob '!**/tests/**' \
      --glob '!**/__tests__/**' \
      --glob '!**/test/**' \
      --glob '!**/*.test.*' \
      --glob '!**/*.spec.*' \
      "$pattern" "$target_dir" 2>/dev/null | head -5 || true
    VIOLATIONS=$((VIOLATIONS + 1))
  fi
}

# =============================================================================
# Check 1: Contract logic duplication (definitions, not imports)
# =============================================================================
echo "1) Checking for contract logic duplication..."

# Python repos - check for derive_cursor definition
check_no_pattern "talos-gateway" '^\s*def\s+derive_cursor\s*\(' "." \
  "Re-implements derive_cursor (should import from talos_contracts)"

check_no_pattern "talos-mcp-connector" '^\s*def\s+derive_cursor\s*\(' "." \
  "Re-implements derive_cursor (should import from talos_contracts)"

check_no_pattern "talos-audit-service" '^\s*def\s+derive_cursor\s*\(' "." \
  "Re-implements derive_cursor (should import from talos_contracts)"

# TypeScript repos - check for deriveCursor function definition
check_no_pattern "talos-dashboard" 'function\s+deriveCursor\s*\(' "src" \
  "Re-implements deriveCursor (should import from @talosprotocol/contracts)"

check_no_pattern "talos-sdk-ts" 'function\s+deriveCursor\s*\(' "packages" \
  "Re-implements deriveCursor (should import from @talosprotocol/contracts)"

# =============================================================================
# Check 2: Browser encoding footguns (btoa/atob)
# =============================================================================
echo "2) Checking for browser encoding footguns..."

check_no_pattern "talos-dashboard" '\bbtoa\s*\(|\batob\s*\(' "src" \
  "Uses btoa/atob (should use contracts base64url)"

check_no_pattern "talos-sdk-ts" '\bbtoa\s*\(|\batob\s*\(' "packages" \
  "Uses btoa/atob (should use contracts base64url)"

# =============================================================================
# Check 3: Deep links and cross-repo imports
# =============================================================================
echo "3) Checking for deep links..."

check_no_pattern "talos-dashboard" 'file:///' "." \
  "Has file:// deep links"

check_no_pattern "talos-gateway" 'file:///' "." \
  "Has file:// deep links"

check_no_pattern "talos-dashboard" '\.\.\/\.\.\/talos\/' "." \
  "Has cross-repo relative imports"

check_no_pattern "talos-gateway" '\.\.\/\.\.\/talos\/' "." \
  "Has cross-repo relative imports"

# =============================================================================
# Result
# =============================================================================
echo ""
if [[ $VIOLATIONS -gt 0 ]]; then
  echo "=========================================="
  echo "FAILED: $VIOLATIONS boundary violation(s) found"
  echo "=========================================="
  exit 1
fi

echo "=========================================="
echo "PASS: No boundary violations"
echo "=========================================="
exit 0
