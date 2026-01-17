# Gap and drift analysis

This is a living document. Update it when any of the following change:

- A phase moves status (planned -> in progress -> released).
- A locked invariant is modified.
- A repo introduces new protocol logic outside `talos-contracts`.

## Legend

- RELEASED: vectors passing and CI gated
- IN PROGRESS: code exists but not fully gated
- PLANNED: spec written, not implemented
- UNKNOWN: repo state not yet audited

## Program-level gaps

### Gap 1: MVP now requires backend completeness

The current roadmap jumps from Phase 6 (identity) to Phase 7/8/9, but the MVP success criteria has tightened:

- Backend must be complete enough to support production-grade agent operations.
- The A2A and A2-multi communication channel must be a marquee differentiator.

This requires promoting several cross-cutting enablers from "future" to "MVP-blocking".

### Gap 2: A2A / A2-multi comm is not explicitly first-class in the phase plan

A2A messaging appears implicitly in Talos conceptually, but it is not planned as an end-to-end deliverable with:

- schemas
- vectors
- gateway surfaces
- operational metrics
- security posture

This must become a named phase with locked invariants.

## Repo-level drift risks (top)

### Risk A: Schema duplication across repos

Observed risk pattern:

- Gateway and SDKs often re-implement validation for speed or convenience.
- Dashboard sometimes re-implements cursor and ordering rules.

Mitigation:

- CI gate that fails any repo containing duplicated "contract logic" (cursor/base64url/uuidv7/order).
- Force consumers to import those functions from published contracts artifacts.

### Risk B: Canonicalization drift

If any component uses "almost canonical" JSON, event hashes and signatures will drift across languages.

Mitigation:

- One reference vector suite for canonicalization.
- Vectors must include canonical bytes as hex.
- Gate: any hash/signature related change requires vector update.

### Risk C: Null vs absent regressions

This is a recurring source of subtle auth and audit bugs.

Mitigation:

- Explicit invalid vectors for null where absent is required.
- Runtime must delete non-applicable fields instead of writing null.

## Status table (authoritative)

| Phase | Name                         |   Status | Blocking for MVP | Notes                                          |
| ----- | ---------------------------- | -------: | ---------------: | ---------------------------------------------- |
| 5     | Audit Integrity              | RELEASED |              Yes | Locked spec, deterministic hashes              |
| 6     | Identity Hardening           | RELEASED |              Yes | Locked v2 identities                           |
| 7     | RBAC Core                    | RELEASED |              Yes | PolicyEngine + middleware (2026-01-15)         |
| 8     | Secrets Management           | RELEASED |              Yes | Envelope encryption, KEK rotation (2026-01-15) |
| 9     | talos-governance-agent       | RELEASED |              Yes | TGA, tool servers, runtime loop (2026-01-15)   |
| 10    | A2A / A2-multi communication | RELEASED |              Yes | Sessions, frames, groups (2026-01-16)          |

## What must be audited next (action list)

This section is intentionally concrete. Each item must result in a PR that updates either:

- code, or
- vectors, or
- these anchors

1. Contracts audit

   - Confirm Phase 5 and Phase 6 schemas and vectors exist and match locked rules.
   - Confirm vector runner is gating CI.

2. Gateway audit

   - Confirm request surfaces map to permissions.
   - Confirm audit emission uses route template extraction only.
   - Confirm identity validation uses SDK validation wrappers and returns stable errors.

3. SDK audit

   - Confirm schema caching and pinning is correct.
   - Confirm no re-implementation of contract logic.

4. Connector audit

   - Confirm MCP servers never allow raw passthrough and enforce args schemas.

5. Missing phase definition
   - Write Phase 10 spec (A2A/A2-multi), schemas, and vectors.
