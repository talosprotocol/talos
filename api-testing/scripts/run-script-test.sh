#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$ROOT_DIR/api-testing/logs"

mkdir -p "$LOG_DIR"
cd "$ROOT_DIR"

# 1. Configuration
export DATABASE_WRITE_URL="postgresql://talos:talos_dev_password@localhost:5433/talos"
export DATABASE_READ_URL="postgresql://talos:talos_dev_password@localhost:5433/talos"
export REDIS_URL="redis://localhost:6379/0"
export TALOS_KEY_PEPPER="dev-pepper"
export A2A_DEV_BEARER_TOKEN="test-key-hard"
export AUTH_ADMIN_SECRET="dev-admin-secret"
export USE_JSON_STORES="false"
export MODE="dev"
export DEV_MODE="true"
export A2A_SIMULATED_LLM_RESPONSES="false"
export A2A_DEFAULT_MODEL_GROUP="ollama-group"
export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/services/ai-gateway"
export AUDIT_SINK_URL="http://127.0.0.1:8002"

echo "--- Talos Test Setup ---"

# 2. Check for Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "❌ Error: Ollama is not running on http://localhost:11434."
  echo "Please start Ollama before running this script."
  exit 1
fi
echo "✓ Ollama detected."

# 3. Start Dependencies (Postgres & Redis)
echo "Starting Docker dependencies..."
docker compose up -d postgres redis

# 4. Run Seeding Script
echo "Seeding database with test RBAC and virtual key..."
python3 "$SCRIPT_DIR/seed_test_env.py"

# 5. Start Sub-Services in Background
echo "Starting Sub-Services..."

# Kill any lingering uvicorn processes
pkill uvicorn || true

# Audit Service (8002)
(cd services/audit && \
TALOS__STORAGE_TYPE=memory \
TALOS_SKIP_INTEGRITY_CHECK=true \
uvicorn src.adapters.http.main:app --port 8002 --host 127.0.0.1) > "$LOG_DIR/audit.log" 2>&1 &
echo "✓ Audit Service starting on :8002"

# Configuration Service (8003)
(cd services/configuration && \
PORT=8003 \
uvicorn main:app --port 8003 --host 127.0.0.1) > "$LOG_DIR/config.log" 2>&1 &
echo "✓ Configuration Service starting on :8003"

# MCP Connector (8082)
(cd services/mcp-connector && \
TALOS_MCP_CONFIG="config.example.json" \
PYTHONPATH=src \
uvicorn main:app --port 8082 --host 127.0.0.1) > "$LOG_DIR/mcp.log" 2>&1 &
echo "✓ MCP Connector starting on :8082"

# Terminal Adapter (8083)
(cd services/terminal-adapter && \
TALOS_ENV="dev" \
TALOS_AUDIT_URL="http://127.0.0.1:8002" \
TALOS_TERMINAL_SESSION_DIR="/tmp/talos-terminal-sessions" \
PYTHONPATH=src \
uvicorn src.terminal_adapter.main:app --port 8083 --host 127.0.0.1) > "$LOG_DIR/terminal.log" 2>&1 &
echo "✓ Terminal Adapter starting on :8083"

# AI Chat Agent (8090)
(cd services/ai-chat-agent/api && \
CHAT_SHARED_SECRET="dev-secret" \
AI_GATEWAY_URL="http://127.0.0.1:8001" \
TALOS_API_TOKEN="test-key-hard" \
AI_MODEL="ollama-group" \
PYTHONPATH=src \
uvicorn src.main:app --port 8090 --host 127.0.0.1) > "$LOG_DIR/chat.log" 2>&1 &
echo "✓ AI Chat Agent starting on :8090"

# AIOps (8200)
(cd services/aiops/api && \
AUDIT_SERVICE_URL="http://127.0.0.1:8002" \
PYTHONPATH=src \
uvicorn src.main:app --port 8200 --host 127.0.0.1) > "$LOG_DIR/aiops.log" 2>&1 &
echo "✓ AIOps starting on :8200"

# 6. Start AI Gateway (Foreground)
echo -e "\n--- Starting Talos AI Gateway ---"
echo "Listening on http://127.0.0.1:8001"
echo "Service logs: $LOG_DIR"
echo "Data-plane token: test-key-hard"
echo "Admin/session JWT: fetch from the running gateway before admin or data-plane API calls."
echo "Generate a fresh scoped JWT:"
echo "curl -sS -X POST http://127.0.0.1:8001/admin/v1/auth/token \\"
echo "  -H 'X-Talos-Admin-Secret: ${AUTH_ADMIN_SECRET}' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"principal\":\"dev-admin\",\"permissions\":[\"llm.read\",\"mcp.read\",\"audit.read\"],\"ttl_seconds\":3600}'"
echo "Example admin request:"
echo "ADMIN_JWT=\$(curl -sS -X POST http://127.0.0.1:8001/admin/v1/auth/token -H 'X-Talos-Admin-Secret: ${AUTH_ADMIN_SECRET}' -H 'Content-Type: application/json' -d '{\"principal\":\"dev-admin\",\"permissions\":[\"llm.read\"],\"ttl_seconds\":3600}' | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"token\"])')"
echo "curl -sS http://127.0.0.1:8001/admin/v1/llm/upstreams -H \"Authorization: Bearer \$ADMIN_JWT\""
echo "Press Ctrl+C to stop all services."

# Trap to kill background processes on exit
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

AUDIT_SINK_URL="http://127.0.0.1:8002" \
uvicorn services.ai-gateway.app.main:app --port 8001 --host 127.0.0.1 --loop asyncio --workers 1
