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
For signatures and audit persistence (RFC 8785 strict v1):
- UTF-8 encoding, keys sorted, no whitespace
- Binary fields: **base64url without padding**
- **Strict Limits**:
    - No floats (integers only for timestamps/counters)
    - No NaN/Infinity
    - No duplicate keys
    - Omit null fields (null is invalid)

### 1.3 Hashing (Frozen Formulas)
```
capability_hash = sha256(canonical_json(capability_with_signature))
request_hash    = sha256(canonical_json(mcp_request))
response_hash   = sha256(canonical_json(mcp_response))
```

### 1.4 Signatures (Frozen Formulas)
- Algorithm: **Ed25519**
- Input: `canonical_json(object_minus_signature)`
- Output: 64-byte signature
- Formula: `signature = ed25519_sign(canonical_json(object_minus_signature))`

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

### 8.1 MCP Proxy Frame Signed Field Coverage (v1)
All frames are signed over `canonical_json(frame_minus_signature)` using Ed25519. The signature MUST cover the binding fields that make tool invocation auditable and replay-safe.

**Frame Strictness (v1)**: Unknown top-level frame fields are rejected. MCP payload remains opaque and is bound only by hash.

#### MCP_MESSAGE (Request Frame)
*   `type = "MCP_MESSAGE"`
*   `protocol_version`
*   `session_id`
*   `correlation_id`
*   `peer_id` (sender identity)
*   `issued_at` (int unix seconds - audit ordering only)
*   `request_hash` (sha256 of canonical MCP JSON-RPC request)
*   `tool` (logical identifier, e.g. "tools/call")
*   `method` (logical identifier)
*   `capability_hash` (**REQUIRED always**)
*   `capability` (First request: Present. Follow-up: Omitted. JSON Object embedded in frame)

#### MCP_RESPONSE (Response Frame)
*   `type = "MCP_RESPONSE"`
*   `protocol_version`
*   `session_id`
*   `correlation_id`
*   `peer_id` (responder identity)
*   `issued_at` (int unix seconds - audit ordering only)
*   `response_hash` (sha256 of canonical MCP JSON-RPC response)
*   `tool`
*   `method`
*   `result_code` (OK | DENY | ERROR)
*   `denial_reason` (Optional, present if DENY)
*   `mcp_id` (Recommended)

---

## 9. Versioning

- Protocol version: `_talos_version: 1`
- Breaking changes require version bump
- v1 clients MUST reject unknown versions

---

## 10. Implementation Checklist

- [x] Protobuf schema compiled
- [x] Session cache with LRU eviction
- [x] Bloom filter for revocation
- [x] Async audit queue
- [x] Benchmark: <5ms p99 verified

---

## 11. Agent-to-Agent (A2A) v1 Protocol & Security Extension

### 11.1 Architecture & Separation of Concerns

The Talos A2A ecosystem decouples the core agent communication standard from cryptographic trust and execution backends:

1. **Protocol-Pure Core (`talosprotocol/a2a`):** Open standard data structures, task lifecycle states, multimodal parts, JSON-RPC 2.0 transport, and dual execution drivers (`InMemoryTaskRunner` and `TemporalTaskRunner`).
2. **Cryptographic Security Extension (`talosprotocol/talos-a2a`):** W3C decentralized identifiers (DIDs), forward-secret E2EE sessions, signed capability delegation tokens, and tamper-evident Merkle audit receipts.

```
+-------------------------------------------------------------------------+
|                         Autonomous Calling Agent                        |
+-------------------------------------------------------------------------+
                                     |
                       [JSON-RPC 2.0 / SSE Transport]
                                     v
+-------------------------------------------------------------------------+
|                  A2A Transport Dispatcher & Gateway                     |
+-------------------------------------------------------------------------+
                                     |
        +----------------------------+----------------------------+
        |                                                         |
        v                                                         v
+-----------------------------+             +-----------------------------+
|    InMemoryTaskRunner       |             |     TemporalTaskRunner      |
| (<5ms Edge Asyncio Queues)  |             |  (Durable Cluster Workflows)|
+-----------------------------+             +-----------------------------+
        |                                                         |
        +----------------------------+----------------------------+
                                     v
+-------------------------------------------------------------------------+
|                     Multimodal Message Engine                           |
|       TextPart   |   AudioPart (Opus/PCM)   |   VideoPart (Keyframes)   |
+-------------------------------------------------------------------------+
                                     v
+-------------------------------------------------------------------------+
|                    Talos Zero-Trust Security Layer                      |
|  - W3C Ed25519 DIDs (did:talos:agent:...)                               |
|  - Authenticated Agent Card (/.well-known/agent.json)                   |
|  - ChaCha20-Poly1305 AEAD (Forward-Secret E2EE Channels)                |
|  - Attenuated Capability Tokens (Tool Whitelists & Quotas)              |
|  - Domain-Separated Merkle Audit Trees (SHA-256 Receipts)               |
+-------------------------------------------------------------------------+
```

### 11.2 Task Lifecycle & State Transitions

Every A2A task follows a deterministic state machine:

```
           +-------------+
           |  SUBMITTED  |
           +-------------+
                  |
                  v
           +-------------+      cancel()
           |   WORKING   | -----------------> +-------------+
           +-------------+                    |  CANCELED   |
            |           |                     +-------------+
    success |           | failure
            v           v
     +-----------+ +----------+
     | COMPLETED | |  FAILED  |
     +-----------+ +----------+
```

| State | Terminal? | Description |
|---|---|---|
| `SUBMITTED` | No | Task envelope received, validated, and enqueued. |
| `WORKING` | No | Execution driver active; streaming intermediate progress or tokens. |
| `COMPLETED` | Yes | Task finished successfully with output messages and artifacts. |
| `FAILED` | Yes | Task execution halted with an explicit typed error. |
| `CANCELED` | Yes | Task canceled by caller or supervisory timeout. |

### 11.3 JSON-RPC 2.0 Transport Methods

A2A endpoints expose standard JSON-RPC 2.0 methods:

#### `tasks/send`
Submits a task for synchronous execution (Immediate mode) or returns a task handle (Submit mode):
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{ "text": "Analyze founder sentiment" }]
    },
    "context_id": "ctx-9812",
    "delivery": "immediate"
  },
  "id": "req-01"
}
```

#### `tasks/get`
Retrieves current task state, status messages, and emitted artifacts:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/get",
  "params": { "id": "task-4a9f" },
  "id": "req-02"
}
```

#### `tasks/cancel`
Requests cooperative cancellation of an active task:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/cancel",
  "params": { "id": "task-4a9f", "reason": "User abort" },
  "id": "req-03"
}
```

#### `tasks/list`
Lists recent tasks scoped by context ID or tenant boundary:
```json
{
  "jsonrpc": "2.0",
  "method": "tasks/list",
  "params": { "context_id": "ctx-9812", "limit": 20 },
  "id": "req-04"
}
```

### 11.4 Multimodal Message Parts

A2A messages contain an ordered array of typed parts:

1. **`TextPart`**: Natural language instructions, structured text, or JSON/YAML payloads.
2. **`AudioPart`**: Binary Opus or raw PCM chunks, sample rate negotiation, and streaming buffers (`AudioStreamBuffer`).
3. **`VideoPart`**: Keyframes, video segments, and spatial bounding-box annotations (`BoundingBoxArtifact`).
4. **`Artifact`**: Named outputs (structured datasets, charts, generated files) attached to the task record.

### 11.5 Dual Execution Drivers

1. **`InMemoryTaskRunner`**:
   - Zero external dependencies; leverages Python `asyncio.Queue` and local pub/sub.
   - Designed for sub-second edge instances (e.g. Raspberry Pi), CLI tools, and unit testing.
   - Typical execution dispatch latency: `< 5ms`.
2. **`TemporalTaskRunner`**:
   - Backed by Temporal distributed workflow orchestrators.
   - Provides resilient cross-node task queues, activity heartbeating, automatic retries, and saga compensations.
   - Designed for durable multi-day campaigns, cross-organization swarms, and batch synthesis.

### 11.6 Talos Cryptographic Security Extension

#### 11.6.1 Decentralized Identity (W3C DIDs)
- **Syntax:** `did:talos:agent:<name>:<sha256_fingerprint>`
- **Asymmetric Primitives:** Ed25519 signing keys and X25519 key exchange.
- **Discovery Card:** Published at `/.well-known/agent.json` containing W3C DID document and `Ed25519Signature2020` proof.

#### 11.6.2 End-to-End Encryption (E2EE)
- **Cipher:** ChaCha20-Poly1305 AEAD.
- **Key Agreement:** Ephemeral X25519 Diffie-Hellman producing forward-secret session keys.
- **Associated Authenticated Data (AAD):** Cryptographically binds `sender_did || recipient_did || session_id` to prevent message rerouting or substitution attacks.

#### 11.6.3 Attenuated Capability Tokens
- Compact, signed URL-safe tokens delegating authority from supervisor to worker agents.
- Enforces strict method glob allowlists (e.g. `["tools:read:*", "weather:*"]`).
- Enforces invocation quotas (e.g. maximum 25 tool calls) and expiration timestamps (Unix epoch millis).

#### 11.6.4 Domain-Separated Merkle Audit Receipts
To prevent second-preimage attacks:
- **Leaf Hash:** `sha256(0x00 || canonical_json(event_payload))`
- **Intermediate Node Hash:** `sha256(0x01 || left_child_hash || right_child_hash)`
- Produces a tamper-evident `MerkleReceipt` that can be verified independently by any auditor.
