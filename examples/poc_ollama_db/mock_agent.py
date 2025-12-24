import subprocess
import json
import time
import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Usage: python mock_agent.py <peer_id>")
        sys.exit(1)
        
    peer_id = sys.argv[1]
    
    print(f"[Agent] 🤖 Starting Agent. Target Peer: {peer_id}")
    print("[Agent] 📡 Launching Talos MCP Tunnel...")
    
    # Start talos mcp-connect as a subprocess (this is what Claude/Ollama would do)
    # We assume 'talos' is in path, or use sys.executable to call module
    # Using python -m src.client.cli to be safe in dev environment
    cmd = [sys.executable, "-m", "src.client.cli", "mcp-connect", peer_id, "--port", "8767"]
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr, # let stderr flow through
        text=True,
        bufsize=0 # Unbuffered for real-time
    )
    
    # Wait for connection (in real life, maybe wait 1-2s)
    time.sleep(2)
    
    try:
        # 1. Initialize
        print("[Agent] 🤝 Sending Initialize...")
        init_req = {
            "jsonrpc": "2.0", 
            "method": "initialize", 
            "params": {"capabilities": {}}, 
            "id": 1
        }
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()
        
        # Read response
        resp_line = process.stdout.readline()
        print(f"[Agent] 📩 Received: {resp_line.strip()}")
        
        # 2. List Tools
        print("[Agent] 🔍 Listing Tools...")
        list_req = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        }
        process.stdin.write(json.dumps(list_req) + "\n")
        process.stdin.flush()
        
        resp_line = process.stdout.readline()
        print(f"[Agent] 📩 Received: {resp_line.strip()}")
        
        # 3. Call Tool (Query DB)
        print("[Agent] 🦅 Calling Tool: query_db(users)...")
        call_req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "query_db",
                "arguments": {"table": "users"}
            },
            "id": 3
        }
        process.stdin.write(json.dumps(call_req) + "\n")
        process.stdin.flush()
        
        resp_line = process.stdout.readline()
        print(f"[Agent] 📩 Received: {resp_line.strip()}")
        
        # Parse result
        resp = json.loads(resp_line)
        content = resp["result"]["content"][0]["text"]
        print(f"\n[Agent] ✅ Database Result:\n{json.dumps(json.loads(content), indent=2)}")
        
    finally:
        process.terminate()

if __name__ == "__main__":
    main()
