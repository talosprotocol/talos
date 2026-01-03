#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Stop All Services
# =============================================================================
# Stops all running Talos services without cleaning build artifacts.
# Use cleanup_all.sh to also remove dependencies.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Named service PID files (from start_all.sh)
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

# =============================================================================
# 1. Stop services via PID files
# =============================================================================
log_info "Stopping services via PID files..."

for name in "${SERVICE_PIDS[@]}"; do
    pid_file="/tmp/${name}.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "  ✓ Stopped $name (PID: $pid)"
            ((stopped++)) || true
        else
            echo "  - $name not running (stale PID file)"
            ((not_running++)) || true
        fi
        rm -f "$pid_file"
    else
        echo "  - $name (no PID file)"
        ((not_running++)) || true
    fi
    rm -f "/tmp/${name}.log"
done

echo ""

# =============================================================================
# 2. Kill all Talos-related processes by pattern
# =============================================================================
log_info "Stopping all Talos processes by pattern..."

# Gateway (uvicorn on various ports)
if pkill -f "uvicorn.*main:app" 2>/dev/null; then
    echo "  ✓ Killed uvicorn (Gateway) processes"
    ((stopped++)) || true
fi

# Audit Service (FastAPI)
if pkill -f "talos-audit-service" 2>/dev/null; then
    echo "  ✓ Killed Audit Service processes"
    ((stopped++)) || true
fi

# MCP Connector
if pkill -f "talos-mcp-connector" 2>/dev/null; then
    echo "  ✓ Killed MCP Connector processes"
    ((stopped++)) || true
fi

# Dashboard (Next.js dev server)
if pkill -f "next dev" 2>/dev/null; then
    echo "  ✓ Killed Next.js dev server processes"
    ((stopped++)) || true
fi

# Traffic generator
if pkill -f "traffic_gen.py" 2>/dev/null; then
    echo "  ✓ Killed traffic generator processes"
    ((stopped++)) || true
fi

# Any Python process in talos-gateway directory
if pkill -f "talos-gateway.*python" 2>/dev/null; then
    echo "  ✓ Killed Gateway Python processes"
    ((stopped++)) || true
fi

# Any Python uvicorn running on typical Talos ports
for port in 8000 8080 8081 8082 8083 3000 3001; do
    if lsof -ti :$port >/dev/null 2>&1; then
        lsof -ti :$port | xargs kill 2>/dev/null || true
        echo "  ✓ Killed process on port $port"
        ((stopped++)) || true
    fi
done

echo ""

# =============================================================================
# 3. Clean up any stale temp files
# =============================================================================
log_info "Cleaning up temp files..."
rm -f /tmp/talos-*.pid /tmp/talos-*.log 2>/dev/null || true
echo "  ✓ Cleaned /tmp/talos-* files"

echo ""
echo "=========================================="
echo "Stop Complete"
echo "=========================================="
echo ""
echo "All Talos services have been stopped."
echo ""
echo "To restart: ./deploy/scripts/start_all.sh"
