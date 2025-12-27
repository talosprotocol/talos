# Talos Protocol Specification v1.0

> Wire format, message types, and capability semantics for MCP tool invocation security.

---

## 0. Performance Invariants (Non-Negotiable)

### 0.1 Latency SLAs
| Operation | Target | Hard Limit |
|-----------|--------|------------|
| Authorization (cached session) | <1ms | 5ms |
| Signature verification | <500μs | 2ms |
| Revocation check | <100μs | 500μs |
| **Total Talos overhead** | **<2ms p50** | **<5ms p99** |

### 0.2 Audit Path
- Audit events: **async, non-blocking**
- Durability guarantee: best-effort (batch flush every 100ms)
- Critical audit (denials): sync flush within 1s

### 0.3 Session Caching
- Capability signatures verified **once per session**, not per request
- Session validity: check `session_id` + timestamp only on subsequent calls
- Revocation: checked every request (bloom filter, <100μs)

### 0.4 Binary Wire Format
- Talos envelope: **Protobuf** (not JSON)
- MCP payload: JSON (tool compatibility)
- Capability token: Protobuf for wire, JSON for storage/signing

---

## 1. Encoding Rules

### 1.1 Binary Encoding (Hot Path)
Talos fields use **Protocol Buffers v3**:
```protobuf
message TalosEnvelope {
  bytes capability = 1;        // Serialized Capability
  bytes correlation_id = 2;    // 16 bytes
  uint64 timestamp_ms = 3;     // Unix millis
  bytes session_id = 4;        // 16 bytes
  bytes request_hash = 5;      // 32 bytes (sha256)
}
```

### 1.2 Canonical JSON (Signing/Storage)
For signatures and audit persistence:
- UTF-8 encoding, keys sorted, no whitespace
- Binary fields: **base64url without padding**

### 1.3 Hashing
```
request_hash  = sha256(canonical_json(mcp_request))
response_hash = sha256(canonical_json(mcp_response))
```

### 1.4 Signatures
- Algorithm: **Ed25519**
- Input: canonical bytes (excluding `signature` field)
- Output: 64-byte signature

---

## 2. Capability Token

### 2.1 Binary Structure (Wire)
```protobuf
message Capability {
  bytes id = 1;                // 12 bytes
  uint32 version = 2;
  bytes issuer = 3;            // DID bytes
  bytes subject = 4;           // DID bytes
  bytes scope = 5;             // UTF-8 scope string
  bytes constraints = 6;       // CBOR-encoded constraints
  uint64 issued_at_ms = 7;
  uint64 expires_at_ms = 8;
  bool delegatable = 9;
  repeated bytes delegation_chain = 10;
  bytes signature = 11;        // 64 bytes Ed25519
}
```

### 2.2 JSON Structure (Storage/Signing)
```json
{
  "id": "cap_<24-hex-chars>",
  "version": 1,
  "issuer": "did:talos:<issuer-id>",
  "subject": "did:talos:<subject-id>",
  "scope": "tool:<name>/method:<name>",
  "constraints": {},
  "issued_at": "2024-12-27T00:00:00Z",
  "expires_at": "2024-12-27T01:00:00Z",
  "delegatable": false,
  "delegation_chain": [],
  "signature": "<base64url>"
}
```

### 2.3 Scope Grammar
```
scope = tool:<name>[/method:<name>][/resource:<pattern>]
```
Prefix containment: `tool:fs` covers `tool:fs/method:read`.

### 2.4 Expiry Semantics
- `issued_at`, `expires_at` signed
- 60-second skew window
- Revocation overrides validity

---

## 3. Session-Cached Verification

### 3.1 Session Establishment
```
1. Agent presents capability + session_id
2. Verify capability signature (ONCE)
3. Cache: session_id → (capability_hash, verified_at, expires_at)
4. Subsequent requests: check session_id exists + not expired
```

### 3.2 Session Cache Entry
```protobuf
message SessionCacheEntry {
  bytes session_id = 1;
  bytes capability_hash = 2;
  bytes subject = 3;
  bytes scope = 4;
  uint64 verified_at_ms = 5;
  uint64 expires_at_ms = 6;
}
```

### 3.3 Per-Request Fast Path
```python
def authorize_fast(session_id, tool, method):
    entry = session_cache.get(session_id)
    if not entry:
        return FULL_VERIFY  # Fall back to full verification
    
    if time_ms() > entry.expires_at_ms:
        return EXPIRED
    
    if revocation_bloom.maybe_contains(entry.capability_hash):
        # False positives OK, triggers full check
        return FULL_VERIFY
    
    if not scope_covers(entry.scope, tool, method):
        return SCOPE_MISMATCH
    
    return ALLOWED  # <1ms path
```

### 3.4 Revocation Bloom Filter
- False positive rate: 1%
- Size: 10KB per 10k capabilities
- Rebuild: every 10s from revocation list
- Check time: **<100μs**

---

## 4. Authorization

### 4.1 Canonical API
```python
CapabilityManager.authorize(
    capability: Capability,
    tool: str,
    method: str,
    session_id: Optional[bytes] = None
) -> AuthorizationResult
```

### 4.2 Validation (Full Path)
1. Capability issuer signature
2. `issued_at` / `expires_at` (60s skew)
3. Revocation status
4. Delegation chain signatures + scope containment
5. Scope covers `tool:name/method:name`
6. Unknown tool: **deny by default**
7. `correlation_id` not in replay cache
8. **Cache session** for fast path

### 4.3 Denial Reasons
```
NO_CAPABILITY | EXPIRED | REVOKED | SCOPE_MISMATCH
DELEGATION_INVALID | UNKNOWN_TOOL | REPLAY | SIGNATURE_INVALID
```

---

## 5. Audit Event

### 5.1 Structure
```protobuf
message AuditEvent {
  uint32 event_type = 1;       // GRANT=1, DENY=2, INVOKE=3, REVOKE=4
  bytes tool = 2;
  bytes capability_hash = 3;
  bytes request_hash = 4;
  bytes response_hash = 5;
  bytes agent_id = 6;
  bytes tool_id = 7;
  uint64 timestamp_ms = 8;
  uint32 result_code = 9;      // OK=0, DENIED=1, ERROR=2
  uint32 denial_reason = 10;
  bytes signature = 11;
}
```

### 5.2 Async Audit Queue
- Buffer: 1000 events
- Flush: every 100ms or buffer full
- Denial events: priority flush

---

## 6. Replay Protection

### 6.1 Correlation ID
- 16 bytes (128 bits entropy)
- Unique per request within session

### 6.2 Cache
- Size: 10k IDs per session (LRU)
- Eviction: only acked entries
- **Ack** = audit event emitted

---

## 7. Tool Identity

- MCP server signs tool responses
- Tool name is an attribute in audit
- Future: tool-level DIDs

---

## 8. Message Types

| Type | Code | Description |
|------|------|-------------|
| MCP_MESSAGE | 10 | MCP request with Talos envelope |
| MCP_RESPONSE | 11 | MCP response |
| MCP_ERROR | 12 | MCP error |

---

## 9. Versioning

- Protocol version: `_talos_version: 1`
- Breaking changes require version bump
- v1 clients MUST reject unknown versions

---

## 10. Implementation Checklist

- [ ] Protobuf schema compiled
- [ ] Session cache with LRU eviction
- [ ] Bloom filter for revocation
- [ ] Async audit queue
- [ ] Benchmark: <5ms p99 verified
