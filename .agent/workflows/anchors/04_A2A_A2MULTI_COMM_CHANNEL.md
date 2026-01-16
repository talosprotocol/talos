# Phase 10: A2A and A2-multi communication channel (MVP win)

This phase is promoted to MVP-critical.

## Goal

Deliver a secure, high-signal agent-to-agent (A2A) and multi-agent (A2-multi) communication channel that is:

- End-to-end encrypted
- Authenticated by Talos identities
- Auditable without leaking content
- Easy to integrate for tool servers and governance workflows

## Why this matters

The governance agent only becomes compelling if it can coordinate multiple specialized agents (GitHub agent, Docs agent, Security agent) and do so securely.

## Scope

### A2A messaging

- Establish a secure session between two agents.
- Support request/response and streaming.
- Provide explicit delivery semantics.

### A2-multi (group sessions)

- Establish a group session with membership management.
- Ensure membership changes are auditable.
- Provide per-message sender authentication.

## Non-negotiable security properties

1. Identity binding
   - Every message is bound to a validated principal identity (Phase 6).

2. Confidentiality
   - Message content is encrypted end-to-end.
   - Audit logs contain only hashes and metadata, not plaintext.

3. Forward secrecy
   - Session keys must be ratcheted (or rotated) to limit blast radius.

4. Replay protection
   - Messages include monotonically increasing counters or unique IDs.

5. Determinism for audits
   - Any hashed metadata uses canonical JSON where applicable.

## Architecture (recommended)

### Control plane vs data plane

- Control plane: handshake, membership, and capability checks go through the gateway.
- Data plane: encrypted message frames travel peer-to-peer or through a relay that cannot decrypt.

### Session objects

- Session ID: uuidv7
- Participants: principal IDs
- Transcript hash chain: hash-only commits, no content

## Proposed deliverables

### PR 10.0: Contracts
Repo: talos-contracts

- Schemas:
  - `schemas/a2a/session_open.schema.json`
  - `schemas/a2a/message_frame.schema.json`
  - `schemas/a2a/group_event.schema.json`
- Vectors:
  - Handshake vectors (initiator/responder)
  - Message frame canonicalization vectors (metadata only)
  - Group membership change vectors

### PR 10.1: Gateway surfaces
Repo: talos-gateway

- Surfaces:
  - `POST /a2a/sessions/open`
  - `POST /a2a/sessions/{id}/rotate`
  - `POST /a2a/groups/open`
  - `POST /a2a/groups/{id}/members/add`
  - `POST /a2a/groups/{id}/members/remove`

Hard rules:

- Every surface maps to an RBAC permission.
- Every surface emits Phase 5 audit events.

### PR 10.2: Transport adapter
Repo: talos (core) + SDKs

- Provide a reference transport adapter:
  - WebSocket
  - QUIC (optional later)

The adapter must:

- Authenticate peers (principal binding)
- Encrypt message frames
- Support backpressure

### PR 10.3: End-to-end example
Repo: talos-governance-agent

- Demonstrate multi-agent coordination:
  - governance agent orchestrates github agent and docs agent
  - messages include approvals and capability propagation

## MVP acceptance criteria

- A2A:
  - Create session, exchange 100 messages, rotate keys, continue.
  - Replay attempt is rejected.
  - Audit trail reconstructs: who talked to whom, when, and outcome, without content.

- A2-multi:
  - Create group, add member, remove member, verify old member cannot decrypt new frames.
  - Membership changes produce audit events.

- Operational:
  - Metrics: session_open_total, message_sent_total, message_drop_total, rotate_total
  - No plaintext in logs

## Open questions (lock before implementation)

These must be resolved in Phase 10.0 contracts PR, not ad hoc in code:

- Group key management model (sender keys vs shared group key vs MLS-like)
- Exact message ordering and dedup semantics
- Whether gateway provides a relay service or peers connect directly
