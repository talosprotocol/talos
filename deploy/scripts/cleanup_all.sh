#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Cleanup All
# =============================================================================
# Stops all services and removes all dependencies.
# Leaves only source code ready to be built again.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOS_DIR="$(cd "$SCRIPT_DIR/../repos" && pwd)"

# Source common helpers
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

echo "=========================================="
echo "Talos Protocol - Cleanup All"
echo "=========================================="
echo ""

# =============================================================================
# 1. Stop all services
# =============================================================================
info "Stopping all services via stop_all.sh..."
"$SCRIPT_DIR/stop_all.sh"

# Kill any lingering processes that scripts might not track
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

info "All services stopped"
echo ""

# =============================================================================
# 2. Clean each repo
# =============================================================================
info "Cleaning repositories..."

for repo in "${COMMON_REPOS[@]}"; do
    repo_dir="$REPOS_DIR/$repo"
    cleanup_script="$repo_dir/scripts/cleanup.sh"
    
    if [ -f "$cleanup_script" ]; then
        echo "  Cleaning $repo (script)..."
        (cd "$repo_dir" && bash "scripts/cleanup.sh")
    else
        # Fallback: manual cleanup
        echo "  Cleaning $repo (manual)..."
        (
            cd "$repo_dir"
            
            # Node.js
            rm -rf node_modules .next out dist build coverage .eslintcache .turbo 2>/dev/null || true
            
            # Python
            rm -rf *.egg-info .venv venv .pytest_cache .ruff_cache __pycache__ 2>/dev/null || true
            find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
            find . -name "*.pyc" -delete 2>/dev/null || true
            
            # Rust
            rm -rf target 2>/dev/null || true
        )
        echo "  ✓ $repo cleaned"
    fi
done

# =============================================================================
# 3. Clean root project
# =============================================================================
info "Cleaning root project..."
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
(
    cd "$ROOT_DIR"
    rm -rf .venv venv .pytest_cache .ruff_cache __pycache__ 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
)
echo "  ✓ Root project cleaned"

# =============================================================================
# 4. Clean temp files
# =============================================================================
info "Cleaning temp files..."
rm -f /tmp/talos-*.pid /tmp/talos-*.log 2>/dev/null || true

echo ""
echo "=========================================="
echo "Cleanup Complete"
echo "=========================================="
echo ""
echo "All repositories are now source-only."
echo "Ready for fresh build with: ./deploy/scripts/start_all.sh"
