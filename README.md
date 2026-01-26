# Talos Protocol: A Secure Communication and Trust Layer for Autonomous AI Agents

> **Academic Abstract**: The rapid ascent of autonomous AI agents necessitates a trustable communication substrate that transcends centralized identity and authorization silos. The Talos Protocol introduces a decentralized, contract-driven architecture integrating self-sovereign identity (DIDs), capability-based authorization (RFC-style scopes), and forward-secure messaging (Double Ratchet). This work presents the first production-grade implementation of a trust layer specifically optimized for high-performance agentic interactions, achieving <2ms p50 authorization overhead while maintaining blockchain-anchored accountability.

---

## 1. Introduction

Autonomous agents lack a trustable substrate for cross-organizational interaction. Current paradigms rely on centralized OAuth or opaque platform-specific silos, which introduce single points of failure and prevent verifiable accountability. Talos addresses this by providing:

- **Cryptographic Identity**: Self-sovereign DIDs for every agent and service.
- **Granular Authorization**: Capability-based tokens with deterministic scope matching.
- **Verifiable Audit**: Blockchain-anchored, non-repudiable logs of all tool invocations.
- **Performance**: A Rust-based core capable of 600k+ auth/sec.

---

## 2. Related Work & Competitive Analysis

| Feature | TLS/OAuth (Standard) | DID/VC (General) | **Talos Protocol** |
| --------------------- | -------------------- | ------------------- | --------------------------- |
| **Identity** | Centralized (IdP) | Decentalized (DID) | **Decentralized (DID)** |
| **Authorization** | Bearer Tokens | Verifiable Creds | **Capability Tokens (L1)** |
| **Messaging** | TLS (Point-to-point) | Varies | **Double Ratchet (E2EE)** |
| **Accountability** | Database Logs | Optional Ledger | **Blockchain-Anchored** |
| **Latency (p50)** | 50ms - 200ms | >1s (usually) | **<2ms (C-Kernel)** |

---

## 3. System Architecture

Talos follows a **Contract-Driven Design** where the `contracts` repository serves as the single source of truth for all schemas and test vectors.
**Non-negotiable**: this project is contract-first; protocol logic and validation must come from published `contracts` artifacts, not re-implemented in consumers.

```mermaid
graph TD
    Root["talos (Orchestrator)"] --> Contracts["contracts (Schemas/Vectors)"]
    Root --> Core["core (Rust Performance Kernel)"]
    Root --> SDKs["sdks (Polyglot Clients)"]
    Root --> Services["services (Runtime)"]
    
    Services --> Gateway["gateway (REST/Auth)"]
    Services --> Audit["audit (Aggregation)"]
    
    Gateway --> Core
    SDKs --> Contracts
```

### Core Components

- **`contracts`**: JSON Schemas for identity, capabilities, and audit.
- **`core`**: Rust implementation of cryptographic primitives (PyO3 bindings).
- **`services/gateway`**: High-performance entry point for agent requests.
- **`services/audit`**: Secure collector for non-repudiable event logs.

---

## 3.1 End-to-End Flow Map (Runtime)

This section summarizes the default request path across the runtime surfaces (LLM, MCP tools, A2A, audit, and governance).

### Cross-cutting gates (all surfaces)
- **Contract-first validation**: schemas and vectors come from `contracts/`.
- **Surface registry + RBAC**: every route maps to permissions; unmapped routes are denied.
- **Audit always**: allowlisted metadata only; canonical JSON hashing; async sink.

### A) LLM inference (`POST /v1/chat/completions`)
1) Agent/SDK calls Gateway data plane.
2) Auth middleware validates key, RBAC, optional attestation.
3) Budget + routing pick upstream; call provider.
4) Audit event emitted (success or failure).

### B) MCP tool discovery + invocation (`/v1/mcp/*`)
1) List servers/tools or call tool via Gateway.
2) RBAC + per-team MCP policy enforcement.
3) Gateway calls MCP server (stdio or SSE).
4) Audit event emitted with allowlisted metadata.

### C) A2A sessions + frames (`/a2a/v1/*`)
1) Attested A2A requests create/accept/rotate sessions.
2) Frames are stored with replay protection and digest checks.
3) Group membership changes produce audit events.

### D) A2A JSON-RPC tasks (LLM or MCP path)
1) JSON-RPC envelope validated against A2A schemas.
2) Dispatcher creates task, enforces `a2a.invoke`.
3) Route to LLM or MCP tool call.
4) Task status updates streamed via Redis + SSE.

### E) Governance Agent (TGA) sidecar
1) Agent sends MCP call + capability token to TGA.
2) TGA validates Ed25519 JWS + constraints; logs hash-chained state.
3) Tool executes; response returned and logged.

### F) Audit service + dashboard visibility
1) Gateway emits audit event to Audit Service (`/events`).
2) Audit Service persists + exposes query + SSE stream.
3) Dashboard consumes stats and live stream.

---

## 4. Technical Design (High-Level)

### 4.1 Multi-Region & High Availability (Phase 12)

The runtime layer supports read/write database splitting with circuit-breaker failover, ensuring sub-5ms latency across geographic regions while maintaining strong consistency for security-critical secrets.

### 4.2 Automated Secret Rotation (Phase 13)

Talos implements zero-downtime key rotation using a `MultiKekProvider` with background workers and Postgres advisory locking, mitigating the risk of long-term credential exposure.

### 4.3 Adaptive Budgeting (Phase 15)

Autonomous agents are constrained by atomic `BudgetService` enforcement, preventing runaway costs and ensuring fair resource allocation via `off/warn/hard` enforcement modes.

---

## 5. Security Analysis

Talos is designed to withstand the following threat vectors:

- **Identity Spoofing**: Prevented by Ed25519-signed DIDs.
- **Replay Attacks**: Mitigated by session-bound correlation IDs and sliding window caches.
- **Privilege Escalation**: Blocked by deterministic scope containment rules in the Policy Engine.

---

## 6. Getting Started

### Quick Start

```bash
# Clone with all submodules
git clone --recurse-submodules git@github.com:talosprotocol/talos.git
cd talos

# Initialize and validate
./deploy/scripts/setup.sh
./run_all_tests.sh --ci --changed
```

📖 **Full Documentation**: [Wiki](https://github.com/talosprotocol/talos/wiki) | [Deployment Guide](docs/DEPLOYMENT.md)

---

## 7. Future Work

- **Phase 16**: Zero-Knowledge Proofs for capability obfuscation.
- **Phase 17**: Hardware Security Module (HSM) native integration.

---

## 8. References

[1] Nakamoto, S. (2008). "Bitcoin: A Peer-to-Peer Electronic Cash System."
[2] Bernstein, D. J. (2012). "High-speed high-security signatures." (Ed25519).
[3] Signal Messenger. "The Double Ratchet Algorithm."
[4] W3C. "Decentralized Identifiers (DIDs) v1.0."
[5] IETF RFC 8785. "JSON Canonicalization Scheme (JCS)."
