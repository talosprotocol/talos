# A2A SDK Usage Guide

> **Phase 10 Feature** | Released 2026-01-29

## Overview

The **A2A (Agent-to-Agent) SDK** enables secure, forward-secret communication between autonomous agents using the Signal Double Ratchet protocol.

**Key Features**:

- Session lifecycle management (create, accept, rotate)
- Frame encryption/decryption with replay protection
- Ratchet state persistence and synchronization
- Group messaging support

---

## Quick Start

### Installation

```bash
# Python SDK
pip install talos-sdk

# Or from source
cd sdks/python
pip install -e .
```

### Basic Usage

```python
import asyncio
from talos_sdk.a2a import A2ATransport, A2ASessionClient
from talos_sdk.wallet import Wallet

async def main():
    # Initialize wallet and transport
    wallet = Wallet.generate()
    transport = A2ATransport(
        base_url="http://localhost:8000",
        wallet=wallet
    )
    
    # Create a session
    client = await A2ASessionClient.initiate(
        transport=transport,
        sender_id=wallet.public_id,
        responder_id="did:peer:responder123"
    )
    
    # Send encrypted message
    await client.send_message(b"Hello from agent!")
    
    # Receive messages
    async for frame in client.receive_messages():
        plaintext = client.crypto.decrypt(frame)
        print(f"Received: {plaintext.decode()}")

asyncio.run(main())
```

---

## 1. Session Lifecycle

### Creating a Session (Initiator)

```python
from talos_sdk.a2a import A2ATransport, A2ASessionClient

# Initialize transport
transport = A2ATransport(
    base_url="http://localhost:8000",
    wallet=your_wallet
)

# Create session as initiator
client = await A2ASessionClient.initiate(
    transport=transport,
    sender_id=your_wallet.public_id,
    responder_id="did:peer:other_agent"
)

print(f"Session created: {client.session_id}")
```

The initiator:

1. Generates an ephemeral X25519 keypair
2. Calls `POST /a2a/sessions` with responder DID
3. Initializes Double Ratchet with initiator role
4. Stores session ID and ratchet state

### Accepting a Session (Responder)

```python
# Responder receives session notification
# (via polling, webhook, or SSE - implementation-specific)

# Accept the session
client = await A2ASessionClient.accept(
    transport=transport,
    session_id="session_abc123",
    sender_id=your_wallet.public_id,
    initiator_id="did:peer:initiator"
)

print(f"Session accepted: {client.session_id}")
```

The responder:

1. Generates an ephemeral X25519 keypair
2. Calls `POST /a2a/sessions/{session_id}/accept`
3. Initializes Double Ratchet with responder role
4. Stores session ID and ratchet state

### Session Rotation

Rotate the session to refresh keys:

```python
# Either party can initiate rotation
await client.rotate()

print("Session rotated - new ratchet state")
```

Rotation:

1. Generates new ephemeral keypair
2. Calls `POST /a2a/sessions/{session_id}/rotate`
3. Re-initializes Double Ratchet
4. Updates stored ratchet state

---

## 2. Frame Encryption

### Sending Encrypted Frames

```python
# Send a message (automatically encrypted)
await client.send_message(b"Confidential message")

# Send with metadata
await client.send_message(
    b"Task result",
    metadata={"task_id": "123", "status": "complete"}
)
```

Under the hood:

1. Increments sender sequence number
2. Encrypts plaintext with Double Ratchet
3. Computes `ciphertext_hash = SHA256(ciphertext)`
4. Calls `POST /a2a/frames` with encrypted frame
5. Updates ratchet state

### Receiving and Decrypting Frames

```python
# Poll for new frames
async for frame in client.receive_messages():
    # Decrypt frame
    plaintext = client.crypto.decrypt(frame)
    
    # Process message
    print(f"[{frame.sender_id}]: {plaintext.decode()}")
    
    # Acknowledge (optional)
    await client.acknowledge(frame.frame_id)
```

Under the hood:

1. Calls `GET /a2a/frames?session_id={session_id}&recipient_id={your_id}`
2. Validates `ciphertext_hash`
3. Checks sequence numbers for replay protection
4. Decrypts with Double Ratchet
5. Updates ratchet state

---

## 3. Ratchet State Management

The SDK automatically persist ratchet state after each encryption/decryption operation.

### Ratchet State Blob

The Gateway stores:

- `ratchet_state_blob_b64u`: Base64url-encoded serialized ratchet state
- `ratchet_state_digest`: SHA-256 hash of the blob

### Custom Storage

Provide your own storage backend:

```python
from talos_sdk.a2a import SequenceStorage

class RedisSequenceStorage(SequenceStorage):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_sender_seq(self, session_id: str) -> int:
        seq = await self.redis.get(f"seq:sender:{session_id}")
        return int(seq) if seq else 0
    
    async def set_sender_seq(self, session_id: str, seq: int):
        await self.redis.set(f"seq:sender:{session_id}", seq)
    
    async def get_recipient_seq(self, session_id: str) -> int:
        seq = await self.redis.get(f"seq:recipient:{session_id}")
        return int(seq) if seq else 0
    
    async def set_recipient_seq(self, session_id: str, seq: int):
        await self.redis.set(f"seq:recipient:{session_id}", seq)

# Use custom storage
client = await A2ASessionClient.initiate(
    transport=transport,
    sender_id=wallet.public_id,
    responder_id="did:peer:other",
    sequence_storage=RedisSequenceStorage(redis_client)
)
```

---

## 4. Group Messaging

### Creating a Group

```python
# Create a group
group_resp = await transport.create_group(
    owner_id=wallet.public_id,
    member_ids=["did:peer:member1", "did:peer:member2"]
)

group_id = group_resp.group_id
print(f"Group created: {group_id}")
```

### Adding Members

```python
# Add a new member
await transport.add_group_member(
    group_id=group_id,
    member_id="did:peer:member3"
)
```

### Removing Members

```python
# Remove a member (owner only)
await transport.remove_group_member(
    group_id=group_id,
    member_id="did:peer:member2"
)
```

### Sending Group Messages

```python
# Broadcast to all group members
await client.send_group_message(
    group_id=group_id,
    message=b"Team update: project complete"
)
```

---

## 5. Error Handling

### Common Errors

```python
from talos_sdk.a2a.errors import (
    SessionNotFoundError,
    SessionExpiredError,
    ReplayAttackError,
    PermissionDeniedError
)

try:
    await client.send_message(b"test")
except SessionNotFoundError:
    print("Session does not exist")
except SessionExpiredError:
    print("Session expired - create new session")
except ReplayAttackError:
    print("Replay attack detected")
except PermissionDeniedError:
    print("Not authorized for this action")
```

### Error Codes

| Code | Description |
| :--- | :--- |
| `A2A_SESSION_NOT_FOUND` | Session ID does not exist |
| `A2A_SESSION_EXPIRED` | Session TTL exceeded |
| `A2A_SESSION_STATE_INVALID` | Invalid state transition |
| `A2A_MEMBER_NOT_ALLOWED` | Not a session/group member |
| `A2A_REPLAY_DETECTED` | Sequence number replay |
| `A2A_DIGEST_MISMATCH` | Ciphertext hash invalid |

---

## 6. Complete Example

```python
"""
Complete A2A demo: initiator and responder exchange messages.
"""

import asyncio
from talos_sdk.a2a import A2ATransport, A2ASessionClient
from talos_sdk.wallet import Wallet

# Agent 1 (Initiator)
async def agent_1():
    wallet = Wallet.generate()
    transport = A2ATransport(
        base_url="http://localhost:8000",
        wallet=wallet
    )
    
    # Create session
    client = await A2ASessionClient.initiate(
        transport=transport,
        sender_id=wallet.public_id,
        responder_id="did:peer:agent2"
    )
    
    print(f"[Agent 1] Session created: {client.session_id}")
    
    # Send message
    await client.send_message(b"Hello Agent 2!")
    print("[Agent 1] Message sent")
    
    # Wait for response
    async for frame in client.receive_messages():
        plaintext = client.crypto.decrypt(frame)
        print(f"[Agent 1] Received: {plaintext.decode()}")
        break

# Agent 2 (Responder)
async def agent_2(session_id: str):
    wallet = Wallet.generate()
    transport = A2ATransport(
        base_url="http://localhost:8000",
        wallet=wallet
    )
    
    # Accept session
    client = await A2ASessionClient.accept(
        transport=transport,
        session_id=session_id,
        sender_id=wallet.public_id,
        initiator_id="did:peer:agent1"
    )
    
    print(f"[Agent 2] Session accepted: {client.session_id}")
    
    # Receive message
    async for frame in client.receive_messages():
        plaintext = client.crypto.decrypt(frame)
        print(f"[Agent 2] Received: {plaintext.decode()}")
        
        # Send response
        await client.send_message(b"Hello Agent 1!")
        print("[Agent 2] Response sent")
        break

# Run both agents
async def main():
    # Start agent 1
    await agent_1()
    
    # Agent 2 would receive notification and accept
    # (Implementation-specific discovery mechanism)

asyncio.run(main())
```

---

## 7. API Reference

### `A2ATransport`

Low-level HTTP client for A2A Gateway.

```python
class A2ATransport:
    def __init__(self, base_url: str, wallet: Wallet):
        ...
    
    async def create_session(
        self, 
        responder_id: str, 
        *, 
        expires_at: str | None = None
    ) -> SessionResponse:
        ...
    
    async def accept_session(
        self, 
        session_id: str,
        ratchet_state_blob_b64u: str | None = None,
        ratchet_state_digest: str | None = None
    ) -> SessionResponse:
        ...
    
    async def rotate_session(
        self, 
        session_id: str,
        ratchet_state_blob_b64u: str | None = None,
        ratchet_state_digest: str | None = None
    ) -> SessionResponse:
        ...
    
    async def send_frame(
        self, 
        frame: FrameRequest
    ) -> FrameResponse:
        ...
    
    async def list_frames(
        self, 
        session_id: str, 
        recipient_id: str,
        cursor: str | None = None, 
        limit: int = 100
    ) -> FrameListResponse:
        ...
```

### `A2ASessionClient`

High-level session manager with encryption.

```python
class A2ASessionClient:
    @classmethod
    async def initiate(
        cls,
        transport: A2ATransport,
        sender_id: str,
        responder_id: str,
        sequence_storage: SequenceStorage | None = None,
        crypto: FrameCrypto | None = None,
    ) -> "A2ASessionClient":
        ...
    
    @classmethod
    async def accept(
        cls,
        transport: A2ATransport,
        session_id: str,
        sender_id: str,
        initiator_id: str,
        sequence_storage: SequenceStorage | None = None,
        crypto: FrameCrypto | None = None,
    ) -> "A2ASessionClient":
        ...
    
    async def send_message(self, plaintext: bytes) -> str:
        ...
    
    async def receive_messages(self) -> AsyncIterator[Frame]:
        ...
    
    async def rotate(self) -> None:
        ...
```

---

## 8. See Also

- [A2A Channels](features-messaging-a2a-channels) - Protocol specification
- [Production Hardening](guides-production-hardening) - Phase 11 features
- [Double Ratchet](features-messaging-double-ratchet) - Cryptographic details
- [API Reference](api-api-reference) - Complete API documentation
