#!/bin/bash
set -e

# Talos Protocol - Integration Environment (Monorepo)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
GATEWAY_DIR="$ROOT_DIR/services/ai-gateway"
DASHBOARD_DIR="$ROOT_DIR/site/dashboard"
CONNECTOR_DIR="$ROOT_DIR/services/mcp-connector"

# Cleanup function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $(jobs -p) 2>/dev/null || true
    pkill -f "uvicorn main:app" || true
    pkill -f "next-server" || true
    echo "✅ All services stopped."
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup EXIT SIGINT SIGTERM

# Kill any existing instances before starting
echo "🧹 Cleaning up existing processes..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "talos-gateway" 2>/dev/null || true
# Kill any processes using our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1
echo "✅ Cleanup complete."

echo "🚀 Starting Talos Security Integration Environment..."

# 1. Start AI Gateway (Backend)
echo "---------------------------------------------------"
echo "📡 Starting AI Gateway (localhost:8000)..."
if [ -d "$GATEWAY_DIR" ]; then
    # Install if needed? Assuming dependencies installed via Makefile/start.sh or manual
    # We set MODE=dev for local run
    (cd "$GATEWAY_DIR" && export MODE=dev && export TALOS_ENV=dev && nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../../../gateway.log 2>&1 &)
    GATEWAY_PID=$!
    echo "   Gateway PID: $GATEWAY_PID"
else
    echo "❌ Gateway directory missing: $GATEWAY_DIR"
    exit 1
fi

# Wait for Gateway to be ready
sleep 3

# 2. Start Dashboard
echo "---------------------------------------------------"
echo "📊 Starting Dashboard (localhost:3000)..."
if [ -d "$DASHBOARD_DIR" ]; then
    (cd "$DASHBOARD_DIR" && npm run dev > ../../../dashboard.log 2>&1 &)
    DASH_PID=$!
    echo "   Dashboard PID: $DASH_PID"
else
    echo "❌ Dashboard directory missing: $DASHBOARD_DIR"
fi

# 3. Start Connector (Extracted)
echo "---------------------------------------------------"
echo "🔌 Starting Connector..."
if [ -d "$CONNECTOR_DIR" ]; then
    # Connector might have its own start script or needs specific launch
    # Adjusting to standard python launch if no script, or using existing logic if known.
    # Previous script ran: ./start.sh inside connector dir.
    if [ -f "$CONNECTOR_DIR/start.sh" ]; then
        (cd "$CONNECTOR_DIR" && ./start.sh > ../../../connector.log 2>&1 &)
        CONN_PID=$!
        echo "   Connector PID: $CONN_PID"
    else
        echo "⚠️  Connector start script not found. Skipping."
    fi
else
    echo "⚠️  Connector directory missing. Skipping."
fi

echo "---------------------------------------------------"
echo "✅ System Online!"
echo "   - Gateway:   http://localhost:8000/docs"
echo "   - Dashboard: http://localhost:3000"
echo "   - Logs:      tail -f gateway.log dashboard.log connector.log"
echo "   - Press Ctrl+C to stop"
echo "---------------------------------------------------"

# Wait forever successfully
wait
