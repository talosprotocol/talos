# Python SDK

> **Developer-Friendly API for Talos Protocol**

## Overview

The Talos SDK provides a clean, Pythonic interface for building secure AI agent communication systems. It wraps the core protocol components with high-level abstractions.

## Installation

```bash
pip install -e .
```

---

## Quick Start

```python
from talos import TalosClient, SecureChannel

# Create client (auto-loads or generates identity)
client = TalosClient.create("my-agent")

# Start client
await client.start()

# Get your prekey bundle to share
bundle = client.get_prekey_bundle()

# Establish session with peer
session = await client.establish_session(peer_id, peer_bundle)

# Send encrypted message
await client.send(peer_id, b"Hello, World!")

# Cleanup
await client.stop()
```

---

## Core Components

### TalosClient

Main entry point for the SDK:

```python
from talos import TalosClient, TalosConfig

# Quick creation
client = TalosClient.create("agent-name")

# With custom config
config = TalosConfig(
    name="my-agent",
    difficulty=4,
    log_level="DEBUG",
)
client = TalosClient.create("my-agent", config)

# As async context manager
async with TalosClient.create("my-agent") as client:
    await client.send(peer_id, b"Hello!")
```

### SecureChannel

Async context manager for peer communication:

```python
from talos import SecureChannel

async with SecureChannel(client, peer_id, peer_bundle) as channel:
    # Send messages
    await channel.send(b"Hello!")
    await channel.send_text("Text message")
    await channel.send_json({"key": "value"})
    
    # Receive messages
    data = await channel.receive(timeout=5.0)
    text = await channel.receive_text()
    obj = await channel.receive_json()
```

### Identity

Manage cryptographic keys:

```python
from talos import Identity

# Create new identity
identity = Identity.create("my-agent")
print(f"Address: {identity.address}")

# Save to disk (private keys!)
identity.save("~/.talos/keys.json")

# Load existing
identity = Identity.load("~/.talos/keys.json")

# Sign data
signature = identity.sign(b"data to sign")
```

---

## Configuration

### TalosConfig

```python
from talos import TalosConfig

config = TalosConfig(
    # Identity
    name="my-agent",
    
    # Storage
    data_dir=Path.home() / ".talos",
    
    # Network
    registry_url="ws://localhost:8765",
    listen_port=0,  # Auto-assign
    
    # Blockchain
    difficulty=2,
    
    # Security
    forward_secrecy=True,
    
    # Rate limiting
    max_requests_per_minute=60,
    
    # Logging
    log_level="INFO",
)
```

### Environment Variables

Override config via environment:

```bash
export TALOS_NAME="prod-agent"
export TALOS_DIFFICULTY=4
export TALOS_LOG_LEVEL="WARNING"
```

### Presets

```python
# Development (relaxed settings)
config = TalosConfig.development()

# Production (strict settings)
config = TalosConfig.production()
```

---

## Session Management

### Prekey Bundles

```python
# Get your bundle to share
bundle = client.get_prekey_bundle()
# Returns: {"identity_key": "...", "signed_prekey": "...", ...}

# Publish to registry
await registry.publish(client.address, bundle)
```

### Establishing Sessions

```python
# Fetch peer's bundle from registry
peer_bundle = await registry.get(peer_id)

# Establish session
session = await client.establish_session(peer_id, peer_bundle)

# Check if session exists
if client.has_session(peer_id):
    await client.send(peer_id, b"Hello!")
```

---

## Error Handling

All errors inherit from `TalosError`:

```python
from talos import TalosError
from talos.exceptions import (
    ConnectionError,
    EncryptionError,
    AuthenticationError,
    SessionError,
    RateLimitError,
    TimeoutError,
)

try:
    await client.send(peer_id, data)
except SessionError as e:
    print(f"No session with {e.peer_id}")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except TalosError as e:
    print(f"Error [{e.code}]: {e.message}")
```

---

## Channel Pool

Manage multiple channels:

```python
from talos.channel import ChannelPool

pool = ChannelPool(client)

# Get or create channel
channel = await pool.get_or_create(peer_id, peer_bundle)
await channel.send(b"Hello!")

# Close all channels
await pool.close_all()
```

---

## Examples

### Simple Messaging

```python
import asyncio
from talos import TalosClient

async def main():
    async with TalosClient.create("alice") as alice:
        async with TalosClient.create("bob") as bob:
            # Exchange prekeys
            bob_bundle = bob.get_prekey_bundle()
            
            # Alice establishes session
            await alice.establish_session(bob.address, bob_bundle)
            
            # Alice sends message
            await alice.send(bob.address, b"Hello, Bob!")
            
            print(f"Alice -> Bob: Message sent!")

asyncio.run(main())
```

### AI Agent Communication

```python
from talos import TalosClient, SecureChannel
import json

async def agent_loop(client: TalosClient, peer_id: str, peer_bundle: dict):
    async with SecureChannel(client, peer_id, peer_bundle) as channel:
        # Send tool request
        await channel.send_json({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "file_read", "arguments": {"path": "/tmp"}},
            "id": 1,
        })
        
        # Receive response
        response = await channel.receive_json(timeout=30.0)
        print(f"Tool result: {response}")
```

---

## API Reference

### TalosClient

| Method | Description |
|--------|-------------|
| `create(name, config)` | Create client with auto-identity |
| `start()` | Start client |
| `stop()` | Stop client |
| `get_prekey_bundle()` | Get prekey bundle dict |
| `establish_session(peer, bundle)` | Create session |
| `has_session(peer)` | Check for session |
| `send(peer, data)` | Send encrypted data |
| `decrypt(peer, data)` | Decrypt received data |
| `get_stats()` | Get client statistics |

### SecureChannel

| Method | Description |
|--------|-------------|
| `connect()` | Establish channel |
| `close()` | Close channel |
| `send(data)` | Send bytes |
| `send_text(text)` | Send string |
| `send_json(obj)` | Send JSON |
| `receive(timeout)` | Receive bytes |
| `receive_text(timeout)` | Receive string |
| `receive_json(timeout)` | Receive JSON |

---

## See Also

- [Double Ratchet](Double-Ratchet.md) - Encryption protocol
- [Access Control](Access-Control.md) - Permission management
- [Getting Started](Getting-Started.md) - Installation guide
