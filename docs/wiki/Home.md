# Welcome to the Talos Wiki

**Talos Protocol** - A production-ready, end-to-end encrypted P2P messaging system for AI Agents.

> **Version 2.0.0** | **355 Tests Passing** | **57% Coverage** | **7/7 Phases Complete** ✅

## Quick Links

### 🚀 Getting Started
- [Getting Started](Getting-Started) - Installation and quick start
- [Usage Examples](Usage-Examples) - Copy-paste code examples
- [Simple Guide](Simple-Guide) - Basic concepts explained

### ⚙️ Setup & Ops
- [Infrastructure](Infrastructure) - Docker, Kubernetes, Helm
- [Development](Development) - Local dev setup
- [Testing](Testing) - Running the test suite

### 🔌 Integration (SDK & API)
- [Python SDK](Python-SDK) - Client library guide
- [API Reference](API-Reference) - Full API docs
- [MCP Integration](MCP-Integration) - AI tool tunneling
- [File Transfer](File-Transfer) - Secure media exchange
- [Light Client](Light-Client) - SPV mode for low-resource nodes

### 🧠 Core Concepts
- [Architecture](Architecture) - System design overview
- [Blockchain](Blockchain) - Chain structure and sync
- [Cryptography](Cryptography) - Security model & primitives
- [Double Ratchet](Double-Ratchet) - Forward secrecy protocol
- [Access Control](Access-Control) - Fine-grained permissions
- [Validation Engine](Validation-Engine) - 5-layer entry verification
- [DIDs/DHT](DIDs-DHT) - Decentralized identity & discovery

### 📚 Reference
- [Schemas](Schemas) - JSON data models
- [Benchmarks](Benchmarks) - Performance metrics
- [Enterprise Performance](Enterprise-Performance) - High-throughput stats
- [Security Proof](Mathematical-Security-Proof) - Formal verification
- [Future Improvements](Future-Improvements) - Project roadmap

---

## What is Talos?

Talos is a decentralized messaging protocol that combines:

- **End-to-end encryption** using modern cryptography (Ed25519, X25519, ChaCha20-Poly1305)
- **Forward secrecy** via Signal Double Ratchet protocol
- **Blockchain-based logging** for integrity and non-repudiation
- **P2P networking** for censorship resistance
- **Fine-grained ACLs** for access control
- **MCP Tunneling** for secure AI tool access

## v2.0.0 Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🔐 **Double Ratchet** | ✅ | Per-message forward secrecy |
| ✅ **Validation Engine** | ✅ | 5-layer block validation |
| 🔒 **Fine-Grained ACLs** | ✅ | Tool/resource permissions |
| 📦 **Python SDK** | ✅ | Clean developer API |
| 💡 **Light Client** | ✅ | SPV proof verification |
| 🆔 **DIDs/DHT** | ✅ | Decentralized identity |
| 🚢 **Infrastructure** | ✅ | Docker & Kubernetes |

## Quick Example

```python
from talos import TalosClient

async def main():
    async with TalosClient.create("my-agent") as client:
        # Get prekey bundle for others to connect
        bundle = client.get_prekey_bundle()
        
        # Establish encrypted session with peer
        await client.establish_session(peer_id, peer_bundle)
        
        # Send message with forward secrecy
        await client.send(peer_id, b"Hello!")

import asyncio
asyncio.run(main())
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     SDK / CLI Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ TalosClient │  │SecureChannel│  │    Identity     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    Security Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │Double Ratchet│ │   ACL Mgr   │  │   Validation    │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    Protocol Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Messages   │  │   Crypto    │  │  Serialization  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    Network Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │    P2P      │  │   Registry  │  │  Conn. Pool     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                   Storage Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Blockchain  │  │   Indexes   │  │  Merkle Proofs  │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Test Stats

| Module | Tests |
|--------|-------|
| Validation Engine | 19 |
| Double Ratchet | 16 |
| ACL System | 16 |
| SDK | 19 |
| Light Client | 24 |
| DIDs/DHT | 41 |
| Other | 126 |
| **Total** | **261** |

## License

MIT License - See [LICENSE](../../LICENSE)
