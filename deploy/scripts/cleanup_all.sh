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

# All repos
REPOS=(
    talos-contracts
    talos-core-rs
    talos-sdk-py
    talos-sdk-ts
    talos-gateway
    talos-audit-service
    talos-mcp-connector
    talos-dashboard
)

# Service PID files
SERVICE_PIDS=(
    talos-gateway
    talos-audit-service
    talos-mcp-connector
    talos-dashboard
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

echo "=========================================="
echo "Talos Protocol - Cleanup All"
echo "=========================================="
echo ""

# =============================================================================
# 1. Stop all services
# =============================================================================
log_info "Stopping all services..."

for name in "${SERVICE_PIDS[@]}"; do
    pid_file="/tmp/${name}.pid"
    if [ -f "$pid_file" ]; then
        kill "$(cat "$pid_file")" 2>/dev/null || true
        rm -f "$pid_file"
        echo "  Stopped $name"
    fi
    rm -f "/tmp/${name}.log"
done

# Kill any lingering processes
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

log_info "All services stopped"
echo ""

# =============================================================================
# 2. Clean each repo
# =============================================================================
log_info "Cleaning repositories..."

for repo in "${REPOS[@]}"; do
    repo_dir="$REPOS_DIR/$repo"
    cleanup_script="$repo_dir/scripts/cleanup.sh"
    
    if [ -f "$cleanup_script" ]; then
        bash "$cleanup_script"
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
log_info "Cleaning root project..."
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
log_info "Cleaning temp files..."
rm -f /tmp/talos-*.pid /tmp/talos-*.log 2>/dev/null || true

echo ""
echo "=========================================="
echo "Cleanup Complete"
echo "=========================================="
echo ""
echo "All repositories are now source-only."
echo "Ready for fresh build with: ./deploy/scripts/start_all.sh"
