#!/bin/bash
set -e

# Talos Protocol - Quick Start Script (Monorepo)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GATEWAY_DIR="$SCRIPT_DIR/deploy/repos/talos-ai-gateway"
DASHBOARD_DIR="$SCRIPT_DIR/deploy/repos/talos-dashboard"

echo "=================================="
echo "   Talos Protocol - Quick Start   "
echo "=================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found."
    exit 1
fi

# Check for Node/NPM
if ! command -v npm &> /dev/null; then
    echo "Error: npm could not be found."
    exit 1
fi

# Kill any existing running instances
echo "[1/3] Cleaning up existing processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true # Gateway
pkill -f "next-server" 2>/dev/null || true # Dashboard
pkill -f "traffic_gen.py" 2>/dev/null || true
pkill -f "talos-gateway" 2>/dev/null || true
sleep 1
echo "    Previous processes terminated."

echo "[2/3] Installing/Verifying Dependencies..."
# Gateway
echo "    -> Gateway..."
if [ -d "$GATEWAY_DIR" ]; then
    (cd "$GATEWAY_DIR" && pip install -q -r requirements.txt)
else
    echo "ERROR: Gateway directory not found at $GATEWAY_DIR"
    exit 1
fi

# Dashboard
echo "    -> Dashboard..."
if [ -d "$DASHBOARD_DIR" ]; then
    (cd "$DASHBOARD_DIR" && npm install --silent)
else
    echo "ERROR: Dashboard directory not found at $DASHBOARD_DIR"
    exit 1
fi


echo "[3/3] Launching Development Stack..."

# 1. Start Gateway
echo "    Starting AI Gateway (Port 8000)..."
(cd "$GATEWAY_DIR" && export MODE=dev && export TALOS_ENV=dev && python3 -m uvicorn main:app --port 8000 --host 0.0.0.0 --reload) > gateway.log 2>&1 &
GATEWAY_PID=$!
echo "    Gateway PID: $GATEWAY_PID"

# 2. Start Dashboard
echo "    Starting Dashboard (Port 3000)..."
(cd "$DASHBOARD_DIR" && npm run dev) > dashboard.log 2>&1 &
DASH_PID=$!
echo "    Dashboard PID: $DASH_PID"

echo "------------------------------------------------"
echo "✅ Stack Online!"
echo "   - Gateway:   http://localhost:8000/docs"
echo "   - Dashboard: http://localhost:3000"
echo "   - Logs:      tail -f gateway.log dashboard.log"
echo ""
echo "Press Ctrl+C to stop all services."
echo "------------------------------------------------"

# Cleanup trap
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $GATEWAY_PID 2>/dev/null || true
    kill $DASH_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

wait
