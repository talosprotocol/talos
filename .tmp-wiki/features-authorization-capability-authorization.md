# Capability-Based Authorization

> Per-request cryptographic authorization for MCP tool invocation.

---

## Overview

Talos uses **capability tokens** instead of ACLs for authorization. Capabilities are:

- **Cryptographically signed** by the issuer
- **Scoped** to specific tools and methods
- **Time-bounded** with expiry
- **Revocable** at any time
- **Delegatable** (with scope narrowing only)

---

## Core Concepts

| Concept | Description |
| :--- | :--- |
| **Capability** | Signed token granting access to a scope |
| **Scope** | `tool:<name>/method:<name>/resource:<pattern>` |
| **Issuer** | Authority that signs capabilities |
| **Subject** | Agent receiving the capability |
| **Delegation** | Creating sub-capabilities (scope can only narrow) |

---

## Capability Token Structure

```json
{
  "id": "cap_24ba327720024c64986b37db",
  "version": 1,
  "issuer": "did:talos:issuer",
  "subject": "did:talos:agent",
  "scope": "tool:filesystem/method:read",
  "constraints": {"paths": ["/data/*"]},
  "issued_at": "2024-12-27T00:00:00Z",
  "expires_at": "2024-12-27T01:00:00Z",
  "delegatable": false,
  "delegation_chain": [],
  "signature": "<base64url>"
}
```

---

## Usage

### Granting Capabilities

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from src.core.capability import CapabilityManager

# Create manager with issuer keypair
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()
manager = CapabilityManager("did:talos:issuer", private_key, public_key)

# Grant capability
cap = manager.grant(
    subject="did:talos:agent",
    scope="tool:filesystem/method:read",
    constraints={"paths": ["/data/*"]},
    expires_in=3600,  # 1 hour
    delegatable=True
)
```

### Authorization (Full Path)

```python
result = manager.authorize(
    capability=cap,
    tool="filesystem",
    method="read",
)

if result.allowed:
    print(f"Access granted: {result.capability_id}")
else:
    print(f"Denied: {result.reason}")  # EXPIRED, REVOKED, SCOPE_MISMATCH, etc.
```

### Session-Cached Authorization (Fast Path)

For subsequent requests, use session caching for <1ms authorization:

```python
import secrets

# Cache session after first authorization
session_id = secrets.token_bytes(16)
manager.cache_session(session_id, cap)

# Subsequent requests: <1ms authorization
result = manager.authorize_fast(
    session_id=session_id,
    tool="filesystem",
    method="read",
)
print(f"Latency: {result.latency_us}μs")  # ~4μs typical
```

### Delegation

```python
# Delegate with narrower scope
child_cap = manager.delegate(
    parent_capability=cap,
    new_subject="did:talos:sub-agent",
    narrowed_scope="tool:filesystem/method:read/resource:/data/public/*",
    expires_in=1800  # Capped by parent expiry
)
```

### Revocation

```python
manager.revoke(cap.id, reason="session ended")

# Revocation is checked in authorize_fast via O(1) hash lookup
result = manager.authorize_fast(session_id, "filesystem", "read")
assert result.reason == DenialReason.REVOKED
```

---

## Denial Reasons

| Code | Description |
| :--- | :--- |
| `NO_CAPABILITY` | No capability provided |
| `EXPIRED` | Capability TTL exceeded |
| `REVOKED` | Capability explicitly revoked |
| `SCOPE_MISMATCH` | Requested action outside scope |
| `DELEGATION_INVALID` | Bad delegation chain |
| `UNKNOWN_TOOL` | Tool not in allowed list |
| `REPLAY` | Correlation ID already used |
| `SIGNATURE_INVALID` | Cryptographic verification failed |

---

## Performance SLAs

| Operation | Target | Measured |
| :--- | :--- | :--- |
| `authorize_fast` | <1ms p99 | **0μs avg** |
| `verify` (signature) | <500μs | **154μs avg** |
| Grant | <5ms | **72μs avg** |
| Throughput | >10k/sec | **695k/sec** |

---

## MCP Integration

In the proxy, capabilities are **mandatory** for all requests:

```text
Request 1: capability + session_id → full verify → cache session
Request 2: session_id only       → authorize_fast (<1ms)
Request 3: session_id only       → authorize_fast (<1ms)
...
```

See [MCP Cookbook](integrations-mcp-cookbook) for integration details.

---

## Security Properties

1. **No bypass path** - Every MCP request requires valid capability
2. **Signature verification** - Ed25519 on all capability fields
3. **Scope containment** - Delegated scope must be subset of parent
4. **Revocation overrides** - Revoked capabilities fail even if TTL valid
5. **Replay protection** - Correlation ID checked per session

---

## Related Pages

- [Protocol Specification](PROTOCOL)
- [MCP Cookbook](integrations-mcp-cookbook)
- [Threat Model](architecture-threat-model)
- [Agent Capabilities](agent-capabilities)
