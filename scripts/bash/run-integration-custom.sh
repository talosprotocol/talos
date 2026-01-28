#!/bin/bash
set -e

# Define Paths
GATEWAY_DIR="services/ai-gateway"
AUDIT_DIR="services/audit"
CHAT_DIR="services/ai-chat-agent/api"
CONFIG_DIR="services/configuration"
DASHBOARD_DIR="site/dashboard"

echo "=========================================="
echo "   Talos Integration Test - Full Stack    "
echo "=========================================="

export TALOS_DATABASE_URL="postgresql://talos:talos_dev_password@localhost:5433/talos"
export DATABASE_WRITE_URL="$TALOS_DATABASE_URL"
export RUN_MIGRATIONS="true"
export TALOS_KEY_PEPPER="dev_pepper_secret_12345"
export MASTER_KEY="dev_master_key_12345"
export TALOS__CONFIG_VERSION="1.0"
export TALOS__GLOBAL__ENV="dev"

# Cleanup
echo "[1/4] Cleaning up..."
pkill -f "uvicorn" || true
pkill -f "next-server" || true
kill -9 $(lsof -t -i:3002) 2>/dev/null || true
kill -9 $(lsof -t -i:8000) 2>/dev/null || true
kill -9 $(lsof -t -i:8001) 2>/dev/null || true
kill -9 $(lsof -t -i:8100) 2>/dev/null || true

# Skip Venv/Installs for speed/stability
# setup venv ... (skipped)
# install deps ... (skipped)

# Launch
echo "[3/4] Launching Services..."

# Gateway (8000)
echo "    -> Gateway :8000"
(cd "$GATEWAY_DIR" && python3 -m uvicorn app.main:app --port 8000 --host 0.0.0.0) > gateway.log 2>&1 &
GATEWAY_PID=$!

# Audit (8001)
echo "    -> Audit   :8001"
(cd "$AUDIT_DIR" && python3 -m uvicorn src.main:app --port 8001 --host 0.0.0.0) > audit.log 2>&1 &
AUDIT_PID=$!

# Chat (8100)
echo "    -> Chat    :8100"
(cd "$CHAT_DIR" && python3 -m uvicorn src.main:app --port 8100 --host 0.0.0.0) > chat.log 2>&1 &
CHAT_PID=$!

# Configuration (8002)
echo "    -> Config  :8002"
(cd "$CONFIG_DIR" && pip install -q -r requirements.txt --prefer-binary)
(cd "$CONFIG_DIR" && python3 -m uvicorn main:app --port 8002 --host 0.0.0.0) > config.log 2>&1 &
CONFIG_PID=$!

# Dashboard (3002)
# Ensure .env is correct (stripped Mock mode, fixed Config URL)
echo "    -> Dashboard :3002"
(cd "$DASHBOARD_DIR" && \
 sed -i '' '/DATA_SOURCE_MODE=MOCK/d' .env && \
 sed -i '' 's|TALOS_CONFIGURATION_URL=.*|TALOS_CONFIGURATION_URL=http://localhost:8002|g' .env && \
 npm run dev -- -p 3002) > dashboard.log 2>&1 &
DASH_PID=$!

# Wait for Dashboard/DB to be ready
echo "Waiting for stack..."
sleep 15

# Inject Session
echo "    -> Injecting Session..."
(cd "$DASHBOARD_DIR" && node scripts/inject-session.js > ../../session.txt)

# Traffic Gen
echo "    -> Traffic Gen"
python3 scripts/traffic_gen.py > traffic.log 2>&1 &
TRAFFIC_PID=$!

echo "------------------------------------------"
echo "✅ Stack Running!"
echo "   Gateway: $GATEWAY_PID"
echo "   Audit:   $AUDIT_PID"
echo "   Chat:    $CHAT_PID"
echo "   Config:  $CONFIG_PID"
echo "   Dash:    $DASH_PID"
echo "   Traffic: $TRAFFIC_PID"
echo "------------------------------------------"
echo "Logs available in respective directories (or current dir)"

# Wait loop
cleanup() {
    echo "Stopping..."
    kill $GATEWAY_PID $AUDIT_PID $CHAT_PID $CONFIG_PID $DASH_PID $TRAFFIC_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

wait
