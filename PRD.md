# Talos Product Requirements

**Updated:** 2026-10-10
**Status:** Proposed delivery baseline grounded in the current source review. Requirements below are acceptance obligations, not a claim that the system already meets them.

## 1. Purpose

Talos helps teams control and inspect AI agent activity. An agent should have a verifiable identity, receive limited authority, perform an allowed action within its budget, and leave evidence that an operator can inspect and independently verify. Supported SDKs should make this workflow usable without requiring developers to implement cryptography or policy checks themselves.

The immediate product objective is one reproducible, authenticated, recoverable deployment with complete agent and operator journeys. Existing component implementations are substantial, but the reviewed working tree does not establish production readiness or equivalent behavior across all languages and deployment profiles.

## 2. Users and outcomes

| User | Job to complete | Successful outcome |
| --- | --- | --- |
| Platform administrator | Install, bootstrap identity, connect providers/tools, configure access | A documented deployment reaches a real authorized request with recoverable setup failures |
| Agent developer | Install SDK, create identity, invoke tools, exchange messages | Supported public APIs work from installed artifacts, with typed failures and a truthful compatibility matrix |
| Team administrator | Manage membership, roles, keys, policy and spending | Changes affect only the selected scope and are enforced on the next applicable operation |
| Security analyst | Investigate who did what under which authority | Correlated evidence distinguishes permission, execution outcome, delivery and verification |
| SRE | Detect dependency loss, revoke access, restore service/data | Degraded status is visible; recovery does not lose accepted records or repeat unsafe effects |
| Auditor | Export and verify evidence | Export identifies its scope, completeness, trust roots, versions and redaction |

## 3. Scope and current status

“Implemented” means source exists; it is not a statement about deployed artifacts. “Partial” means an important journey or guarantee is incomplete. The reviewed tree contains uncommitted changes; release claims require artifact-specific evidence.

| Area | Current status | Completion requirement |
| --- | --- | --- |
| Identity/signature primitives and contract schemas | Implemented components | Uniform validation, key lifecycle and published compatibility |
| Two-party encrypted sessions | Operational | Authenticated state transitions, ChaCha20-Poly1305 forward secrecy, and cross-language interop |
| A2A task clients & execution drivers | Completed & published | Canonical JSON-RPC 2.0 schemas, task lifecycles, and dual execution drivers (`InMemoryTaskRunner` & `TemporalTaskRunner`) in `@talosprotocol/a2a` |
| Zero-trust A2A security layer | Completed & published | W3C DIDs, signed Agent Cards, capability tokens, and Merkle audit trees in `@talosprotocol/talos-a2a` |
| Capability/RBAC, virtual keys, LLM/MCP policy | Partial integration | Same authenticated policy boundary on every supported route and profile |
| Budgets and secret rotation | Implemented components | Concurrent reserve/settle/recovery and real rotation journeys |
| Audit ingestion, Merkle proofs, governance logs | Operational | ProofDrawer cryptographic Merkle root attestation verified; durable delivery and independent verification |
| Dashboard and TUI | Operational | Real controls, truthful status, A2A Task Fleet Inspector, dynamic helper onboarding |
| Setup helper and onboarding | Operational | Real agent discovery (`/api/setup/agents`), atomic pairing, and dynamic lease allocation |
| MCP, UCP and terminal adapters | Implemented components | Enforced identity/authority, bounded effects and consistent receipts |
| Multi-region operation | Configuration/code fragments | Tested failover, consistency, recovery and measured availability |
| Group ratchets, Cedar/OPA, post-quantum, NAT/WebRTC | Planned | Separate contracts and product decisions before implementation |

External audit anchoring is optional integration work; it is not established by the default deployment. Chat UI traffic must not be described as end-to-end encrypted merely because encrypted-session code exists elsewhere.

## 4. Release scope

### First supported release

Deliver one documented gateway/control-plane topology, one supported deployment profile, a complete Python and TypeScript integration journey, and truthful capability declarations for Go, Java and Rust. This is a sequencing proposal: it does not remove existing language support. Any language advertised for a feature must pass that feature's public-API gates before release.

Provide identity/bootstrap, scoped administration, key and capability lifecycle, one LLM request, one MCP action, one encrypted agent exchange, budgets, durable evidence, independent proof verification, operator investigation, and recovery. Retain review gates for code and dependency updates.

### Later expansion

Add broader language/profile parity, federated and multi-region operation, durable distributed streaming, external anchors, group channels and alternative policy engines after foundational acceptance gates hold. Do not use a roadmap phase label as evidence that these are shipped.

## 5. Functional requirements

Priority: **P0** blocks a safe release; **P1** completes the supported product; **P2** expands supported capability. Owners are component roles, not assigned individuals.

| ID | Priority / owner | Requirement | Acceptance |
| --- | --- | --- | --- |
| FR-01 | P0 Platform + Security | Every protected operation authenticates a principal and authorizes the exact resource/action | Missing, malformed, expired, revoked and wrong-scope credentials cause no side effect; direct service access cannot bypass the decision |
| FR-02 | P0 Gateway | Apply org/team/key/tool restrictions consistently | List and invoke enforce the same allowlists; a team-scoped administrator cannot access another team's objects |
| FR-03 | P0 Governance | Reuse authority only while every original constraint remains satisfied | Cold and cached decisions agree for target, tool, read/write class, argument digest, principal, expiry and revocation |
| FR-04 | P0 Protocol | Invalid encrypted input cannot consume valid receive state | After each malformed current/skipped/DH-transition frame, the original valid frame still decrypts; replay is rejected |
| FR-05 | P0 Audit + Contracts | Accepted security events have a stable canonical representation and durable ownership | Producer → consumer → store → restart preserves event bytes/hash and proof root; ingestion acknowledgment follows persistence |
| FR-06 | P0 Audit + UI | Evidence availability and verification are distinct | Fetching JSON never produces a verified verdict; tampered leaf/path/root/signature and unknown trust root remain invalid/unverified; ProofDrawer implements Web Crypto Merkle root attestation |
| FR-07 | P0 Budgets | Reserve before an effect and settle/refund idempotently | Concurrent requests cannot exceed the configured hard limit; unavailable enforcement has an explicit safe policy; retries do not double-charge |
| FR-08 | P0 Delivery | Validation and automatic merge respect review policy | Failed/missing required checks block; eligible updates wait for approval then enter the chosen queue with head-SHA binding |
| FR-09 | P0 Platform | Supported images and deployment profiles start and retain state | Clean image startup, correct routes, enforcing network-policy checks, migrations and restart/restore tests pass |
| FR-10 | P1 Setup + UI | Complete first-run setup without manual database repair | Bootstrap → one-use pairing → real helper selection (`/api/setup/agents`) → leased job → result/retry completes; no placeholder IDs |
| FR-11 | P1 SDK | Public client send/receive performs a real transport operation | Two independent installed clients exchange plaintext through the supported encrypted transport; disconnected send has a truthful failure/status |
| FR-12 | P1 Contracts + SDK | Publish versioned capability and compatibility profiles | Package version matches runtime metadata; contract hashes and supported APIs are tested from installed artifacts in each language |
| FR-13 | P1 A2A | Support authenticated task lifecycle and streaming | Send/get/list/cancel and stream reconnect obey task ownership, ordering, bounded replay, cancellation and typed errors; dual drivers (`InMemoryTaskRunner` / `TemporalTaskRunner`) |
| FR-14 | P1 Admin + UI | Manage identities, roles, keys, policies and secrets | Authorized create/update/revoke/rotate has version-conflict handling, confirmation, audit correlation and read-back |
| FR-15 | P1 Configuration | Safely validate, publish and roll back configuration | Authenticated principal is derived from credentials; expected-version/idempotency protect publication; secrets remain redacted |
| FR-16 | P1 UI + TUI | Display actual service and operation status | Loading/empty/denied/unavailable/stale are distinct; reconnect restores ordered events; fixed healthy values cannot hide failure |
| FR-17 | P1 Auth + UI | Users can terminate and recover administrator sessions | Termination revokes server state and cookie; replay fails; displayed expiry matches policy; bootstrap/recovery is documented |
| FR-18 | P1 Analyst tools | Export independently verifiable evidence | Export includes schema/version, canonical records, proof context, ordering, scope, redaction and completeness metadata |
| FR-19 | P1 Connectors | Bound tool and commerce effects | Valid authority is checked at execution, targets are constrained, repeated request IDs do not repeat an acknowledged effect |
| FR-20 | P1 Docs + Marketing | Every user-visible assurance is evidence-backed | Runnable examples pass from release artifacts; claims identify workload/version/date and measure the claimed property |
| FR-21 | P2 Platform | Support deliberate multi-region operation | Region loss and replication lag tests preserve the declared authorization, spending and evidence semantics |
| FR-22 | P2 Protocol | Add planned protocol features | Versioned schemas, threat model, negative vectors and public consumer support precede release claims |

## 6. Nonfunctional requirements

- **Correctness:** denial produces no external side effect; money uses explicit units/rounding; accepted effects have correlated evidence and idempotency semantics.
- **Security:** least privilege, secret redaction, production mode validation, safe key lifecycle and authenticated trust boundaries; see [SECURITY.md](SECURITY.md).
- **Reliability:** bounded retries/queues/timeouts, observable backlogs, migration and restoration procedures; accepted durable state survives process/pod replacement.
- **Performance:** measure auth overhead, provider latency, first-token latency, audit lag, proof generation and UI interaction separately. Establish workload/hardware/concurrency baselines before setting p95/p99 SLOs. Existing benchmark values are not release-wide guarantees.
- **Usability:** keyboard access, visible focus, named controls, comprehensible errors, explicit effective identity/scope/mode, and recoverable workflows; see [DESIGN.md](DESIGN.md).
- **Compatibility:** version the wire profile, contract release set and package independently; preserve or explicitly migrate persisted sessions and data.
- **Operations:** define retention, capacity, RPO, RTO, freshness and revocation bounds per supported profile. Numeric targets remain open until owners validate operating cost and workload; no availability percentage is asserted here.

## 7. Success measures

Release acceptance is based on journeys and invariants, not test count alone. Measure first successful authorized request from a clean install, completion of an allowed and denied tool action, accepted-event persistence/verification coverage, restore success, revocation propagation, SDK compatibility and operational failure visibility. Required security fixtures must all pass with no unexpected skips. Performance and usability targets are proposed only after reproducible baselines exist.

## 8. Delivery order and open decisions

1. Repair trustworthy CI and release inventory; choose queue owner per repository while keeping approval requirements.
2. Close authorization, constraint reuse, budget and cryptographic-state gaps.
3. Freeze canonical evidence/digest semantics; repair durability, recovery and proof verification.
4. Select and validate the supported deployment topology; implement migrations/backups and restoration.
5. Complete onboarding, operator actions, SDK examples and installed-artifact interop.
6. Measure the supported release, then expand optional features.

Open decisions: supported deployment owner/profile, canonical gateway migration path, native GitHub versus Trunk queue ownership, compatibility policy for existing ratchet/digest formats, audit outage policy, retention and recovery targets, enterprise identity integration, and multi-region consistency. Existing schemas remain authoritative until changed through review; this PRD does not silently amend them.

## 9. Document map

[DESIGN.md](DESIGN.md) defines interactions; [ARCHITECTURE.md](ARCHITECTURE.md) defines boundaries; [DATA.md](DATA.md) defines data ownership and invariants; [SECURITY.md](SECURITY.md) defines threat/assurance requirements; [CODE_STYLE.md](CODE_STYLE.md) defines contribution conventions; [TESTING.md](TESTING.md) maps verification; [AGENTS.md](AGENTS.md) routes contributors and agents.
