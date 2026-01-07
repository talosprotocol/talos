#!/usr/bin/env bash
# =============================================================================
# Pre-Commit Build Validation Hook
# =============================================================================
# Validates that critical builds pass before allowing commit.
# Install: ln -sf ../../scripts/pre-commit-validate.sh .git/hooks/pre-commit
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔍 Running pre-commit build validation..."
echo ""

FAILURES=0

# -----------------------------------------------------------------------------
# 1. TypeScript Contracts Tests
# -----------------------------------------------------------------------------
echo "1) Testing talos-contracts/typescript..."
cd "$ROOT_DIR/deploy/repos/talos-contracts/typescript"
if npm test --silent 2>/dev/null | grep -q "passed"; then
    echo "   ✅ Contracts tests pass"
else
    echo "   ❌ Contracts tests FAILED"
    FAILURES=$((FAILURES + 1))
fi

# -----------------------------------------------------------------------------
# 2. Dashboard Build
# -----------------------------------------------------------------------------
echo "2) Building talos-dashboard..."
cd "$ROOT_DIR/deploy/repos/talos-dashboard"
if npm run build --silent 2>/dev/null | grep -q "Compiled successfully"; then
    echo "   ✅ Dashboard builds"
else
    echo "   ❌ Dashboard build FAILED"
    FAILURES=$((FAILURES + 1))
fi

# -----------------------------------------------------------------------------
# 3. Site Build
# -----------------------------------------------------------------------------
echo "3) Building talos-site..."
cd "$ROOT_DIR/deploy/repos/talos-site"
if npm run build --silent 2>/dev/null | grep -q "Compiled successfully"; then
    echo "   ✅ Site builds"
else
    echo "   ❌ Site build FAILED"
    FAILURES=$((FAILURES + 1))
fi

# -----------------------------------------------------------------------------
# 4. Boundary Purity Check
# -----------------------------------------------------------------------------
echo "4) Checking contract boundaries..."
cd "$ROOT_DIR"
if bash deploy/scripts/check_boundaries.sh 2>/dev/null | grep -q "PASS"; then
    echo "   ✅ Boundary check passes"
else
    echo "   ❌ Boundary check FAILED"
    FAILURES=$((FAILURES + 1))
fi

# -----------------------------------------------------------------------------
# Result
# -----------------------------------------------------------------------------
echo ""
if [[ $FAILURES -gt 0 ]]; then
    echo "=========================================="
    echo "❌ COMMIT BLOCKED: $FAILURES build failure(s)"
    echo "=========================================="
    echo "Fix the issues above and try again."
    exit 1
fi

echo "=========================================="
echo "✅ All pre-commit checks passed"
echo "=========================================="
exit 0
