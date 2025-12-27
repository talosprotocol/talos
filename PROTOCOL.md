# Talos Protocol Specification v1.0

> Wire format, message types, and capability semantics for MCP tool invocation security.

---

## 1. Encoding Rules

### 1.1 Canonical JSON
All signed structures use **Canonical JSON (RFC 8785)**:
- UTF-8 encoding
- Keys sorted lexicographically
- No whitespace between separators
- Binary fields: **base64url without padding**

### 1.2 Hashing
```
request_hash  = sha256(canonical_json(mcp_request))
response_hash = sha256(canonical_json(mcp_response))
```

### 1.3 Signatures
- Algorithm: **Ed25519**
- Input: canonical bytes of structure (excluding `signature` field)
- Output: 64-byte signature

---

## 2. Capability Token

### 2.1 Structure
```json
{
  "id": "cap_<24-hex-chars>",
  "version": 1,
  "issuer": "did:talos:<issuer-id>",
  "subject": "did:talos:<subject-id>",
  "scope": "tool:<name>/method:<name>/resource:<pattern>",
  "constraints": {},
  "issued_at": "2024-12-27T00:00:00Z",
  "expires_at": "2024-12-27T01:00:00Z",
  "delegatable": false,
  "delegation_chain": [],
  "signature": "<base64url>"
}
```

### 2.2 Signed Fields
All fields except `signature`.

### 2.3 Scope Grammar (v1)
```
scope = tool:<name>[/method:<name>][/resource:<pattern>]
```
Prefix containment: `tool:fs` covers `tool:fs/method:read`.

### 2.4 Expiry Semantics
- `issued_at`, `expires_at` are signed
- Verifier uses local time with **60-second skew window**
- Revocation overrides validity

---

## 3. MCP Envelope

### 3.1 Structure
```json
{
  "jsonrpc": "2.0",
  "method": "<tool-method>",
  "params": {},
  "id": 1,
  "_talos_capability": { /* Capability token */ },
  "_talos_correlation_id": "<unique-per-session>",
  "_talos_timestamp": "2024-12-27T00:00:00Z",
  "_talos_session_id": "<session-id>"
}
```

### 3.2 Signed Fields (envelope)
| Field | Required |
|-------|----------|
| correlation_id | Yes |
| capability_hash | Yes |
| request_hash | Yes |
| tool | Yes |
| method | Yes |
| timestamp | Yes |
| session_id | Yes |

---

## 4. Authorization

### 4.1 Canonical API
```python
CapabilityManager.authorize(
    capability: Capability,
    tool: str,
    method: str,
    request_hash: str
) -> AuthorizationResult
```

### 4.2 Validation Checklist
1. Capability issuer signature
2. `issued_at` / `expires_at` (60s skew)
3. Revocation status
4. Delegation chain signatures + scope containment
5. Scope covers `tool:name/method:name`
6. Unknown tool: **deny by default**
7. `correlation_id` not in replay cache

### 4.3 Denial Reasons
```
NO_CAPABILITY | EXPIRED | REVOKED | SCOPE_MISMATCH
DELEGATION_INVALID | UNKNOWN_TOOL | REPLAY | SIGNATURE_INVALID
```

---

## 5. Audit Event

### 5.1 Structure
```json
{
  "event_type": "GRANT|DENY|INVOKE|REVOKE",
  "tool": "<tool-name>",
  "capability_hash": "<sha256>",
  "request_hash": "<sha256>",
  "response_hash": "<sha256>",
  "agent_id": "did:talos:<agent>",
  "tool_id": "did:talos:<tool>",
  "timestamp": "2024-12-27T00:00:00Z",
  "result_code": "OK|DENIED|ERROR",
  "denial_reason": "EXPIRED|REVOKED|...",
  "signature": "<base64url>"
}
```

### 5.2 Signed Fields
All fields except `signature`.

---

## 6. Replay Protection

### 6.1 Correlation ID
- Unique per session
- Cryptographically unpredictable (128+ bits entropy)

### 6.2 Cache
- Size: 10k IDs per session (LRU)
- Eviction: only acked entries
- **Ack** = audit event emitted for this correlation_id

---

## 7. Tool Identity

### 7.1 v1 Model
- MCP server signs tool responses
- Tool name is an attribute in audit
- Optional: tool-level DIDs (future)

---

## 8. Issuer Trust

- Capability issuer is designated authority per org
- Issuer public key: DID document or config
- Verifiers must validate issuer chain

---

## 9. Message Types

| Type | Code | Description |
|------|------|-------------|
| TEXT | 1 | Encrypted text message |
| ACK | 2 | Acknowledgment |
| FILE | 3 | File transfer start |
| FILE_CHUNK | 4 | File chunk |
| FILE_COMPLETE | 5 | File transfer complete |
| MCP_MESSAGE | 10 | MCP request |
| MCP_RESPONSE | 11 | MCP response |
| MCP_ERROR | 12 | MCP error |

---

## 10. Versioning

- Protocol version in envelope: `_talos_version: 1`
- Breaking changes require version bump
- v1 clients MUST reject unknown versions
