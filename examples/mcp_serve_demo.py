
"""
MCP Server Example - Demonstrates exposing a local tool via Talos.

This script acts as an MCP Host that exposes a local command (e.g. an MCP server)
to a specific authorized peer over the blockchain.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from talos.client import TalosClient, TalosConfig
from talos.identity import Identity

async def run_mcp_server(authorized_peer_id: str, command: str):
    # 1. Setup Client
    name = "MCP-Host"
    config = TalosConfig(name=name, p2p_port=8002)
    
    # Generate identity if needed
    if not config.keys_path.exists():
        Identity.generate(name).save(config.keys_path)
    
    identity = Identity.load(config.keys_path)
    client = TalosClient(identity, config)
    
    try:
        # 2. Start Client
        await client.start()
        print(f"Host started at {client.address}")
        
        # 3. Start MCP Proxy for Tool
        print(f"Exposing command: '{command}'")
        print(f"Authorized Peer: {authorized_peer_id[:16]}...")
        
        await client.start_mcp_server_proxy(authorized_peer_id, command)
        
        print("MCP Server Proxy is running. Waiting for connections...")
        
        # Keep alive
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await client.stop()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python mcp_serve_demo.py <authorized_peer_id> <command>")
        print("Example: python mcp_serve_demo.py <peer_id> 'npx -y @modelcontextprotocol/server-filesystem ./sandbox'")
        sys.exit(1)
        
    asyncio.run(run_mcp_server(sys.argv[1], sys.argv[2]))
