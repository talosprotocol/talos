---
status: Implemented
audience: Developer
---

# Quickstart

> **Problem**: Get from zero to working Talos agent in 10 minutes.  
> **Guarantee**: Minimal steps, no optional branches.  
> **Non-goal**: This is not comprehensive—see [Python SDK](Python-SDK) for full API.

## Prerequisites

- Python 3.11+
- 5 minutes

## Install

```bash
pip install talos-protocol
```

## Step 1: Create Your Agent Identity

```python
from talos import TalosClient

# Create an agent with a persistent identity
client = TalosClient.create("my-agent")
print(f"Agent ID: {client.peer_id}")
print(f"Public Key: {client.public_key.hex()}")
```

Your agent now has:
- **Ed25519 keypair** for signing
- **X25519 keypair** for encryption
- **Unique peer ID** for discovery

## Step 2: Get Your Prekey Bundle

```python
# This bundle lets others establish sessions with you
bundle = client.get_prekey_bundle()
print(f"Bundle: {bundle}")
```

Share this bundle with peers who want to communicate with you.

## Step 3: Establish a Session

```python
# Given a peer's bundle, establish an encrypted session
await client.establish_session(peer_id, peer_bundle)
```

This creates a **Double Ratchet session** with:
- Per-message forward secrecy
- Authenticated key exchange
- Break-in recovery

## Step 4: Send a Message

```python
# Send an encrypted, signed message
await client.send(peer_id, b"Hello, secure world!")
```

What happens:
1. Message encrypted with current ratchet key
2. Ratchet advances (old key deleted)
3. Message signed with identity key
4. Committed to audit log
5. Transmitted to peer

## Step 5: Receive Messages

```python
# Register a callback for incoming messages
@client.on_message
async def handle_message(sender_id: str, plaintext: bytes):
    print(f"From {sender_id}: {plaintext.decode()}")

# Start listening
await client.listen()
```

## Step 6: Verify Audit Proof

```python
# Get proof that a message exists in the audit log
proof = client.get_merkle_proof(message_hash)

# Verify independently
assert client.verify_proof(proof)
print("✅ Message is permanently auditable")
```

## Complete Example

```python
import asyncio
from talos import TalosClient

async def main():
    async with TalosClient.create("my-agent") as client:
        # Share your bundle (e.g., via registry)
        bundle = client.get_prekey_bundle()
        
        # Establish session with peer
        await client.establish_session(peer_id, peer_bundle)
        
        # Send message
        await client.send(peer_id, b"Hello!")
        
        # Listen for responses
        @client.on_message
        async def on_msg(sender, data):
            print(f"Received: {data}")
        
        await client.listen()

asyncio.run(main())
```

## What You Just Did

| Step | What Happened | Security Property |
|------|---------------|-------------------|
| Create identity | Generated keypairs | Authenticity |
| Get bundle | Prepared for key exchange | Forward secrecy |
| Establish session | Double Ratchet handshake | Confidentiality |
| Send message | Encrypt + sign + commit | Non-repudiation |
| Verify proof | Merkle verification | Auditability |

## Common Patterns

### Two Agents in One Script

```python
async with TalosClient.create("alice") as alice:
    async with TalosClient.create("bob") as bob:
        # Exchange bundles
        await alice.establish_session(bob.peer_id, bob.get_prekey_bundle())
        await bob.establish_session(alice.peer_id, alice.get_prekey_bundle())
        
        # Communicate
        await alice.send(bob.peer_id, b"Hi Bob!")
```

### With MCP Tool Invocation

```python
# Grant capability to invoke a tool
capability = client.grant_capability(
    peer_id=tool_agent_id,
    scope="tools/filesystem/read",
    expires_in=300  # 5 minutes
)

# Invoke tool securely
result = await client.invoke_tool(
    peer_id=tool_agent_id,
    method="read_file",
    params={"path": "/data/config.json"},
    capability=capability
)
```

## Next Steps

| Goal | Page |
|------|------|
| Understand the mental model | [Talos Mental Model](Talos-Mental-Model) |
| Learn all API methods | [Python SDK](Python-SDK) |
| Secure MCP tools | [MCP Cookbook](MCP-Cookbook) |
| Deploy to production | [Hardening Guide](Hardening-Guide) |

---

> ⚠️ **Do not copy-paste to production**. This quickstart uses defaults suitable for development. See [Hardening Guide](Hardening-Guide) for production configuration.
