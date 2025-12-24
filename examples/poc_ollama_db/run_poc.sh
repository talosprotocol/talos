#!/bin/bash
set -e

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up..."
    kill $(jobs -p) 2>/dev/null || true
    rm -rf /tmp/talos_poc_*
}
trap cleanup EXIT

echo "🚀 Starting Talos POC: Ollama Agent + In-Memory DB"
echo "---------------------------------------------------"

# 1. Start Registry
echo "1️⃣  Starting Registry Server..."
python3 -m src.server.server --port 8765 > /dev/null 2>&1 &
REGISTRY_PID=$!
sleep 2

# 2. Setup Server (DB Host)
echo "2️⃣  Setting up DB Host (Alice)..."
export DATA_DIR_A="/tmp/talos_poc_alice"
mkdir -p $DATA_DIR_A
python3 -m src.client.cli --data-dir $DATA_DIR_A init --name "Alice" > /dev/null
python3 -m src.client.cli --data-dir $DATA_DIR_A register --server localhost:8765 > /dev/null

# Get Alice's ID
ALICE_ID=$(python3 -m src.client.cli --data-dir $DATA_DIR_A status | grep "Full ID:" | awk '{print $3}')
echo "   Alice ID: $ALICE_ID"

# 3. Setup Agent (Bob)
echo "3️⃣  Setting up Agent (Bob)..."
export DATA_DIR_B="/tmp/talos_poc_bob"
mkdir -p $DATA_DIR_B
python3 -m src.client.cli --data-dir $DATA_DIR_B init --name "Bob" > /dev/null
python3 -m src.client.cli --data-dir $DATA_DIR_B register --server localhost:8765 > /dev/null

# Get Bob's ID
BOB_ID=$(python3 -m src.client.cli --data-dir $DATA_DIR_B status | grep "Full ID:" | awk '{print $3}')
echo "   Bob ID: $BOB_ID"

# 4. Start MCP Server on Alice
echo "4️⃣  Starting MCP Server on Alice's machine..."
# We run this in background. It listens for Bob. Matches Bob's ID.
# Command points to our mock db script
DB_SCRIPT="$(pwd)/examples/poc_ollama_db/db_server.py"

python3 -m src.client.cli --data-dir $DATA_DIR_A mcp-serve \
    --authorized-peer $BOB_ID \
    --command "python3 $DB_SCRIPT" \
    --server localhost:8765 \
    --port 8766 > /dev/null 2>&1 &
SERVER_PID=$!

sleep 2

# 5. Run Agent (Bob)
echo "5️⃣  Running Agent Simulation (Bob)..."
# We need to tell the mock agent where to look for config/executable
# But wait, mock_agent invokes `src.client.cli` as subprocess.
# We need to ensure that subprocess uses Bob's data dir.
# The mock_agent.py needs to pass --data-dir. 

# Let's patch mock_agent.py or just pass ENV var?
# The CLI reads config from ctx. But we can modify mock_agent to accept extra args?
# Easier: Just modify mock_agent.py to respect TALOS_DATA_DIR env var if we supported it?
# OR: Just patch mock_agent quickly to inject DATA_DIR_B.

# Actually, let's just use a wrapper for the agent subprocess in the python script?
# No, let's just make the mock_agent use the default CLI but we override the home dir?
# The ClientConfig uses Path.home() / .talos. 
# If we change HOME env var, it changes data dir.

export HOME="/tmp/talos_poc_home_bob"
mkdir -p $HOME/.talos
# Copy Bob's wallet there so the default init finds it
cp -r $DATA_DIR_B/* $HOME/.talos/

python3 examples/poc_ollama_db/mock_agent.py $ALICE_ID

echo "---------------------------------------------------"
echo "✅ POC Complete!"
