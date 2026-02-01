# Phase 1.1: CapabilityManager Integration in proxy.py

## Pre-Implementation Analysis (per Discipline Protocol)

---

## Goal and Invariants

1. **CapabilityManager becomes sole enforcement surface** - ACLManager deprecated
2. **Mandatory capability check** - No bypass path; every MCP request requires valid capability
3. **Fail closed** - Missing/invalid capability = rejection + audit denial event
4. **Per-request verification** - Capability checked on every request, not per session
5. **Revocation overrides validity** - Even if TTL not expired
6. **Unknown tools denied by default** - Log denial with reason
7. **Backward compatibility** - Existing API consumers get clear deprecation warning
8. **Audit always** - Both approvals and denials emit audit events

---

## Edge Cases and Gotchas

1. **Concurrent requests** - Multiple requests with same capability during expiry window
2. **Clock skew** - Capability issued by remote server with different clock
3. **Replay attack** - Same correlation_id reused
4. **Delegation chain** - Deep chains need recursive verification
5. **Partial failure** - Capability valid but tool execution fails
6. **Session vs Request** - Session survives capability expiry, individual requests fail
7. **Migration path** - Existing `acl_manager` users need clear migration

---

## Design Decisions

| Decision | Rule |
|----------|------|
| **Authorization method** | `CapabilityManager.authorize(envelope, request_hash, tool, method, resource)` |
| **Denial reasons** | Use taxonomy: NO_CAPABILITY, EXPIRED, REVOKED, SCOPE_MISMATCH, etc. |
| **Audit emission** | CapabilityManager emits, not proxy |
| **Optional → Mandatory** | `capability_manager` param required, `acl_manager` deprecated |

---

## API Changes

### proxy.py MCPServerProxy

```python
# OLD (deprecated)
def __init__(self, engine, allowed_client_id, command, acl_manager=None)

# NEW (v3.0)
def __init__(self, engine, allowed_client_id, command, capability_manager)  # Required
```

### capability.py CapabilityManager

Add `authorize()` method:

```python
def authorize(
    self,
    capability: Capability,
    tool: str,
    method: str,
    request_hash: str,
    correlation_id: str,
) -> AuthorizationResult:
    """
    Authorize an MCP request.
    
    Returns AuthorizationResult with allowed/denied + reason.
    Emits audit event.
    """
```

---

## Test Plan

### Unit Tests
- `test_proxy_requires_capability` - Reject request without capability
- `test_proxy_rejects_expired_capability` - EXPIRED denial
- `test_proxy_rejects_revoked_capability` - REVOKED denial  
- `test_proxy_rejects_scope_mismatch` - SCOPE_MISMATCH denial
- `test_proxy_denies_unknown_tool` - UNKNOWN_TOOL denial

### Adversarial Tests
- `test_replayed_request_rejected` - Same correlation_id rejected
- `test_delegation_scope_widening_fails` - Can't expand scope

### Regression Tests
- `test_acl_manager_deprecation_warning` - ACL users get warning

---

## Security Risk Assessment

| Risk | Mitigation |
|------|------------|
| **Silent bypass** | No `if capability_manager` check—always required |
| **Signature reuse** | Context prefix in signature (future) |
| **Replay** | Correlation ID cache (10k/session LRU) |
| **Clock manipulation** | Server-side time source for expiry |

---

## Think Harder Questions

1. **What could go wrong in production?** - Missing capability_manager raises clear error, not silent bypass
2. **How would attacker abuse?** - Replay blocked by correlation_id cache
3. **Irrecoverable state?** - None; capabilities are stateless tokens
4. **Silent authorization bypass?** - Prevented by mandatory check + audit
5. **Worst plausible bug?** - Clock skew causing premature/late expiry → configurable skew window

---

## Implementation Plan

1. Add `DenialReason` enum to `capability.py`
2. Add `AuthorizationResult` dataclass to `capability.py`
3. Add `authorize()` method to `CapabilityManager`
4. Update `MCPServerProxy.__init__` to require `capability_manager`
5. Replace ACL check with capability check in `handle_bmp_message`
6. Add deprecation warning for `acl_manager` param
7. Add tests
8. Update docs
