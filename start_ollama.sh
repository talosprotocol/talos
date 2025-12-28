#!/bin/bash
set -e

# Configuration
IDENTITY_NAME="OllamaHost"
DATA_DIR="/tmp/talos_ollama_host"
REGISTRY="localhost:8765"

echo "=========================================="
echo "   Talos + Ollama MCP Connector Startup   "
echo "=========================================="

# 1. Check for Ollama
echo "🔍 Checking for local Ollama instance..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running."
else
    echo "❌ Error: Ollama is not running on port 11434."
    echo "   Please start Ollama first (e.g., 'ollama serve')."
    exit 1
fi

# 2. Check for Registry
echo "🔍 Checking for Talos Registry..."
if ! curl -s http://$REGISTRY/health > /dev/null; then
    echo "⚠️  Registry not found at $REGISTRY."
    echo "   Running independent startup (no P2P discovery yet)."
    # We continue, but peer discovery won't work without registry.
else
    echo "✅ Registry found."
fi

# 3. Initialize Identity
if [ ! -d "$DATA_DIR" ]; then
    echo "🔑 Initializing new identity: $IDENTITY_NAME..."
    mkdir -p "$DATA_DIR"
    python3 -m src.client.cli --data-dir "$DATA_DIR" init --name "$IDENTITY_NAME"
else
    echo "🔑 Using existing identity in $DATA_DIR"
fi

# 4. Register
echo "🌐 Registering with network..."
python3 -m src.client.cli --data-dir "$DATA_DIR" register --server "$REGISTRY" || true

# 5. Start MCP Server Bridge
HOST_ID=$(python3 -m src.client.cli --data-dir "$DATA_DIR" status | grep "Full ID:" | awk '{print $3}')
echo "------------------------------------------"
echo "✅ MCP Server Ready!"
echo "   Peer ID: $HOST_ID"
echo "   Authorized Agent: <ANY> (Demo Mode)"
echo "------------------------------------------"
echo "🚀 Starting Bridge..."
echo "   Command: python3 examples/mcp_server_ollama.py"

# Note: In production, you would restrict --authorized-peer <AGENT_ID>
# For this demo script, we aren't enforcing a specific peer in the launch command 
# unless user provides it as argument. 
# Codebase `mcp-serve` usually requires `--authorized-peer`. 
# Let's assume user might pass it, or we default to a placeholder/wildcard if supported.
# Looking at proxy.py, it enforces check.
# We will ask user specifically or generate a dummy 'Bob' to connect.

if [ -z "$1" ]; then
    echo "⚠️  Usage: ./start_ollama.sh <AUTHORIZED_AGENT_PEER_ID>"
    echo "   (Because this is a secure tunnel, you must explicitly allow a client)"
    exit 1
fi

AGENT_ID=$1

python3 -m src.client.cli --data-dir "$DATA_DIR" mcp-serve \
    --authorized-peer "$AGENT_ID" \
    --command "python3 examples/mcp_server_ollama.py" \
    --server "$REGISTRY" \
    --port 0 

