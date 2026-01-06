---
status: Implemented
audience: Everyone
---

# Talos in 60 Seconds

> The secure communication and trust layer for autonomous AI agents.

## The Problem

AI agents are proliferating—but they have no trustable way to:

- **Identify** themselves cryptographically
- **Communicate** without centralized intermediaries
- **Prove** what they did, to whom, and when
- **Authorize** actions across organizational boundaries

Existing tools fail:

| Tool | Why It Fails |
|------|--------------|
| HTTP + OAuth | Centralized trust, no forward secrecy |
| Kafka / SQS | Infrastructure-heavy, not cryptographic |
| Matrix / Signal | Human-centric, not agent-native |
| gRPC + mTLS | No audit trail, no capability model |

## Who It's For

- **Agent developers** building multi-agent systems
- **Enterprises** deploying autonomous AI workflows
- **Regulated industries** requiring cryptographic audit trails
- **Cross-org collaborations** where no party trusts the other

## The Guarantees

| Guarantee | How Talos Provides It |
|-----------|----------------------|
| **Confidentiality** | Double Ratchet + E2EE |
| **Authenticity** | Ed25519 signatures |
| **Forward Secrecy** | Ephemeral key ratcheting |
| **Non-repudiation** | Blockchain-anchored audit log |
| **Capability Control** | Scoped, expiring, revocable tokens |
| **Verifiability** | Merkle proofs |

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Agents                          │
│    ┌─────────┐    ┌─────────┐    ┌─────────┐               │
│    │ Agent A │    │ Agent B │    │ Tool C  │               │
│    └────┬────┘    └────┬────┘    └────┬────┘               │
│         │              │              │                     │
├─────────┼──────────────┼──────────────┼─────────────────────┤
│         │     Talos Protocol Layer    │                     │
│    ┌────┴──────────────┴──────────────┴────┐               │
│    │  Identity │ Sessions │ Capabilities   │               │
│    │  Messaging │ Audit │ Proofs           │               │
│    └────────────────────────────────────────┘               │
│                         │                                   │
├─────────────────────────┼───────────────────────────────────┤
│              Blockchain │ (Optional Trust Anchor)           │
│    ┌────────────────────┴────────────────────┐             │
│    │  Identity anchors │ Capability commits  │             │
│    │  Audit roots │ Revocation events        │             │
│    └─────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## One Example

```python
from talos import TalosClient

async with TalosClient.create("my-agent") as client:
    # Establish encrypted session with peer
    await client.establish_session(peer_id, peer_bundle)
    
    # Send message with forward secrecy
    await client.send(peer_id, b"Execute task X")
    
    # Verify audit proof
    proof = client.get_merkle_proof(message_hash)
    assert client.verify_proof(proof)
```

**Result**: Agent A negotiated with Agent B, invoked Tool C, and produced an auditable, non-repudiable proof—all without a centralized server.

## Why Talos Matters

1. **Agent-native**: Built for autonomous systems, not humans
2. **Decentralized**: No single point of failure or control
3. **Auditable**: Every action is provable
4. **Practical**: Works today, not theoretical
5. **Extensible**: MCP, capabilities, cross-org—all built-in

---

**Next**: [Quickstart](Quickstart) | [Mental Model](Talos-Mental-Model) | [Glossary](Glossary)
