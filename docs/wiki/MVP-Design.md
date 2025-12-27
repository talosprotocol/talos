# Talos Protocol - Next Phases MVP Design

## Objective
Position Talos as a credible, production-ready trust protocol for MCP tool invocation, with clear separation between open-source protocol work and future productizable extensions.

## Philosophy
Talos treats authorization and audit as protocol invariants, not application conventions.

---

## Explicit MVP Non-Goals

❌ Not in scope for MVP
- No UI
- No multi-language SDKs
- No performance claims beyond local benchmarks
- No production SLA guarantees

---

## MCP Trust Boundary Definition

Before detailing phases, Talos explicitly defines its trust boundary with MCP:

| Assumption | Talos Position |
| --- | --- |
| MCP transport | Treated as untrusted. All messages are encrypted and signed |
| MCP server correctness | Talos enforces identity, authorization, audit. Talos does not validate MCP protocol correctness |
| Tool behavior | Tools are trusted only to execute what they receive. Misbehavior is detectable but not prevented |
| Tool output | Logged for audit. Not validated for semantic correctness. Tool outputs must be hashed and bound to request correlation ID in audit |

> **IMPORTANT**  
> Where Talos stops: Talos guarantees who invoked what tool with which capability and when. It does not guarantee the tool behaves correctly or safely.

> **NOTE**  
> Detectable means: audit proof binds tool identity, request hash, response hash, and capability, enabling post-hoc attribution, not prevention.

---

## Phase 0: Prerequisites (Prior Work Sync)

Based on prior conversation history, complete these prerequisites before Phase 1:

| Task | Source | Status |
| --- | --- | --- |
| Lint cleanup | 2022 errors (1589 auto-fixable) | Run `ruff check --fix` |
| Documentation sync | Testing.md shows 464 tests, actual is 496 | Update docs |
| Coverage at 79% | Threshold is 80% per prior work | +1% needed |
| README/CHANGELOG sync | v2.0.6 references may be stale | Verify |

> **NOTE**  
> These are housekeeping items. They should not block Phase 1 design work but must be resolved before shipping.

### Acceptance Criteria
- Ruff: zero errors, zero warnings in CI
- Coverage: ≥80% line coverage via pytest-cov in CI (same command as local)
- Docs: test count removed or made dynamic

---

## Phase 1: Protocol Credibility Gate (0–6 weeks)

Goal: Make the credible claim: "This protocol can be used to secure MCP tool invocation in real systems."

### Protocol Semantics (BLOCKING)

| Task | Current State | Required Work |
| --- | --- | --- |
| Wire format specification | Implicit in code | Write formal spec: message types, field ordering, versioning rules |
| Capability token lifecycle | Implemented but underdocumented | Document grant/revoke/delegate state machine, TTL semantics |
| Session establishment protocol | X3DH + Double Ratchet works | Document handshake sequence, failure modes, timeout behavior |
| Error semantics | Custom exceptions exist | Standardize error codes (TalosError enum), document recovery actions |
| MCP message envelope | MCPMessage dataclass | Specify required vs optional fields, capability binding |

> **IMPORTANT**  
> Protocol Ambiguity #1 - RESOLVED: CapabilityManager is the sole enforcement surface.

**Resolution (v1):**
- Canonical authorization: `CapabilityManager.authorize(envelope, request_hash, tool, method, resource)`
- `proxy.py` MUST call CapabilityManager for every request
- ACLManager is deprecated and may not be used for authorization in MCP pathways
- Legacy ACL config migrates to capability issuance policies (issuer-side)

> **IMPORTANT**  
> Protocol Ambiguity #2 - RESOLVED: Capabilities are checked per request, not per session.
- Sessions survive capability expiry
- Individual requests fail once capability expires
- No implicit privilege continuation (avoids sticky authority bugs)
- Revocation overrides validity even if TTL not expired
- Capability tokens include signed `issued_at` and `expires_at`
- Verifiers enforce expiry using local time with a configurable skew window (default: 60s)
- Short TTLs with caching may optimize later

### Cryptography (BLOCKING)

| Task | Current State | Required Work |
| --- | --- | --- |
| Key derivation audit | HKDF-SHA256 in `session.py` | Security review of INFO_* constants, domain separation |
| Signature binding | Ed25519 signs capability bytes | Add context prefix to prevent cross-protocol attacks |
| Replay protection | Message nonces exist | Document nonce generation spec, rejection rules |
| Timing attack surface | Standard Python comparisons | Replace with `secrets.compare_digest` in verification paths |

### Audit and Proofs (BLOCKING)

| Task | Current State | Required Work |
| --- | --- | --- |
| Audit log format | Informal logging in proxy | Define structured audit event schema, sign entries |
| Proof verification API | ValidationEngine validates blocks | Add API for capability proof verification, not just block proofs |
| Delegation chain verification | `delegation_chain` field on Capability | Implement recursive signature verification up the chain |

> **NOTE**  
> Audit Source: Audit events are emitted by the canonical capability enforcement path (CapabilityManager), not ACLManager. ACLManager audit hooks are deprecated and removed once CapabilityManager becomes the sole enforcement surface.

> **IMPORTANT**  
> Signed Structures Rule: All signed structures must have canonical byte encoding defined in PROTOCOL.md.
- All canonical JSON is UTF-8 bytes
- Binary fields are base64url without padding
- For request/response bodies, Talos signs hashes, not raw payloads
- Canonical JSON (RFC 8785) is the v1 encoding

#### Signed Field Coverage (v1)

| Object | Signed Fields |
| --- | --- |
| Capability | All fields except `signature` |
| Delegation | parent_capability_hash, child_scope, issued_at, expires_at, delegator_id, delegatee_id |
| MCP Envelope | correlation_id, capability_hash, request_hash, tool, method, timestamp, session_id |
| Audit Event | event_type, tool, capability_hash, request_hash, response_hash, agent_id, tool_id, timestamp, result_code |

> **NOTE**  
> Tool Identity (v1): MCP server is the signer of tool responses. Tool name is an attribute. Optional tool-level DIDs may be added later.

> **NOTE**  
> Issuer Trust: Capability issuer is a designated authority per org. Issuer public key distributed via DID document or config. Verifiers must validate issuer chain.

> **IMPORTANT**  
> Delegation Invariant: Delegated capabilities may only reduce scope, never expand it.

**v1 Scope Grammar:**  
`scope = tool:<name>[/method:<name>][/resource:<pattern>]`  
Prefix containment applies to slash-separated segments.

### MCP Integration (BLOCKING)

| Task | Current State | Required Work |
| --- | --- | --- |
| Capability enforcement | `proxy.py` has optional acl_manager | Make capability check mandatory, no bypass path |
| Request/response binding | MCP JSON-RPC uses `id` | Add Talos correlation ID, bind capability to request |
| Tool discovery | Not implemented | Implement `tools/list` with capability-scoped filtering |
| Unknown tool policy | Not implemented | Deny by default, log denial with reason |

> **CAUTION**  
> Enforcement Invariant: Any MCP request without a valid capability MUST be rejected before tool invocation and MUST emit an audit denial event.

**Denial Reason Taxonomy:**  
NO_CAPABILITY | EXPIRED | REVOKED | SCOPE_MISMATCH | DELEGATION_INVALID | UNKNOWN_TOOL | REPLAY | SIGNATURE_INVALID

> **NOTE**  
> Correlation ID Semantics: Unique per session, cryptographically unpredictable.  
> Replay cache: 10k IDs per session, LRU eviction.  
> Eviction only drops entries already acked.  
> Ack means receiver has emitted an audit event for this correlation_id.

### Benchmarks and Metrics (Nice to Have)

| Task | Current State | Required Work |
| --- | --- | --- |
| MCP round-trip latency | Not measured | Add benchmark: capability-checked tool invocation latency |
| Capability verification throughput | Not measured | Target: >10,000 verifications/sec |
| Session establishment time | Not measured | Target: <50ms for X3DH handshake |

### Documentation Gaps (Nice to Have)

| Gap | Impact |
| --- | --- |
| No PROTOCOL.md spec document | Teams cannot implement compatible clients |
| No threat model for MCP bridge | Unknown security properties at trust boundaries |
| No formal versioning policy | Breaking changes will surprise adopters |

---

## Phase 2: Reference Implementation Hardening (6–12 weeks)

### Highest-Risk Failure Modes
Production risks:
- Session state corruption on crash
- Key material in memory after exception
- Unbounded capability delegation chains
- Rate limit bypass via clock manipulation
- Concurrent session write corruption

Mitigations:
- WAL-based persistence
- Explicit key zeroization
- Enforce chain depth limit
- Server-side timestamps
- Per-session locks or STM

### Correctness Guarantees

| Task | Implementation |
| --- | --- |
| Session persistence durability | Replace JSON file writes with LMDB transactions |
| Key zeroization | Best-effort via `__del__` cleanup + `ctypes.memset` |
| Capability chain limit | Enforce MAX_DELEGATION_DEPTH = 3 in `delegate()` |
| Monotonic timestamps | Use `time.monotonic()` for rate limiting, not `time.time()` |

### API and Wire Format Stabilization

| Task | Description |
| --- | --- |
| Freeze Capability schema | Version 1.0 schema, no field additions without version bump |
| Freeze MCPMessage envelope | Add protocol_version field, define backward-compat rules |
| Semantic versioning policy | Document what constitutes breaking vs non-breaking |

### End-to-End Benchmarks

| Benchmark | Target | Measurement |
| --- | --- | --- |
| Full MCP invocation (session + capability + tool call + audit) | <100ms p99 | `pytest benchmarks/ --benchmark-json` |
| 1000 concurrent sessions | <500MB memory | Memory profiling with tracemalloc |
| Session recovery after crash | <5s | Kill process mid-message, measure recovery |

### Concurrency, Durability, Recovery

| Task | Current State | Required Work |
| --- | --- | --- |
| Session write conflicts | No locking | Add asyncio.Lock per session ID |
| Capability store crash safety | In-memory dict | LMDB or SQLite with WAL mode |
| Graceful degradation | Process dies on error | Structured error boundaries, health checks |

### Python Runtime Limitations

| Limitation | Impact | Tracking Condition |
| --- | --- | --- |
| GIL contention | Limited parallelism for signature verification | >30% CPU with <50% single-core utilization |
| Memory fragmentation | Long-running services degrade | RSS growth >2x over 24h under steady load |
| Startup time | Cold start latency | >500ms import time |

> **WARNING**  
> Python Key Zeroization Caveat: Python zeroization is best-effort. `__del__` not guaranteed to run promptly, objects may be copied. Strong guarantees require moving key material to a native core with explicit memory management.

Rust or Java core justified when:
- Signature verification becomes bottleneck (>80% of request time)
- Memory growth exceeds 3x baseline under sustained load
- Customers require <10ms p99 latency SLAs

> **CAUTION**  
> Explicit Go/No-Go #1: If secure MCP invocation p99 exceeds 50ms under 100 concurrent agents on a single node, Python core is non-viable.

> **CAUTION**  
> Explicit Go/No-Go #2: Under sustained load, RSS must remain within 2x baseline over 1 hour, and audit storage growth must be linear with events (not quadratic).

---

## Phase 3: Product Wedge Identification (12–20 weeks)

### Wedge 1: Talos Audit Plane (Enterprise)
Problem: Enterprises deploying AI agents need compliance-grade audit trails that satisfy SOC 2, GDPR, and internal governance requirements. On-device logs are insufficient.

Who pays: Enterprise security teams, compliance officers, MSPs managing multi-tenant agent deployments.

Why outside core protocol: The core protocol produces audit events. The Audit Plane aggregates, indexes, retains, and visualizes them.

Minimum commercial surface:
- Centralized audit event ingestion (gRPC or OTLP endpoint)
- 90-day retention with signed tamper-proof storage
- Query API: filter by agent, tool, time range, outcome
- Compliance export: SOC 2 evidence package generator
- Webhook alerts: capability revocation events, anomaly detection

Protocol adoption driver: Free protocol, paid observability.

**Protocol remains fully usable without this product.**

### Wedge 2: Talos Gateway (Policy Enforcement)
Problem: Organizations want to deploy MCP-connected agents without rewriting authorization into every agent. They need a centralized policy enforcement point.

Who pays: Platform teams managing 10+ agents, regulated industries, AI security vendors.

Why outside core protocol: The protocol defines how to check capabilities. The Gateway provides where and what policies.

Minimum commercial surface:
- Reverse proxy for MCP traffic (transparent interception)
- Policy language: Rego or CEL-based rules
- Capability token minting service (agents request, Gateway issues)
- Rate limiting and quota management (per-org, per-agent)
- CLI for operators (policy apply, agent list, request tail)

Post-pilot (after design partner validation):
- Admin UI: policy editor, agent registry, live request viewer

Protocol adoption driver: Gateway becomes the on-ramp for enterprises that want security without deep protocol integration.

**Protocol remains fully usable without this product.**

---

## Phase 4: What to Explicitly Defer or Avoid

### Postpone (Not Yet)

| Feature | Reason to Defer |
| --- | --- |
| TypeScript/Browser SDK | Focus on server-side agent use cases first |
| Post-Quantum cryptography | Standards still finalizing, add as optional later |
| Onion routing or metadata protection | Complexity, most users do not need it yet |
| BFT consensus | Single-org deployments do not need multi-validator |
| ZK proofs | Novel crypto rarely justifies protocol-level integration |
| Dashboard UI | Validate CLI/API first, UI is expensive to maintain |
| Multi-chain anchoring | Blockchain anchoring is off hot path, defer integration |

### Never in Core Protocol

| Feature | Reason |
| --- | --- |
| Token or incentive layer | Destroys neutrality, makes protocol a product |
| Built-in storage service | Protocol is transport-agnostic, storage is app concern |
| LLM-specific features | Protocol must work for any agent type |
| Vendor lock-in APIs | No Talos Inc. service dependencies in protocol spec |
| Paid gating of protocol features | All protocol capabilities must be open source |

### Common Traps to Avoid

| Trap | Why Harmful | How to Avoid |
| --- | --- | --- |
| Premature SDK proliferation | Fragments community, increases maintenance | One canonical SDK (Python), accept PRs for others |
| Feature creep before adoption | Complexity scares early adopters | Freeze scope until 5 production users |
| UI before API | UI opinions are expensive to change | Prove value via CLI, then invest in UI |
| Enterprise features in core | Slows open-source iteration | Keep enterprise in separate repos/services |
| Blockchain maximalism | Anchoring is optional, do not over-emphasize | De-emphasize in docs, it is a proof mechanism, not identity |

---

## Verification Plan

### Automated Tests
All existing tests pass as baseline:

```bash
pytest tests/ -v
pytest tests/test_capability.py tests/test_capability_store.py -v
pytest tests/test_session.py -v
pytest tests/test_mcp_integration.py tests/test_mcp_advanced.py -v
pytest tests/test_validation.py -v
```

### New Tests Required for Phase 1

| Test | File | Description |
| --- | --- | --- |
| test_capability_mid_session_expiry | tests/test_capability.py | Verify behavior when capability expires during active session |
| test_proxy_requires_capability | tests/test_mcp_integration.py | Confirm proxy rejects requests without valid capability |
| test_delegation_chain_verification | tests/test_capability.py | Verify recursive signature checking in delegation chains |

### Adversarial Tests (Security Invariants)

| Test | File | Description |
| --- | --- | --- |
| test_replayed_request_rejected | tests/test_mcp_integration.py | Request with same correlation ID rejected |
| test_delegation_scope_widening_fails | tests/test_capability.py | Attempt to delegate broader scope fails cryptographically |
| test_signature_context_confusion | tests/test_capability.py | Cross-protocol signature reuse rejected |

### Manual Verification (User Review)

- Protocol spec review: after writing PROTOCOL.md, request review from 2+ design partners
- Security audit scoping: identify scope for external cryptographic review
- MCP integration demo: record screencast of end-to-end capability-secured tool invocation

---

## Summary

This plan prioritizes:

- Protocol credibility over feature completeness
- Adoption ease over theoretical purity
- Monetization separation from protocol trust
- Implementation flexibility preserved for future optimizations

Critical path is Phase 1: Protocol Semantics + MCP Integration. Without mandating enforcement, Talos cannot credibly claim to "secure MCP tool invocation."
