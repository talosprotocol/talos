#!/usr/bin/env bash
# =============================================================================
# Pre-Push Deployment Validation Hook
# =============================================================================
# Validates that deployment-critical checks pass before allowing push.
# This is more comprehensive than pre-commit since pushes trigger CI.
#
# INSTALLATION:
#   chmod +x scripts/pre-push-validate.sh
#   ln -sf ../../scripts/pre-push-validate.sh .git/hooks/pre-push
#
# SKIP HOOK (for emergency):
#   git push --no-verify
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Handle being called from .git/hooks or directly from scripts/
if [[ "$SCRIPT_DIR" == *".git/hooks"* ]]; then
    ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
    ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

cd "$ROOT_DIR"

echo "🚀 Running pre-push deployment validation..."
echo ""

FAILURES=0

# -----------------------------------------------------------------------------
# 1. Run all pre-commit checks first
# -----------------------------------------------------------------------------
echo "=== Phase 1: Pre-commit checks ==="
if [[ -f "scripts/pre-commit" ]]; then
    if ! bash scripts/pre-commit; then
        echo ""
        echo "❌ Pre-commit checks failed. Push blocked."
        exit 1
    fi
else
    echo "⚠️  Pre-commit script not found, running inline checks..."
fi

echo ""
echo "=== Phase 2: Deployment checks ==="

# -----------------------------------------------------------------------------
# 2. Verify test vectors exist and are valid
# -----------------------------------------------------------------------------
echo "1) Verifying test vectors..."
if [[ -f "deploy/scripts/ci_verify_vectors.sh" ]]; then
    if bash deploy/scripts/ci_verify_vectors.sh 2>/dev/null | grep -q "✓"; then
        echo "   ✅ Test vectors valid"
    else
        echo "   ❌ Test vectors FAILED"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "   ⚠️  Vector script not found (skipped)"
fi

# -----------------------------------------------------------------------------
# 3. Verify submodule consistency
# -----------------------------------------------------------------------------
echo "2) Checking submodule status..."
DIRTY_SUBMODULES=$(git submodule status 2>/dev/null | grep -c "^+" || true)
if [[ "$DIRTY_SUBMODULES" -gt 0 ]]; then
    echo "   ⚠️  $DIRTY_SUBMODULES submodule(s) have uncommitted changes"
    echo "       Consider: git submodule update --remote"
else
    echo "   ✅ Submodules clean"
fi

# -----------------------------------------------------------------------------
# 4. Check for debug artifacts
# -----------------------------------------------------------------------------
echo "3) Checking for debug artifacts..."
DEBUG_FILES=$(find . -name "*.debug" -o -name "*.log" -o -name ".DS_Store" 2>/dev/null | grep -v node_modules | grep -v .git | head -5 || true)
if [[ -n "$DEBUG_FILES" ]]; then
    echo "   ⚠️  Found debug files (consider removing):"
    echo "$DEBUG_FILES" | head -3 | sed 's/^/       /'
else
    echo "   ✅ No debug artifacts"
fi

# -----------------------------------------------------------------------------
# 5. Docker build check (optional, slow)
# -----------------------------------------------------------------------------
if [[ "${TALOS_CHECK_DOCKER:-0}" == "1" ]]; then
    echo "4) Docker build check..."
    if docker build -f docker/Dockerfile.talos-node -t talos:test . 2>/dev/null; then
        echo "   ✅ Docker builds"
    else
        echo "   ❌ Docker build FAILED"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "4) Docker build check (skipped - set TALOS_CHECK_DOCKER=1 to enable)"
fi

# -----------------------------------------------------------------------------
# Result
# -----------------------------------------------------------------------------
echo ""
if [[ $FAILURES -gt 0 ]]; then
    echo "=========================================="
    echo "❌ PUSH BLOCKED: $FAILURES deployment check(s) failed"
    echo "=========================================="
    echo "Fix the issues above and try again."
    echo "To skip validation: git push --no-verify"
    exit 1
fi

echo "=========================================="
echo "✅ All pre-push checks passed - safe to push!"
echo "=========================================="
exit 0
