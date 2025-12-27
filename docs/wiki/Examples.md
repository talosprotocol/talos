# Examples Guide

> Runnable examples demonstrating Talos Protocol features.

## Quick Start

```bash
# Run all examples
python examples/demo_capability.py  # Main demo (recommended first)
python examples/11_capability_auth.py
python examples/12_rate_limiting.py
python examples/13_audit_plane.py
python examples/14_gateway.py
```

---

## Example Index

| Example | Description | Features |
|---------|-------------|----------|
| [demo_capability.py](../../../examples/demo_capability.py) | Full Phase 1-3 demo | All features |
| [01_crypto.py](../../../examples/01_crypto.py) | Cryptographic primitives | Wallet, signatures, encryption |
| [02_blockchain.py](../../../examples/02_blockchain.py) | Blockchain operations | Mining, validation, persistence |
| [03_acl.py](../../../examples/03_acl.py) | Access control | ACL rules, rate limiting |
| [10_sdk_quickstart.py](../../../examples/10_sdk_quickstart.py) | SDK basics | Wallet, Blockchain |
| [11_capability_auth.py](../../../examples/11_capability_auth.py) | **Capability authorization** | Grant, authorize, delegate |
| [12_rate_limiting.py](../../../examples/12_rate_limiting.py) | **Rate limiting** | Token bucket, per-session |
| [13_audit_plane.py](../../../examples/13_audit_plane.py) | **Audit plane** | Events, export JSON/CSV |
| [14_gateway.py](../../../examples/14_gateway.py) | **Gateway** | Multi-tenant, health check |

---

## Phase 1-3 Features Demo

Run the main demo to see all Phase 1-3 features:

```bash
python examples/demo_capability.py
```

### Expected Output

```
============================================================
  TALOS PROTOCOL DEMO - Phase 1-3 Features
============================================================

✓ Created CapabilityManager
  Issuer: did:talos:issuer
  Key type: Ed25519

✓ Granted capability: cap_f9e864...
  Subject: did:talos:agent
  Scope: tool:filesystem/method:read
  Delegatable: True

✓ Authorization result: ALLOWED

✓ Session-cached authorization:
  ├─ Average: 0.1μs
  ├─ p99: 3μs
  └─ Status: ✓ PASS (<1ms target)

✓ Audit events recorded:
  ├─ Total: 3
  ├─ Denials: 1
  └─ Approval rate: 67%

✓ Rate limiter test (burst=5, 10 calls):
  ├─ Allowed: 5
  └─ Blocked: 5
```

---

## Capability Authorization Example

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from src.core.capability import CapabilityManager

# Create manager
private_key = Ed25519PrivateKey.generate()
manager = CapabilityManager(
    issuer_id="did:talos:issuer",
    private_key=private_key,
    public_key=private_key.public_key(),
)

# Grant capability
cap = manager.grant(
    subject="did:talos:agent",
    scope="tool:filesystem/method:read",
    expires_in=3600,
)

# Authorize
result = manager.authorize(cap, "filesystem", "read")
print(f"Allowed: {result.allowed}")  # True

# Session-cached (fast path)
session_id = secrets.token_bytes(16)
manager.cache_session(session_id, cap)
fast_result = manager.authorize_fast(session_id, "filesystem", "read")
print(f"Latency: {fast_result.latency_us}μs")  # ~1μs
```

---

## Rate Limiting Example

```python
from src.core.rate_limiter import SessionRateLimiter, RateLimitConfig

limiter = SessionRateLimiter(RateLimitConfig(
    burst_size=5,
    requests_per_second=2,
))

session = secrets.token_bytes(16)

# First 5 allowed (burst), rest blocked
for i in range(10):
    allowed = limiter.allow(session)
    print(f"Request {i+1}: {'✓' if allowed else '✗'}")
```

---

## Audit Plane Example

```python
from src.core.audit_plane import AuditAggregator

agg = AuditAggregator()

# Record events
agg.record_authorization(
    agent_id="did:talos:agent",
    tool="filesystem", method="read",
    capability_id="cap_123", allowed=True,
)

# Export
print(agg.export_csv())
```

---

## Gateway Example

```python
from src.core.gateway import Gateway, GatewayRequest, TenantConfig

gateway = Gateway()
gateway.register_tenant(TenantConfig(
    tenant_id="tenant1",
    capability_manager=manager,
    allowed_tools=["filesystem", "database"],
))
gateway.start()

response = gateway.authorize(GatewayRequest(
    request_id="req1",
    tenant_id="tenant1",
    session_id=session_id,
    tool="filesystem",
    method="read",
))
print(f"Allowed: {response.allowed}")
```

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Specific modules
pytest tests/test_capability.py -v      # Capability authorization
pytest tests/test_performance.py -v     # Performance SLAs
pytest tests/test_red_team.py -v        # Security tests
pytest tests/test_gateway.py -v         # Gateway tests
```

---

## See Also

- [Capability Authorization](Capability-Authorization.md)
- [Testing](Testing.md)
- [RUNBOOK](../../../RUNBOOK.md)
