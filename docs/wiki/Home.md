# Welcome to the Talos Wiki

**Talos Protocol** - A production-ready, end-to-end encrypted P2P messaging system for AI Agents.

> **Version 2.0.0-alpha.1** | **261 Tests Passing** | **6/7 Phases Complete**

## Quick Links

### Core Documentation
- [🚀 Getting Started](Getting-Started) - Installation and quick start
- [📦 Python SDK](Python-SDK) - SDK usage guide
- [💡 Light Client](Light-Client) - Efficient header-only sync
- [🏗️ Architecture Overview](Architecture) - System design

### Security Features
- [🔄 Double Ratchet](Double-Ratchet) - Forward secrecy protocol
- [🔒 Access Control (ACLs)](Access-Control) - Fine-grained permissions
- [✅ Validation Engine](Validation-Engine) - Block validation
- [🆔 DIDs/DHT](DIDs-DHT) - Decentralized identity
- [🔐 Cryptography Guide](Cryptography) - Encryption details
- [📐 Mathematical Security Proof](Mathematical-Security-Proof)

### Integration
- [🤖 MCP Integration](MCP-Integration) - AI tool tunneling
- [📡 Network Protocol](Network-Protocol) - P2P networking
- [📁 File Transfer](File-Transfer) - Chunked streaming

### Reference
- [🔧 API Reference](API-Reference) - Full API docs
- [⛓️ Blockchain Design](Blockchain) - Message integrity
- [📊 Performance Benchmarks](Benchmarks) - Speed tests
- [🧪 Testing Guide](Testing) - Run tests
- [🛠️ Development Guide](Development) - Contributing

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
| 💡 **Light Client** | 🔄 | SPV proof verification |
| 🆔 **DIDs/DHT** | 🔄 | Decentralized identity |

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
| Python SDK | 19 |
| Other | 126 |
| **Total** | **196** |

## License

MIT License - See [LICENSE](../LICENSE)
