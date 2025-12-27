# Talos Protocol - Next Phases MVP Design

## Philosophy
Talos treats authorization and audit as protocol invariants, not application conventions.

---

## MCP Trust Boundary

| Assumption | Talos Position |
| --- | --- |
| MCP transport | Untrusted. Encrypted and signed |
| Tool behavior | Trusted to execute; misbehavior detectable, not prevented |
| Tool output | Hashed and bound to correlation_id in audit |

**Tool Identity (v1)**: MCP server signs tool responses, tool name is an attribute.

---

## Phase 0: Prerequisites

- Ruff: zero errors in CI
- Coverage: ≥80% **line coverage** via pytest-cov in CI
- Docs: test count removed or dynamic

---

## Phase 1: Protocol Credibility Gate (0–6 weeks)

### Protocol Ambiguity #1 — RESOLVED
CapabilityManager is the sole enforcement surface.

**Canonical API**: `CapabilityManager.authorize(capability, tool, method, request_hash)`

**Authorize MUST validate**:
- Sender signature on envelope
- Capability issuer signature and chain
- `issued_at`, `expires_at` (60s skew window)
- Revocation status
- Delegation chain signatures + scope containment
- `request_hash` matches canonical MCP bytes
- Unknown tool: **deny by default**
- Correlation_id replay cache check

### Protocol Ambiguity #2 — RESOLVED
Capabilities checked per request, not per session. Revocation overrides validity.

### Signed Structures Rule
- UTF-8 bytes, base64url without padding
- Sign hashes, not raw payloads
- Canonical JSON (RFC 8785) v1 encoding

**Request/response hashing**:
- `request_hash = sha256(canonical_json(mcp_request))`
- `response_hash = sha256(canonical_json(mcp_response))`

### Signed Field Coverage (v1)

| Object | Signed Fields |
| --- | --- |
| Capability | All fields except `signature` |
| Delegation | parent_capability_hash, child_scope, issued_at, expires_at, delegator_id, delegatee_id |
| MCP Envelope | correlation_id, capability_hash, request_hash, tool, method, timestamp, session_id |
| Audit Event | event_type, tool, capability_hash, request_hash, response_hash, agent_id, tool_id, timestamp, result_code |

### v1 Scope Grammar
`scope = tool:<name>[/method:<name>][/resource:<pattern>]`

**Scope containment (v1)**: Delegated scope must be a subset of parent scope under prefix containment of slash-separated segments.

### Enforcement Invariant
Any MCP request without valid capability MUST be rejected and MUST emit audit denial event.

**Unknown tool policy**: Deny by default, emit audit denial `UNKNOWN_TOOL`.

**Denial Taxonomy**:
```
NO_CAPABILITY | EXPIRED | REVOKED | SCOPE_MISMATCH | DELEGATION_INVALID | UNKNOWN_TOOL | REPLAY | SIGNATURE_INVALID
```

### Correlation ID Semantics
- Unique per session, cryptographically unpredictable
- Replay cache: 10k IDs/session, LRU eviction
- **Ack = receiver emitted audit event for this correlation_id**

---

## Phase 2: Hardening (6–12 weeks)

- LMDB transactions for session persistence
- Best-effort key zeroization
- MAX_DELEGATION_DEPTH = 3
- `time.monotonic()` for rate limiting

**Go/No-Go**: p99 > 50ms @ 100 concurrent → Python non-viable

---

## Phase 3: Product Wedges

**Audit Plane**: Enterprise audit aggregation. Protocol usable without it.

**Gateway**: Centralized enforcement proxy. Protocol usable without it.

---

## Phase 4: Defer List

**Postpone**: TypeScript SDK, Post-Quantum, UI

**Never**: Token layer, vendor lock-in APIs

---

## Verification Plan

### Required Tests
- test_capability_mid_session_expiry
- test_proxy_requires_capability
- test_delegation_chain_verification

### Adversarial Tests
- test_replayed_request_rejected
- test_delegation_scope_widening_fails
- test_signature_context_confusion
