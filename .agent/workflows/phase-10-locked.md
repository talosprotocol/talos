---
description: Phase 10 A2A Communication Channels - LOCKED SPEC
---

# Phase 10: A2A Communication Channels

## Status

LOCKED SPEC (Revised with Phase 10.1 Mandatory Decisions)

---

## Security Invariants (Non-Negotiable)

### I1: Unified Encoding

Use **base64url (no padding)** for ALL binary fields.

### I2: Normative frame_digest

`frame_digest = sha256(RFC8785_canonical_json(preimage))`
Preimage: `{schema_id, schema_version, session_id, sender_id, sender_seq, header_b64u, ciphertext_hash}`

### I3: Sender-Local Sequence

- `sender_seq` is sender-local monotonic (per session, per sender)
- Reject duplicates: unique constraint on `(session_id, sender_id, sender_seq)`
- Reject too-far-future: `sender_seq > last_seen + MAX_FUTURE_DELTA` (default: 1024)
- Out-of-order allowed within window

### I4: Append-Only Events

Session and group lifecycle MUST be append-only event logs with hash chain.

### I5: No Plaintext in Audit

Audit contains only: ids, sizes, digests, action types, outcomes. NO ciphertext.

### I6: Gateway Stores Ratchet State (Option A)

Gateway stores encrypted ratchet state blob. Routes include `ratchet_state_blob_b64u` + `ratchet_state_digest`.

---

## Phase 10.0: Contracts ✅ COMPLETE

### State Schemas

- `session.schema.json` - Session state (derived)
- `session_event.schema.json` - Append-only lifecycle events
- `encrypted_frame.schema.json` - E2E encrypted frames
- `group.schema.json` - Group state (derived)
- `group_event.schema.json` - Membership events

### Request Schemas

- `session_create_request.schema.json` - Includes ratchet_state_blob
- `session_accept_request.schema.json` - Includes ratchet_state_blob
- `session_rotate_request.schema.json` - Includes ratchet_state_blob
- `frame_send_request.schema.json` - Wraps encrypted_frame
- `group_create_request.schema.json`
- `group_member_add_request.schema.json`

---

## Phase 10.1: Gateway Surfaces (NEXT)

### Mandatory Config Constants

```python
A2A_MAX_FRAME_BYTES = 1_048_576  # 1 MiB
A2A_MAX_FUTURE_DELTA = 1024      # Max sequence gap
A2A_SESSION_DEFAULT_TTL = 86400  # 24 hours
```

### Routes

| Method | Path                             | Permission           | Request Schema             |
| ------ | -------------------------------- | -------------------- | -------------------------- |
| POST   | `/a2a/sessions`                  | `a2a.session.create` | `session_create_request`   |
| GET    | `/a2a/sessions/{id}`             | `a2a.session.read`   | -                          |
| POST   | `/a2a/sessions/{id}/accept`      | `a2a.session.accept` | `session_accept_request`   |
| POST   | `/a2a/sessions/{id}/rotate`      | `a2a.session.rotate` | `session_rotate_request`   |
| DELETE | `/a2a/sessions/{id}`             | `a2a.session.close`  | -                          |
| POST   | `/a2a/sessions/{id}/frames`      | `a2a.frame.send`     | `frame_send_request`       |
| GET    | `/a2a/sessions/{id}/frames`      | `a2a.frame.receive`  | - (cursor query)           |
| POST   | `/a2a/groups`                    | `a2a.group.create`   | `group_create_request`     |
| GET    | `/a2a/groups/{id}`               | `a2a.group.read`     | -                          |
| POST   | `/a2a/groups/{id}/members`       | `a2a.group.manage`   | `group_member_add_request` |
| DELETE | `/a2a/groups/{id}/members/{pid}` | `a2a.group.manage`   | -                          |
| DELETE | `/a2a/groups/{id}`               | `a2a.group.close`    | -                          |

### Scope Templates (for Surface Registry)

```json
{"path": "/a2a/sessions", "scope_template": {"scope_type": "principal", "attributes": {"principal_id": "{actor_id}"}}}
{"path": "/a2a/sessions/{id}", "scope_template": {"scope_type": "session", "attributes": {"session_id": "{id}"}}}
{"path": "/a2a/groups", "scope_template": {"scope_type": "principal", "attributes": {"principal_id": "{actor_id}"}}}
{"path": "/a2a/groups/{id}", "scope_template": {"scope_type": "group", "attributes": {"group_id": "{id}"}}}
```

### Recipient Isolation (Normative)

- POST `/frames`: `actor_id == frame.sender_id` AND actor is session participant
- GET `/frames`: Return only frames where recipient = actor (derived from session peer)
- Store `recipient_id` in DB row (derived field for indexing)

### Cursor Semantics

- Use talos-contracts cursor utilities
- Cursor encodes deterministic key: `(created_at, frame_id)`
- Frames are immutable, cursor-based fetch, deletion deferred to future

### Single-Writer Safety (Postgres)

- Advisory lock on `session_id` or `group_id` per event append
- `UNIQUE(session_id, seq)` and `UNIQUE(group_id, seq)`
- Hash-chain validated in transaction

---

## Deliverables

### Files

- `app/domain/a2a/session_manager.py`
- `app/domain/a2a/frame_store.py`
- `app/domain/a2a/group_manager.py`
- `app/api/a2a/routes.py`

### DB Tables

```sql
a2a_session_events(session_id, seq, prev_digest, digest, event_json, ts, actor_id)
a2a_sessions(session_id, state, initiator_id, responder_id, ratchet_state_blob, ratchet_state_digest, expires_at)
a2a_frames(session_id, sender_id, sender_seq, recipient_id, frame_digest, ciphertext_hash, header_b64u, ciphertext_bytes, created_at)
a2a_group_events(group_id, seq, prev_digest, digest, event_json, ts, actor_id, target_id)
a2a_groups(group_id, owner_id, state, created_at)
```

---

## Stable Error Codes

### Session/Group

- `A2A_SESSION_NOT_FOUND`
- `A2A_SESSION_STATE_INVALID`
- `A2A_SESSION_EXPIRED`
- `A2A_GROUP_NOT_FOUND`
- `A2A_GROUP_STATE_INVALID`
- `A2A_MEMBER_NOT_ALLOWED`

### Frames

- `A2A_FRAME_SCHEMA_INVALID`
- `A2A_FRAME_DIGEST_MISMATCH`
- `A2A_FRAME_CIPHERTEXT_HASH_MISMATCH`
- `A2A_FRAME_REPLAY_DETECTED`
- `A2A_FRAME_SEQUENCE_TOO_FAR`
- `A2A_FRAME_SIZE_EXCEEDED`
- `A2A_FRAME_STORE_ERROR`

---

## Tests Required

### Session Lifecycle

- create → pending
- accept valid only from pending → active
- rotate valid only from active
- close valid from pending or active → closed
- Invalid transitions → `A2A_SESSION_STATE_INVALID`

### Frame Send

- Digest mismatch → `A2A_FRAME_DIGEST_MISMATCH`
- Duplicate `(session_id, sender_id, sender_seq)` → `A2A_FRAME_REPLAY_DETECTED`
- Too far future → `A2A_FRAME_SEQUENCE_TOO_FAR`
- Size exceeded → `A2A_FRAME_SIZE_EXCEEDED`

### Frame Receive

- Only recipient can fetch frames
- Cursor ordering stable

### Audit

- Every route emits audit event
- Assert ciphertext absent from audit
