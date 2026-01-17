---
description: Update pending features with TGA Phase 9 completion
---

# Pending Features & Implementation Status

## ✅ Completed Phases

### Phase 7: RBAC Enforcement (2026-01-15)

- RBAC contracts: binding.schema.json, surface_registry.schema.json
- PolicyEngine with deterministic scope matching
- RBAC middleware with deny-by-default
- 45+ tests passing

### Phase 8: Secrets (2026-01-15)

- Envelope schema and vectors
- SDK KekProvider (AES-256-GCM)
- PostgresSecretStore with rotation

### Phase 9: TGA Hardening (2026-01-15)

- Contracts: AR, SD, TC, TE with trace chaining
- Capability model with JWS/EdDSA
- Tool servers classification (LOCKED)
- Runtime loop with crash recovery
- 219 tests passing

### Phase 10: A2A Channels (2026-01-16)

- **Phase 10.0**: Contracts complete (11 schemas, 155 tests)
- **Phase 10.1**: Gateway surfaces (SessionManager, FrameStore, GroupManager)
  - 12 API endpoints with RBAC enforcement
  - Advisory locks for single-writer safety
  - Replay protection and size limits
  - Alembic migration with UNIQUE/CHECK constraints
- **Phase 10.2**: SDK Adapter ✅
  - A2ATransport HTTP client with retry
  - A2ASessionClient for session lifecycle
  - SequenceTracker for monotonic sender_seq
  - Error mapping to typed exceptions
- **Phase 10.3**: Ratchet Binding ✅
  - RatchetFrameCrypto implementation
  - Double Ratchet integration
  - E2E encryption for A2A frames

### Phase 11: Production Hardening (2026-01-17)

- Rate limiting per principal (Redis/Token Bucket)
- Distributed tracing (OpenTelemetry)
- Health check endpoints (/health/live, /health/ready)
- Graceful shutdown gate

## ✅ SDK Examples (2026-01-16)

- `secrets_demo.py` - Envelope encryption (no keys printed)
- `session_persistence_demo.py` - Save/restore ratchet state
- `multi_message_demo.py` - 10 messages, unique digests
- `a2a_messaging.py` - X3DH + Double Ratchet
- `a2a_live_integration.py` - Gateway integration

## ✅ Benchmarks (2026-01-16)

- Wallet: 55k ops/sec
- Double Ratchet: 50k encrypts/sec
- Canonical JSON: 2.6M ops/sec
- Session serialize: 300k+ ops/sec

## 🔴 Future Phases

### Phase 12: Multi-Region

- Postgres replication
- Session state sync
- Key rotation coordination
