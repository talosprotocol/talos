# Talos Program Anchor (.agent)

This directory is the program anchor and anti-drift mechanism for the Talos ecosystem.

## Why it exists

Talos spans multiple repositories (contracts, SDKs, gateway, connectors, dashboard, and now the governance agent). The most common failure mode is drift: duplicated logic, inconsistent schemas, and behavior changes not backed by vectors and CI gates.

## Non-negotiable program rules

1. Contract-first
   - `talos-contracts` is the source of truth for schemas, vectors, and release sets.
   - Consumers validate using bundled artifacts, not hand-written protocol logic.

2. No cross-repo deep links
   - No internal imports across repos.
   - Boundaries cross only via published artifacts (schemas, vectors, packages) or public APIs.

3. Determinism and vectors
   - Any behavior that is hashed, signed, ordered, or used for authz decisions must have test vectors.
   - Canonical JSON uses RFC 8785 JCS where applicable.

4. Audit everywhere
   - Gateway operations must emit audit events per Phase 5.
   - Audit service verifies `event_hash` and deduplicates by `event_hash`.

5. Identity strictness
   - Principal, Org, Team are strict Draft 2020-12 schemas per Phase 6.
   - UUIDv7 is lowercase and optional fields are omitted, not null.

6. CI as a gate, not a suggestion
   - Schema typecheck, vector validation, and drift checks are required to merge.

## Files in this anchor

- `01_PROJECT_HISTORY.md`: what we decided, and why.
- `02_GAP_AND_DRIFT_ANALYSIS.md`: plan vs reality, and what is missing or overdue.
- `03_MVP_BACKEND_COMPLETION.md`: the current MVP focus: complete the backend.
- `04_A2A_A2MULTI_COMM_CHANNEL.md`: the major win: secure agent-to-agent channels.
- `05_TALOS_GOVERNANCE_AGENT_PLAN.md`: the governance agent (repo layout, runtime, supervisor).
- `schemas/talos_governance_agent/`: Draft 2020-12 JSON schemas for TGA v1.

## Anti-drift workflow

- Every PR that changes behavior must add or update vectors.
- Every release updates status tables and freezes schema versions.
- Weekly: run a drift sweep (schemas duplicated, cursor logic duplicated, inconsistent error codes).

## Ownership

Primary owner agent name: `talos-governance-agent`.
