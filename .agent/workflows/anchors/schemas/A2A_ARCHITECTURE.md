# A2A Architecture Diagram

This document provides visual architecture diagrams for Phase 10 A2A communication.

## A2A Session Flow

```mermaid
sequenceDiagram
    participant Alice as Alice (Agent)
    participant Gateway as Talos Gateway
    participant Bob as Bob (Agent)
    participant DB as PostgreSQL

    Note over Alice, Bob: Phase 1: Session Establishment
    Alice->>Gateway: POST /a2a/v1/sessions (X3DH bundle)
    Gateway->>DB: Insert session (state=pending)
    Gateway->>DB: Append session_opened event
    Gateway-->>Alice: session_id

    Bob->>Gateway: POST /a2a/v1/sessions/{id}/accept
    Gateway->>DB: Advisory lock (session_id)
    Gateway->>DB: Update state=active
    Gateway->>DB: Append session_accepted event
    Gateway-->>Bob: OK

    Note over Alice, Bob: Phase 2: Encrypted Messaging
    Alice->>Alice: RatchetFrameCrypto.encrypt()
    Alice->>Gateway: POST /a2a/v1/sessions/{id}/frames
    Gateway->>Gateway: Validate frame_digest
    Gateway->>Gateway: Validate ciphertext_hash
    Gateway->>DB: INSERT frame (replay check via UNIQUE)
    Gateway-->>Alice: 201 Created

    Bob->>Gateway: GET /a2a/v1/sessions/{id}/frames?after=cursor
    Gateway->>DB: SELECT frames ORDER BY created_at
    Gateway-->>Bob: frames[]
    Bob->>Bob: RatchetFrameCrypto.decrypt()

    Note over Alice, Bob: Phase 3: Session Close
    Alice->>Gateway: POST /a2a/v1/sessions/{id}/close
    Gateway->>DB: Update state=closed
    Gateway->>DB: Append session_closed event
    Gateway-->>Alice: OK
```

## Data Flow Architecture

```mermaid
flowchart TB
    subgraph SDK["talos-sdk-py"]
        W[Wallet] --> TC[TalosClient]
        TC --> T[A2ATransport]
        T --> SC[A2ASessionClient]
        SC --> RFC[RatchetFrameCrypto]
        RFC --> S[Session/Double Ratchet]
    end

    subgraph Gateway["talos-ai-gateway"]
        API["/a2a/v1/*" Routes]
        API --> RBAC[RBAC Middleware]
        RBAC --> SM[SessionManager]
        RBAC --> FS[FrameStore]
        RBAC --> GM[GroupManager]
        SM --> PG[(PostgreSQL)]
        FS --> PG
        GM --> PG
    end

    SC <-->|HTTP + AuthZ| API
```

## Database Schema

```mermaid
erDiagram
    A2A_SESSIONS {
        string session_id PK
        string state
        string initiator_id
        string responder_id
        text ratchet_state_blob
        string ratchet_state_digest
        datetime expires_at
        datetime created_at
    }

    A2A_SESSION_EVENTS {
        string session_id PK
        int seq PK
        string prev_digest
        string digest
        json event_json
        datetime ts
        string actor_id
    }

    A2A_FRAMES {
        string session_id PK
        string sender_id PK
        int sender_seq PK
        string recipient_id
        string frame_digest
        string ciphertext_hash
        text header_b64u
        text ciphertext_b64u
        datetime created_at
    }

    A2A_GROUPS {
        string group_id PK
        string owner_id
        string state
        datetime created_at
    }

    A2A_GROUP_EVENTS {
        string group_id PK
        int seq PK
        string prev_digest
        string digest
        json event_json
        datetime ts
        string actor_id
        string target_id
    }

    A2A_SESSIONS ||--o{ A2A_SESSION_EVENTS : "has events"
    A2A_SESSIONS ||--o{ A2A_FRAMES : "contains frames"
    A2A_GROUPS ||--o{ A2A_GROUP_EVENTS : "has events"
```

## Security Properties

| Property           | Implementation                            |
| ------------------ | ----------------------------------------- |
| Forward Secrecy    | Double Ratchet (per-message keys)         |
| Replay Protection  | UNIQUE(session_id, sender_id, sender_seq) |
| Integrity          | frame_digest = SHA256(canonical preimage) |
| Ciphertext Binding | ciphertext_hash = SHA256(ciphertext)      |
| Single-Writer      | pg_try_advisory_xact_lock                 |
| Concurrent Access  | Fails with A2A_LOCK_CONTENTION            |
