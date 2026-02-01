---
status: Implemented
audience: Developer, Security
---

# Wire Format

> **Problem**: Implementers need to understand message structure.  
> **Guarantee**: Canonical format definitions.  
> **Non-goal**: Full protocol spec—see code for authoritative implementation.

---

## Message Envelope

Every Talos message follows this envelope structure:

```json
{
  "version": 2,
  "type": "MESSAGE",
  "id": "msg_7f3k2m4n8p1q",
  "timestamp": "2024-01-15T10:23:45.123Z",
  "sender": "did:talos:alice_7f3k2m",
  "recipient": "did:talos:bob_9x2p1q",
  "payload": "<base64-encoded-encrypted-content>",
  "signature": "<base64-encoded-signature>"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | int | Yes | Protocol version (currently 2) |
| `type` | string | Yes | Message type enum |
| `id` | string | Yes | Unique message ID (prefixed) |
| `timestamp` | string | Yes | ISO 8601 with milliseconds |
| `sender` | string | Yes | Sender DID or peer ID |
| `recipient` | string | Yes | Recipient DID or peer ID |
| `payload` | string | Yes | Base64-encoded encrypted content |
| `signature` | string | Yes | Base64-encoded Ed25519 signature |

---

## Message Types

| Type | Purpose |
|------|---------|
| `MESSAGE` | Encrypted user message |
| `SESSION_INIT` | Session initiation request |
| `SESSION_ACK` | Session acknowledgment |
| `PREKEY_REQUEST` | Request prekey bundle |
| `PREKEY_RESPONSE` | Prekey bundle delivery |
| `CAPABILITY_GRANT` | Capability token delivery |
| `CAPABILITY_REVOKE` | Capability revocation notice |
| `ACK` | Message acknowledgment |
| `ERROR` | Error response |
| `MCP_REQUEST` | MCP tool invocation |
| `MCP_RESPONSE` | MCP tool response |

---

## Payload Structure

The encrypted payload contains:

```json
{
  "content_type": "text/plain",
  "content": "<actual-message-content>",
  "metadata": {
    "reply_to": "msg_previous",
    "thread_id": "thread_abc"
  }
}
```

### Content Types

| Type | Description |
|------|-------------|
| `text/plain` | Plain text message |
| `application/json` | Structured data |
| `application/octet-stream` | Binary data |
| `application/mcp+json` | MCP JSON-RPC |

---

## Encryption Format

Encrypted payloads use:

```
[32-byte nonce][ciphertext][16-byte tag]
```

- **Algorithm**: ChaCha20-Poly1305 (AEAD)
- **Nonce**: Random 32 bytes (256 bits)
- **Key**: Derived from Double Ratchet

### Key Derivation

```
message_key = HKDF(
    ikm=ratchet_chain_key,
    salt=message_counter,
    info="talos-message-key",
    length=32
)
```

---

## Signature Coverage

The signature covers (in order):

1. `version` (as 4-byte big-endian)
2. `type` (UTF-8 bytes)
3. `id` (UTF-8 bytes)
4. `timestamp` (UTF-8 bytes)
5. `sender` (UTF-8 bytes)
6. `recipient` (UTF-8 bytes)
7. `payload` (raw bytes, not base64)

### Canonicalization

Before signing:
1. All strings normalized to NFC Unicode
2. Timestamps in UTC, ISO 8601 format
3. No whitespace in JSON
4. Fields in defined order

```python
def canonicalize_for_signature(msg):
    return (
        msg.version.to_bytes(4, 'big') +
        msg.type.encode('utf-8') +
        msg.id.encode('utf-8') +
        msg.timestamp.encode('utf-8') +
        msg.sender.encode('utf-8') +
        msg.recipient.encode('utf-8') +
        base64.b64decode(msg.payload)
    )
```

---

## Prekey Bundle Format

```json
{
  "identity_key": "<base64-ed25519-public>",
  "signed_prekey": {
    "key": "<base64-x25519-public>",
    "signature": "<base64-signature>",
    "id": 1
  },
  "one_time_prekeys": [
    {"key": "<base64-x25519-public>", "id": 100},
    {"key": "<base64-x25519-public>", "id": 101}
  ]
}
```

### Key Types

| Key | Algorithm | Purpose |
|-----|-----------|---------|
| Identity | Ed25519 | Long-term signing |
| Signed prekey | X25519 | Medium-term DH |
| One-time prekeys | X25519 | Single-use DH |

---

## Capability Token Format

```json
{
  "id": "cap_7f3k2m4n",
  "version": 1,
  "issuer": "did:talos:owner",
  "subject": "did:talos:grantee",
  "scope": "tools/filesystem/read",
  "constraints": {
    "paths": ["/data/*"],
    "rate_limit": "100/hour"
  },
  "issued_at": "2024-01-15T10:00:00Z",
  "expires_at": "2024-01-15T11:00:00Z",
  "delegatable": false,
  "signature": "<base64-signature>"
}
```

### Capability Signature

Signs (in order):
1. `id`
2. `version`
3. `issuer`
4. `subject`
5. `scope`
6. `constraints` (canonical JSON)
7. `issued_at`
8. `expires_at`
9. `delegatable`

---

## Audit Entry Format

```json
{
  "height": 142,
  "timestamp": "2024-01-15T10:23:45Z",
  "type": "MESSAGE",
  "hash": "0x4d2e8f3a...",
  "previous_hash": "0x9a3f1b7c...",
  "data": {
    "sender": "did:talos:alice",
    "recipient": "did:talos:bob",
    "content_hash": "0xabcd1234..."
  },
  "signature": "<base64-signature>"
}
```

### Block Hashing

```
block_hash = SHA256(
    height || timestamp || type || previous_hash || data_hash
)
```

---

## MCP Message Format

### Request

```json
{
  "type": "MCP_REQUEST",
  "payload": {
    "jsonrpc": "2.0",
    "id": "req_123",
    "method": "tools/call",
    "params": {
      "name": "filesystem/read",
      "arguments": {"path": "/data/file.txt"}
    }
  },
  "capability_id": "cap_7f3k2m4n"
}
```

### Response

```json
{
  "type": "MCP_RESPONSE",
  "payload": {
    "jsonrpc": "2.0",
    "id": "req_123",
    "result": {
      "content": "file contents..."
    }
  },
  "execution_hash": "0x..."
}
```

---

## Size Limits

| Component | Limit |
|-----------|-------|
| Message ID | 64 bytes |
| Payload | 10 MB |
| Capability scope | 256 bytes |
| Constraints JSON | 4 KB |
| Prekey bundle | 8 KB |

---

## Encoding

| Data | Encoding |
|------|----------|
| Binary (keys, signatures) | Base64 (standard, with padding) |
| JSON | UTF-8, no BOM |
| Hashes | Lowercase hex with 0x prefix |
| Timestamps | ISO 8601 with Z suffix |

---

**See also**: [Schemas](api-schemas) | [Cryptography](security-cryptography) | [API Reference](api-api-reference)
