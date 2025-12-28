#!/bin/bash
set -e

# Cleanup function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $(jobs -p) 2>/dev/null || true
    pkill -f "src.server.server" || true
    pkill -f "next-server" || true
    echo "✅ All services stopped."
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup EXIT SIGINT SIGTERM

# Kill any existing instances before starting
echo "🧹 Cleaning up existing processes..."
pkill -f "src.server.server" 2>/dev/null || true
pkill -f "uvicorn src.api.server:app" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "talos-mcp-connector/start.sh" 2>/dev/null || true
# Kill any processes using our ports
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1
echo "✅ Cleanup complete."

echo "🚀 Starting Talos Security Integration Environment..."

# 1. Start Gateway (Core)
echo "---------------------------------------------------"
echo "📡 Starting Gateway (localhost:8765)..."
nohup python3 -m src.server.server > gateway.log 2>&1 &
GATEWAY_PID=$!
echo "   PID: $GATEWAY_PID"

# Wait for Gateway to be ready (simple sleep for now)
sleep 2

# 2. Start API Server (Gateway Interface)
echo "---------------------------------------------------"
echo "🌐 Starting API Server (localhost:8000)..."
if [ -f .env ]; then source .env; fi
nohup python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload > api.log 2>&1 &
API_PID=$!
echo "   PID: $API_PID"

# 3. Start Dashboard (Extracted)
echo "---------------------------------------------------"
echo "📊 Starting Dashboard (localhost:3000)..."
# We run dev mode for debugging, or start.sh for consistency
# Using nohup to keep output separate but visible if tailed
(cd deploy/repos/talos-dashboard && npm run dev) > dashboard.log 2>&1 &
DASH_PID=$!
echo "   PID: $DASH_PID"

# 3. Start Connector (Extracted)
echo "---------------------------------------------------"
echo "🔌 Starting Connector..."
# Must set PYTHONPATH to find core src until package is published
(export PYTHONPATH=$(pwd) && cd deploy/repos/talos-mcp-connector && ./start.sh) > connector.log 2>&1 &
CONN_PID=$!
echo "   PID: $CONN_PID"

echo "---------------------------------------------------"
echo "✅ System Online!"
echo "   - Dashboard: http://localhost:3000"
echo "   - Logs: tail -f *.log"
echo "   - Press Ctrl+C to stop"
echo "---------------------------------------------------"

# Wait forever successfully
wait
