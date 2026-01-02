# Welcome to the Talos Wiki

> **Talos is the secure communication and trust layer for autonomous AI agents.**

**Version 4.0** | **700+ Tests** | **100% Core Coverage** | **Contract-Driven**


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
| 📜 **Contract-Driven** | Single Source of Truth for schemas & vectors | [Architecture](Architecture) |
| 🦀 **Rust Kernel** | High-performance crypto & validation | [Architecture](Architecture) |
| 🔐 **Double Ratchet** | Per-message forward secrecy | [Double Ratchet](Double-Ratchet) |
| 🔒 **Capabilities** | Scoped, expiring authorization | [Agent Capabilities](Agent-Capabilities) |
| 📜 **Audit Proofs** | Blockchain-anchored verification | [Audit Explorer](Audit-Explorer) |
| 📊 **Audit Dashboard** | Next.js UI for audit verification, real-time metrics, and proof visualization. | [Audit Explorer](Audit-Explorer) |
| 🔗 **Generic MCP Connector** | A zero-code bridge to expose any standard MCP server (Git, SQLite, Ollama) over the secure Talos network. | [MCP Cookbook](MCP-Cookbook) |
| 🆔 **Agent Identity** | Cryptographic DIDs | [DIDs & DHT](DIDs-DHT) |
| 🌐 **Decentralized** | P2P, no central server | [Architecture](Architecture) |

---

## Quick Links by Role

### 👨‍💻 Developers

| Goal | Page |
|------|------|
| Get running fast | [Quickstart](Quickstart) |
| Use the SDK | [Python SDK](Python-SDK) |
| Secure MCP tools | [MCP Cookbook](MCP-Cookbook) |
| Copy-paste code | [Usage Examples](Usage-Examples) |

### 🔒 Security Reviewers

| Goal | Page |
|------|------|
| What we defend against | [Threat Model](Threat-Model) |
| Formal guarantees | [Security Properties](Security-Properties) |
| Crypto primitives | [Cryptography](Cryptography) |
| Proof verification | [MCP Proof Flow](MCP-Proof-Flow) |
| Explicit non-goals | [Non-Goals](Non-Goals) |

### 🏢 Operators

| Goal | Page |
|------|------|
| Production deployment | [Hardening Guide](Hardening-Guide) |
| Monitoring | [Observability](Observability) |
| Docker/K8s | [Infrastructure](Infrastructure) |
| Performance tuning | [Benchmarks](Benchmarks) |

### 📋 Evaluators

| Goal | Page |
|------|------|
| Why choose Talos | [Why Talos Wins](Why-Talos-Wins) |
| Compare alternatives | [Alternatives Comparison](Alternatives-Comparison) |
| Design decisions | [Decision Log](Decision-Log) |
| Future roadmap | [Future Improvements](Future-Improvements) |

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
| **Agent Model** | [Capabilities](Agent-Capabilities), [Authorization](Capability-Authorization), [Lifecycle](Agent-Lifecycle) |
| **Audit** | [Explorer](Audit-Explorer), [Scope](Audit-Scope), [Validation](Validation-Engine) |
| **Integration** | [MCP Cookbook](MCP-Cookbook), [SDK](Python-SDK), [API](API-Reference) |
| **Operations** | [Infrastructure](Infrastructure), [Benchmarks](Benchmarks), [Testing](Testing) |

---

## License

MIT License - See [LICENSE](../../LICENSE)
