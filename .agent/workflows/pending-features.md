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

## 🔴 Planned

### Phase 10.2: SDK Adapter

- HTTP transport client
- Local sequence tracking
- WebSocket (future)

## Dashboard Features (v3.2) ✅

- Denial Taxonomy Chart
- Request Volume Chart
- Export Evidence JSON
- Audit Explorer Page
- Session Intelligence Page
