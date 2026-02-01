# Welcome to the Talos Wiki

> **Talos v5.15** | **Phase 15: Adaptive Budgets** | **850+ Verified Tests** | **Multi-Repo Architecture**

---

## 🛡️ The Secure Layer for AI Agents

Talos Protocol is the **definitive security and trust layer** for autonomous AI agents. It provides a cryptographically verifiable, decentralized infrastructure for agent identification, communication, and authorization.

---

## 🚀 Quick Navigation

| 🆕 New to Talos? | 🛠️ Development | 🔒 Security & Policy |
| :--- | :--- | :--- |
| [Quickstart](getting-started-quickstart) | [Python SDK](sdk-python-sdk) | [Threat Model](architecture-threat-model) |
| [Mental Model](getting-started-mental-model) | [TypeScript SDK](sdk-typescript-sdk) | [Capability System](features-authorization-agent-capabilities) |
| [Talos in 60s](getting-started-talos-60-seconds) | [Rust Kernel](architecture-overview) | [Audit Logging](features-observability-audit-explorer) |
| [Architecture](architecture-overview) | [Go/Java SDKs](getting-started-getting-started) | [Security Proofs](security-mathematical-proof) |

---

## 📂 Core Components

Talos is built on a **Contract-Driven Kernel** architecture, ensuring consistency across all implementations.

### 🏛️ The Kernel Layer
- **[Contracts](contracts/)**: The single source of truth for all schemas and test vectors.
- **[Core-RS](architecture-overview)**: High-performance Rust implementation for cryptographic primitives.

### 🔌 Connectivity
- **[AI Gateway](features-integrations-mcp-integration)**: Unified entrance for LLM and MCP interactions.
- **[Audit Service](features-observability-observability)**: Tamper-evident event logging and verification.
- **[MCP Connector](features-integrations-mcp-cookbook)**: Secure tool-use bridge.

### 🛠️ Polyglot SDKs
Talos provides native SDKs for the most popular AI development environments:
- [Python SDK](sdk-python-sdk) | [TypeScript SDK](sdk-typescript-sdk) | [Rust SDK](sdk-rust-sdk) | [Go SDK](sdk-typescript-sdk) | [Java SDK](sdk-typescript-sdk)

---

## 🔥 Current Milestone: Phase 15 (Adaptive Budgets)

This release focuses on **economic security** for autonomous agents:
- **Real-time Quota Enforcement**: Atomic credit tracking for tool calls.
- **Multi-Region Recovery**: Zero-downtime budget synchronization.
- **Deterministic Billing**: Cryptographic proof of usage and cost.

---

## 📊 Project Health

- **Total Tests**: `850+` (100% Passing)
- **Coverage**: `92%` average across services
- **Uptime**: `99.99%` (Testnet)
- **Status**: [Production Ready]

---

> [!TIP]
> **New?** Start with the [Quickstart](getting-started-quickstart) to get a local cluster running in 5 minutes.

---

© 2026 Talos Protocol Contributors | [Apache 2.0 License](LICENSE)
