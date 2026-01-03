# Welcome to the Talos Wiki

> **Talos is the secure communication and trust layer for autonomous AI agents.**

**Version 4.0** | **700+ Tests** | **Multi-Repo** | **Contract-Driven**

---

## 🚀 Start Here

| New to Talos? | Start with |
|---------------|------------|
| **Clone & setup** | [Getting Started](Getting-Started) |
| **60-second overview** | [Talos in 60 Seconds](Talos-60-Seconds) |
| **Understand the model** | [Mental Model](Talos-Mental-Model) |
| **Hands-on in 10 min** | [Quickstart](Quickstart) |
| **Learn the terms** | [Glossary](Glossary) |

---

## 📂 Repository Structure

Talos uses **git submodules** for a multi-repo architecture:

| Repo | Purpose |
|------|---------|
| `talos-contracts` | Source of truth (schemas, vectors) |
| `talos-core-rs` | Rust performance kernel |
| `talos-sdk-py` | Python SDK |
| `talos-sdk-ts` | TypeScript SDK |
| `talos-gateway` | FastAPI Gateway |
| `talos-audit-service` | Audit aggregator |
| `talos-mcp-connector` | MCP bridge |
| `talos-dashboard` | Next.js Console |

**Kernel Artifacts** (from `talos-contracts`):
- `schemas/*.json` – JSON Schema definitions
- `test_vectors/*.json` – Golden test cases
- Helper functions – `deriveCursor`, `base64url`, etc.

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
| 📊 **Audit Dashboard** | Next.js UI for proof visualization | [Audit Explorer](Audit-Explorer) |
| 🔗 **MCP Connector** | Zero-code bridge to MCP servers | [MCP Cookbook](MCP-Cookbook) |
| 🆔 **Agent Identity** | Cryptographic DIDs | [DIDs & DHT](DIDs-DHT) |

---

## Quick Links by Role

### 👨‍💻 Developers

| Goal | Page |
|------|------|
| Clone & build | [Getting Started](Getting-Started) |
| Python SDK | [Python SDK](Python-SDK) |
| TypeScript SDK | [TypeScript SDK](TypeScript-SDK) |
| MCP tools | [MCP Cookbook](MCP-Cookbook) |
| Development workflow | [Development](Development) |

### 🔒 Security Reviewers

| Goal | Page |
|------|------|
| Threat model | [Threat Model](Threat-Model) |
| Guarantees | [Security Properties](Security-Properties) |
| Cryptography | [Cryptography](Cryptography) |
| Non-goals | [Non-Goals](Non-Goals) |

### 🏢 Operators

| Goal | Page |
|------|------|
| Production setup | [Hardening Guide](Hardening-Guide) |
| Monitoring | [Observability](Observability) |
| Testing | [Testing](Testing) |
| Performance | [Benchmarks](Benchmarks) |

---

## Contributing

See [Development](Development) for the development workflow, Makefiles, and testing infrastructure.

```bash
# Quick setup
git clone --recurse-submodules git@github.com:talosprotocol/talos.git
./deploy/scripts/setup.sh
./deploy/scripts/run_all_tests.sh
```

---

## License

MIT © 2024 Talos Protocol Contributors
