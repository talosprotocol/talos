#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Stop All Services
# =============================================================================
# Stops all running Talos services without cleaning build artifacts.
# Use cleanup_all.sh to also remove dependencies.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

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
echo "Talos Protocol - Stop All Services"
echo "=========================================="
echo ""

stopped=0
not_running=0

# Stop services via PID files
for name in "${SERVICE_PIDS[@]}"; do
    pid_file="/tmp/${name}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "  ✓ Stopped $name (PID: $pid)"
            ((stopped++))
        else
            echo "  - $name not running (stale PID file)"
            ((not_running++))
        fi
        rm -f "$pid_file"
    else
        echo "  - $name not running"
        ((not_running++))
    fi
    rm -f "/tmp/${name}.log"
done

echo ""

# Kill any lingering processes
log_info "Checking for lingering processes..."

# Gateway (uvicorn)
if pkill -f "uvicorn main:app" 2>/dev/null; then
    echo "  ✓ Killed lingering uvicorn processes"
fi

# Dashboard (next dev)
if pkill -f "next dev" 2>/dev/null; then
    echo "  ✓ Killed lingering Next.js dev processes"
fi

# MCP connector
if pkill -f "talos-mcp-connector" 2>/dev/null; then
    echo "  ✓ Killed lingering MCP connector processes"
fi

echo ""
echo "=========================================="
echo "Stop Complete"
echo "=========================================="
echo ""
echo "Stopped: $stopped services"
echo "Not running: $not_running services"
echo ""
echo "To restart: ./deploy/scripts/start_all.sh"
