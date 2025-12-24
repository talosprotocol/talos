# Welcome to the Talos Wiki

> **Talos is the secure communication and trust layer for autonomous AI agents.**

**Version 2.0.6** | **464 Tests** | **79% Coverage** | **Production-Ready**

---

## Start Here

| New to Talos? | Start with |
|---------------|------------|
| **60-second overview** | [Talos in 60 Seconds](Talos-60-Seconds) |
| **Understand the model** | [Mental Model](Talos-Mental-Model) |
| **Hands-on in 10 min** | [Quickstart](Quickstart) |
| **See it work** | [One-Command Demo](One-Command-Demo) |
| **Learn the terms** | [Glossary](Glossary) |

---

## Why Talos?

AI agents lack a trustable way to:
- **Identify** themselves cryptographically
- **Communicate** without centralized intermediaries  
- **Prove** what they did, to whom, and when
- **Authorize** actions across organizational boundaries

**Talos solves this.** See [Why Talos Wins](Why-Talos-Wins) and [Alternatives Comparison](Alternatives-Comparison).

---

## Core Features

| Feature | Description | Page |
|---------|-------------|------|
| 🔐 **Double Ratchet** | Per-message forward secrecy | [Double Ratchet](Double-Ratchet) |
| 🔒 **Capabilities** | Scoped, expiring authorization | [Agent Capabilities](Agent-Capabilities) |
| 📜 **Audit Proofs** | Blockchain-anchored verification | [Audit Explorer](Audit-Explorer) |
| 🆔 **Agent Identity** | Cryptographic DIDs | [DIDs & DHT](DIDs-DHT) |
| 🤖 **MCP Security** | Secure tool invocation | [MCP Cookbook](MCP-Cookbook) |
| 🌐 **Decentralized** | P2P, no central server | [Architecture](Architecture) |

---

## Quick Links by Role

### 👨‍💻 Developers
- [Quickstart](Quickstart) - Get running in 10 minutes
- [Python SDK](Python-SDK) - Full client library
- [MCP Cookbook](MCP-Cookbook) - Secure tool patterns
- [Usage Examples](Usage-Examples) - Copy-paste code

### 🔒 Security Reviewers
- [Threat Model](Threat-Model) - What we defend against
- [Protocol Guarantees](Protocol-Guarantees) - Security properties
- [Cryptography](Cryptography) - Primitives and rationale
- [Non-Goals](Non-Goals) - What Talos doesn't do

### 🏢 Operators
- [Infrastructure](Infrastructure) - Docker, Kubernetes, Helm
- [Getting Started](Getting-Started) - Installation
- [Benchmarks](Benchmarks) - Performance metrics

### 📋 Evaluators
- [Why Talos Wins](Why-Talos-Wins) - Differentiators
- [Decision Log](Decision-Log) - Design rationale
- [Future Improvements](Future-Improvements) - Roadmap

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Agents                          │
├─────────────────────────────────────────────────────────────┤
│                    Talos Protocol Layer                     │
│   Identity │ Sessions │ Capabilities │ Audit │ Proofs      │
├─────────────────────────────────────────────────────────────┤
│               Blockchain (Optional Trust Anchor)            │
└─────────────────────────────────────────────────────────────┘
```

**Deep dive**: [Architecture](Architecture) | [Mental Model](Talos-Mental-Model)

---

## Quick Example

```python
from talos import TalosClient

async with TalosClient.create("my-agent") as client:
    # Establish encrypted session
    await client.establish_session(peer_id, peer_bundle)
    
    # Send with forward secrecy
    await client.send(peer_id, b"Hello!")
    
    # Verify audit proof
    proof = client.get_merkle_proof(msg_hash)
    assert client.verify_proof(proof)
```

---

## Documentation Map

| Category | Pages |
|----------|-------|
| **Concepts** | [Mental Model](Talos-Mental-Model), [Glossary](Glossary), [Architecture](Architecture) |
| **Security** | [Threat Model](Threat-Model), [Guarantees](Protocol-Guarantees), [Cryptography](Cryptography) |
| **Agent Model** | [Capabilities](Agent-Capabilities), [Lifecycle](Agent-Lifecycle), [Access Control](Access-Control) |
| **Audit** | [Explorer](Audit-Explorer), [Scope](Audit-Scope), [Validation](Validation-Engine) |
| **Integration** | [MCP Cookbook](MCP-Cookbook), [SDK](Python-SDK), [API](API-Reference) |
| **Operations** | [Infrastructure](Infrastructure), [Benchmarks](Benchmarks), [Testing](Testing) |

---

## License

MIT License - See [LICENSE](../../LICENSE)
