# Python SDK

> **Official Talos Protocol Python Client**

## Overview

The `talos-sdk-py` provides a production-ready client for interacting with the Talos Gateway. It handles cryptographic signing, connection management, and MCP protocol framing.

## Installation

```bash
pip install talos-sdk-py
```

## Quick Start

```python
import asyncio
from talos_sdk.client import TalosClient
from talos_sdk.wallet import Wallet

async def main():
    # 1. Initialize Wallet (Identity)
    # In production, load from secure storage
    wallet = Wallet.generate("my-agent-id")
    
    # 2. Connect to Gateway
    client = TalosClient("ws://localhost:8000/v1/ws", wallet)
    await client.connect()
    
    # 3. Send Signed MCP Request
    try:
        response = await client.sign_and_send_mcp(
            request={"method": "tools/list"},
            tool="system",
            action="list_tools"
        )
        print("Gateway Response:", response)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Core Components

### TalosClient

The main entry point for Gateway interaction.

```python
class TalosClient:
    def __init__(self, gateway_url: str, wallet: Wallet): ...
```

#### Methods

- **`async connect() -> None`**
  Establishes WebSocket connection to the Gateway. Raises `TalosTransportError` on failure.

- **`async sign_and_send_mcp(request: dict, tool: str, action: str) -> dict`**
  Signs an MCP JSON-RPC Payload and sends it to the gateway.
  - `request`: The raw JSON-RPC body (e.g., `{"method": "tools/call", ...}`)
  - `tool`: The target tool name (for ACL checks)
  - `action`: The specific action (for ACL checks)
  
- **`sign_http_request(method, path, query="", body=None) -> dict`**
  Generates `X-Talos-*` headers for authenticating standard HTTP requests (Phase 3 Attestation). Returns a dictionary of headers.

- **`async close() -> None`**
  Terminates the connection.

### Wallet

Manages Ed25519 identity keys.

```python
from talos_sdk.wallet import Wallet

# Generate new ephemeral wallet
wallet = Wallet.generate("agent-123")
print(wallet.address) 

# Sign raw bytes
signature = wallet.sign(b"data")
```

---

## Error Handling

All errors inherit from `TalosError`.

```python
from talos_sdk.errors import TalosTransportError

try:
    await client.connect()
except TalosTransportError as e:
    print(f"Connection failed: {e}")
```

## Protocol Compliance

This SDK implements **Talos Protocol v1.0**:
- **Signing**: Ed25519 signatures on canonicalized JSON.
- **Transport**: WebSockets with `talos.1.0` subprotocol.
- **Framing**: `SignedFrame` structure with nonces and timestamps.

