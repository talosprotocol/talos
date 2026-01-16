# Project history and locked decisions

This file captures the major program decisions from the beginning of the Talos project so future work stays consistent with the original intent.

## 0. Core product intent

Talos is a decentralized, cryptographically secure communication protocol designed for AI agents. The core promise is security-first agent tooling:

- Peer-to-peer identity and encrypted transport.
- Capability-based authorization for every tool invocation.
- Deterministic, verifiable audit trails.
- Replaceable implementations (ports and adapters).

## 1. Architecture direction: contract-driven kernel

A major architectural pivot was made toward a contract-driven kernel:

- `talos-contracts` is the source of truth for schemas, test vectors, and release sets.
- SDKs implement the contracts, they do not define protocol logic.
- All cross-repo integration happens through published versioned artifacts, not source imports.

Hard rule: no deep links or cross-repo internal imports.

## 2. Ecosystem decomposition

The ecosystem is intentionally split to avoid coupling:

- `talos` (core protocol reference implementation)
- `talos-contracts` (schemas, vectors, release sets, vector runner)
- `talos-sdk-ts`, `talos-sdk-py` (language SDKs)
- `talos-gateway` (policy enforcement point and routing)
- `talos-mcp-connector` (MCP tooling and connectors)
- `talos-dashboard` (security and observability UI)

## 3. Phase 5: Audit Integrity (locked and shipped)

Phase 5 established a cryptographically verifiable audit trail for gateway operations. The key locked principles:

- Canonical JSON (RFC 8785 JCS) for deterministic hashing.
- `event_hash = sha256(JCS(event_without_hash))`.
- Strict principal shapes (null vs absent) and strict field normalization.
- IP privacy: trusted proxy chain; otherwise omit IP hash fields entirely.
- Async sink must never block business requests.

## 4. Phase 6: Identity Hardening (locked and shipped)

Phase 6 hardened identity objects:

- Schema headers required (`schema_id`, `schema_version`).
- Strict Draft 2020-12 schemas with `additionalProperties: false` and `unevaluatedProperties: false` where composition exists.
- UUIDv7 lowercase only; uppercase must be rejected.
- Principal auth_mode discriminated union with strict absent vs null behavior.

## 5. Product direction: Governance agent

The program expanded from protocol + gateway into a product-grade operator agent:

- The agent is not allowed to call tools directly.
- All tool calls must be Talos-protected MCP calls through the gateway.
- A supervisor is the explicit policy authority for approvals and capability minting.

This agent is named `talos-governance-agent`.

## 6. Current MVP emphasis

The near-term MVP emphasis is:

1) Complete the backend (RBAC + secrets + stable surfaces + hardening).
2) Deliver a major win: secure agent-to-agent (A2A) and multi-agent (A2-multi) communication channels.

These two goals drive Phase 7 to Phase 9 planning in this anchor.
