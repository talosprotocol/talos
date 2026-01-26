#!/bin/bash
set -e

# Target Name from connector config (GenericHost)
# Since Peer IDs are keys, we rely on the Registry to resolve "GenericHost" -> PeerID
# But our CLI needs a PeerID or partial.
# The `mcp-call` implementation I wrote tries to finding by prefix.
# We will use "GenericHost" as a name if possible, OR we need the actual ID.
# The Connector logs "Initializing Identity 'GenericHost' in ...".
# Let's hope the name resolution works or we can grep the ID from logs.
# Actually, the 'mcp-call' command I wrote iterates clients. 
# But wait, `client.get_peers()` returns peers.
# The `GenericHost` will be registered.

echo "🚦 Generating Integration Traffic..."

# 1. Initialize Client Identity
rm -rf ~/.talos/traffic_gen
python3 -m src.client.cli --data-dir ~/.talos/traffic_gen init --name "TrafficGenerator" || true

# 2. Wait for Connector to be ready (run_all.sh should be running)
echo "   Waiting for system stabilization (15s)..."
sleep 15

# 3. List peers to find GenericHost
echo "   Discovering Connector..."
PEER_ID=$(python3 -m src.client.cli --data-dir ~/.talos/traffic_gen peers | grep -A 1 "GenericHost" | grep "ID:" | awk '{print $2}')

if [ -z "$PEER_ID" ]; then
    echo "⚠️  Connector 'GenericHost' not found in registry. Trying blindly with partial 'GenericHost' (unlikely to work if it needs ID)."
    # Actually, let's try calling 'GenericHost' as the ID if the CLI supports name lookup? 
    # My CLI implementation does: `if len(target) < 64: match prefix`.
    # It does NOT match name.
    # So we MUST get the ID.
    echo "   Dumping peers for debug:"
    python3 -m src.client.cli --data-dir ~/.talos/traffic_gen peers
    
    # If fails, maybe the Connector hasn't registered yet?
    exit 1
fi

echo "   Target Peer: $PEER_ID"

# 4. Invoke 'local-git' tool (list_tools)
echo "   Invoking 'tools/list'..."
python3 -m src.client.cli --data-dir ~/.talos/traffic_gen mcp-call $PEER_ID "local-git" "tools/list"

# 5. Invoke 'sqlite-db' tool via mcp (read_query)
# The tool name in config is "sqlite-db".
# Method: "read_query" (this depends on the actual tool implementation).
# Let's assume standard "tools/call" with name="read_query"?
# My CLI wraps `method` as the JSONRPC method.
# So if I want to call a tool, I send method="tools/call" params='{"name": "read_query", "arguments": ...}'
echo "   Invoking 'sqlite-db' query..."
python3 -m src.client.cli --data-dir ~/.talos/traffic_gen mcp-call $PEER_ID "sqlite-db" "tools/call" '{"name": "read_query", "arguments": {"query": "SELECT * FROM audit_log LIMIT 1"}}'

echo "✅ Traffic Generated."
