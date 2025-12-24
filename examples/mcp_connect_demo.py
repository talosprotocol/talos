
"""
MCP Client Example - Demonstrates connecting to an MCP Tool over Talos.

This script acts as a local MCP Agent that connects to a remote MCP Server 
(running on another Talos node) via the blockchain.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from talos.client import TalosClient, TalosConfig
from talos.identity import Identity

async def run_mcp_client(target_peer_id: str):
    # 1. Setup Client
    name = "MCP-Agent"
    config = TalosConfig(name=name, p2p_port=8001)
    
    # Generate identity if needed
    if not config.keys_path.exists():
        Identity.generate(name).save(config.keys_path)
    
    identity = Identity.load(config.keys_path)
    client = TalosClient(identity, config)
    
    try:
        # 2. Start Client
        await client.start()
        print(f"Agent started at {client.address}")
        
        # 3. Connect to MCP Tool
        print(f"Connecting to MCP Tool at {target_peer_id[:16]}...")
        
        # This starts a local stdio proxy that tunnels to the remote peer
        # In a real scenario, you'd pipe this to an MCP SDK or LLM
        proxy = await client.start_mcp_client_proxy(target_peer_id)
        
        print("MCP Proxy Established! You can now send JSON-RPC messages via stdin.")
        print("Try: {'jsonrpc': '2.0', 'method': 'tools/list', 'id': 1}")
        
        # Keep alive
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await client.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mcp_connect_demo.py <target_peer_id>")
        sys.exit(1)
        
    asyncio.run(run_mcp_client(sys.argv[1]))
