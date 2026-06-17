# Talos Protocol Master Index & Developer Bible

Welcome to the **Talos Protocol**, a high-integrity, decentralized communication platform for AI agents. This document is a master directory and guide designed for developers, software engineers, product managers, UX designers, and AI agents operating on or integrating with the Talos Protocol ecosystem.

Use this index as a single entry point ("one-stop index") to find all the specialized architectural, feature, security, and SDK guidelines ("the shops") located throughout the repository.

---

## 🚀 1. Getting Started & Mental Models

If you are new to the Talos Protocol or setting up your development environment for the first time, start with these guides:

- **[quickstart.md](file:///Users/nileshchakraborty/workspace/talos/docs/getting-started/quickstart.md)**: Jump right in with the initial setup instructions and run a simple agent node.
- **[mental-model.md](file:///Users/nileshchakraborty/workspace/talos/docs/getting-started/mental-model.md)**: Understand the core principles of Mission Control, cryptographic auditability, and peer-to-peer agent coordination.
- **[talos-60-seconds.md](file:///Users/nileshchakraborty/workspace/talos/docs/getting-started/talos-60-seconds.md)**: An ultra-high-level summary of Talos guarantees and components.
- **[simple-guide.md](file:///Users/nileshchakraborty/workspace/talos/docs/getting-started/simple-guide.md)**: A step-by-step developer tutorial.
- **[one-command-demo.md](file:///Users/nileshchakraborty/workspace/talos/docs/getting-started/one-command-demo.md)**: Deploy a pre-configured local stack in one step to see Talos in action.

---

## 🏗️ 2. Architecture & Design Specs

Talos is designed around hexagonal ports and adapters to isolate core protocol logic from external services:

- **[overview.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/overview.md)**: System design, data flows, and relations between the gateway, dashboard, and registry components.
- **[context_graph.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/context_graph.md)**: The source-derived live map of codebase components, routes, features, and dependencies.
- **[infrastructure.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/infrastructure.md)**: Specifications for deployment targets, databases (Postgres, Redis), and system services.
- **[wire-format.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/wire-format.md)**: The binary and serialized wire envelope specifications (JWS, frames, header envelopes).
- **[protocol-guarantees.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/protocol-guarantees.md)**: Cryptographic and transaction guarantees provided by the protocol layer.
- **[fullscale_development_plan.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/fullscale_development_plan.md)**: Monorepo integration roadmap and feature development plan.

---

## 🔒 3. Cryptography, Security & Identity

Security is the core foundation of Talos. Access the technical validation and threat modeling wikis:

- **[cryptography.md](file:///Users/nileshchakraborty/workspace/talos/docs/security/cryptography.md)**: Detailed specifications of cryptographic primitives (Ed25519 signatures, X25519 key exchange, ChaCha20-Poly1305 symmetric AEAD encryption, and SHA-256 hashes).
- **[agent-identity.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/identity/agent-identity.md)**: Decentralized Identifiers (DIDs) for cryptographic identity verification.
- **[dids-dht.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/identity/dids-dht.md)**: Peer-to-peer discovery using Distributed Hash Tables (DHT) anchored to key DIDs.
- **[key-management.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/identity/key-management.md)**: Standardized key formats, storage in local wallets, and credential isolation.
- **[threat-model.md](file:///Users/nileshchakraborty/workspace/talos/docs/architecture/threat-model.md)**: Threat profiles, mitigation vectors, and trust boundaries.
- **[validation-engine.md](file:///Users/nileshchakraborty/workspace/talos/docs/security/validation-engine.md)**: Strict schemas and patterns (e.g. UUIDv7, Base64Url) used to validate incoming packets and prevent exploitation.
- **[mathematical-proof.md](file:///Users/nileshchakraborty/workspace/talos/docs/security/mathematical-proof.md)**: Formal verification and proofs of the cryptographic channel guarantees.

---

## 🤝 4. Peer-to-Peer & Agent Protocols (A2A, UCP, MCP)

Talos integrates three core protocols that define how agents talk, buy, and execute:

### Agent-to-Agent (A2A) Secure Messaging
- **[a2a-channels.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/messaging/a2a-channels.md)**: Overview of secure channels established using self-signed handshakes.
- **[double-ratchet.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/messaging/double-ratchet.md)**: Implementation details of the Signal Double Ratchet protocol, providing forward secrecy and break-in recovery.
- **[file-transfer.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/messaging/file-transfer.md)**: Encrypted file chunking and binary streaming across active ratchets.
- **[a2a-sdk-guide.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/a2a-sdk-guide.md)**: Practical guidelines for establishing A2A sessions and tracking tasks.

### Universal Commerce Protocol (UCP)
- **Dynamic Merchant Discovery**: Merchant capability sheets located at `/.well-known/ucp` detailing services, endpoints, and payment methods.
- **Order Tracking**: Post-purchase checkout state retrieval, order logs, and compliance hooks.
- **Identity Linking**: Mapping commerce identities securely to root principal keys in the gateway.

### Model Context Protocol (MCP)
- **[mcp-integration.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/integrations/mcp-integration.md)**: Gateway tunnel architecture that attaches authorization checks to standard MCP calls.
- **[mcp-cookbook.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/integrations/mcp-cookbook.md)**: Reference recipes for developing custom MCP servers and binding them to the gateway.
- **[mcp-proof-flow.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/integrations/mcp-proof-flow.md)**: Cryptographic execution evidence (4-layer artifact model: Identity, Authority, Intent, Execution) proving *who* performed *what* tool action *when*.

---

## 💻 5. SDK Reference & Integration

Talos provides native SDKs for building secure agents. Use these references:

- **[sdk-integration.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/sdk-integration.md)**: Integrations with third-party agent frameworks (e.g. LangChain, AutoGen).
- **[sdk-ergonomics.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/sdk-ergonomics.md)**: Design principles behind the client APIs.
- **[python-sdk.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/python-sdk.md)**: Python reference and installation details (`pip install talos-sdk-py`).
- **[typescript-sdk.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/typescript-sdk.md)**: TypeScript/JavaScript guide (`npm install @talosprotocol/sdk`).
- **[rust-sdk.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/rust-sdk.md)**: High-performance Rust bindings.
- **[usage-examples.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/usage-examples.md)** & **[examples.md](file:///Users/nileshchakraborty/workspace/talos/docs/sdk/examples.md)**: Code snippets for wallet creation, message sending, and peer connection.

---

## 📊 6. Observability, Auditing & UI/UX Design

Monitoring autonomous workflows requires specialized UI patterns. Use these resources:

- **[audit-scope.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/observability/audit-scope.md)**: Scope of the immutable events recorded to the ledger.
- **[audit-use-cases.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/observability/audit-use-cases.md)**: Forensic verification scenarios and compliance reporting.
- **[audit-explorer.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/observability/audit-explorer.md)**: Querying the ledger via TUI, Dashboard, and API.
- **[observability.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/observability/observability.md)**: Distributed tracing (Jaeger), Prometheus metrics, and system instrumentation.
- **[security-dashboard.md](file:///Users/nileshchakraborty/workspace/talos/docs/security/security-dashboard.md)**: System Threat Level states (SECURE, ELEVATED, CRITICAL), visual indicators, and proof drawer verification badges (VERIFIED vs REMEDIATION REQUIRED).

---

## ⚙️ 7. Operational Governance & Budgets

Preventing runaway agents and key compromisals at runtime:

- **[adaptive-budgets.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/operations/adaptive-budgets.md)**: Hierarchical budgeting (Team USD limits and Virtual Key warning/hard thresholds) with real-time reserve and settle flows.
- **[secrets-rotation.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/operations/secrets-rotation.md)**: Automated Key Encryption Key (KEK) rotation, versioned envelopes, and active grace periods to prevent runtime disruptions.
- **[global-load-balancing.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/operations/global-load-balancing.md)** & **[multi-region.md](file:///Users/nileshchakraborty/workspace/talos/docs/features/operations/multi-region.md)**: Resilient failovers and read-replica sync models.

---

## 🛠️ 8. Monorepo Directory & Submodule Index

The Talos Protocol consists of multiple interconnected modules:

- **[contracts/](file:///Users/nileshchakraborty/workspace/talos/contracts)**: Central source of truth for schemas, test vectors, and wire models.
- **[core/](file:///Users/nileshchakraborty/workspace/talos/core)**: Core cryptographic engine and message transport.
- **[services/ai-gateway/](file:///Users/nileshchakraborty/workspace/talos/services/ai-gateway)**: Secure gateway enforcing RBAC, budgets, and MCP tools.
- **[services/audit/](file:///Users/nileshchakraborty/workspace/talos/services/audit)**: Immutable, Merkle-tree event database.
- **[services/ucp-connector/](file:///Users/nileshchakraborty/workspace/talos/services/ucp-connector)**: Bridge to external commerce APIs.
- **[services/mcp-connector/](file:///Users/nileshchakraborty/workspace/talos/services/mcp-connector)**: MCP tool connector.
- **[sdks/](file:///Users/nileshchakraborty/workspace/talos/sdks)**: Language SDK implementations ([Python](file:///Users/nileshchakraborty/workspace/talos/sdks/python), [TypeScript](file:///Users/nileshchakraborty/workspace/talos/sdks/typescript), [Go](file:///Users/nileshchakraborty/workspace/talos/sdks/go), [Java](file:///Users/nileshchakraborty/workspace/talos/sdks/java), [Rust](file:///Users/nileshchakraborty/workspace/talos/sdks/rust)).
- **[site/dashboard/](file:///Users/nileshchakraborty/workspace/talos/site/dashboard)**: Next.js system control dashboard.
- **[tools/talos-tui/](file:///Users/nileshchakraborty/workspace/talos/tools/talos-tui)**: Interactive Terminal UI (TUI) for administration.

---

## 📋 9. Engineering & Contribution Reference

Guidelines for extending the codebase and adding features:

- **[development.md](file:///Users/nileshchakraborty/workspace/talos/docs/guides/development.md)**: Local development setup, database migrations, and hot-reload configs.
- **[testing.md](file:///Users/nileshchakraborty/workspace/talos/docs/testing/testing.md)**: Testing frameworks (pytest, vitest), coverage rules, and integration checks.
- **[test-manifests.md](file:///Users/nileshchakraborty/workspace/talos/docs/testing/test-manifests.md)**: Writing test metadata manifests (`.agent/test_manifest.yml`).
- **[a2a-v1-rollout.md](file:///Users/nileshchakraborty/workspace/talos/docs/guides/a2a-v1-rollout.md)**: PR sequencing and migration path guidelines.
- **[contributing-template.md](file:///Users/nileshchakraborty/workspace/talos/docs/templates/contributing-template.md)**: Code contribution checklists, naming conventions, and pre-commit validation hook requirements.
- **[decision-log.md](file:///Users/nileshchakraborty/workspace/talos/docs/reference/decision-log.md)**: Historic design choices and consequences.
- **[glossary.md](file:///Users/nileshchakraborty/workspace/talos/docs/reference/glossary.md)**: Domain terminologies.

---

## 🧪 10. Factual Status & Roadmap (Known Gaps)

To maintain strict compliance and factuality, please note the status of the following features:

- **A2A Group Channels**: **Planned**. Standardized group messaging schemas are documented, but the multi-party ratchet exchange is not yet fully implemented.
- **Policy Engine (Cedar/OPA Integration)**: **Planned** (DEC-015). Currently, gateway authorization rules are evaluated using declarative JSON/dict structures. Integration of third-party policy engines is on the roadmap.
- **Post-Quantum Cryptography Migration**: **Planned** (DEC-017). Standard primitives are restricted to Ed25519 and X25519.
- **P2P NAT Traversal / WebRTC**: **Planned** (DEC-004). Peer-to-peer discovery runs via the registry. Direct WebRTC P2P fallback channels are under research.
