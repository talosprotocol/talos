# Capability And Audit Checklist

Primary docs:
- `../../../../docs/features/authorization/agent-capabilities.md`
- `../../../../docs/features/authorization/access-control.md`
- `../../../../docs/features/observability/audit-use-cases.md`
- `../../../../docs/reference/failure-modes.md`

High-signal tests:
- `../../../../tests/test_red_team.py`
- `../../../../tests/test_policy_equivalence.py`
- `../../../../tests/test_gateway.py`
- `../../../../tests/test_acl.py`
- `../../../../tests/test_mcp_integration.py`

Questions to answer before changing code:
- Who signs or grants the capability?
- Where is scope enforced?
- What blocks replay, expiry abuse, or revocation bypass?
- What audit record is expected on success and on denial?
- Which test currently proves the invariant, and what new case is missing?

Common regressions to guard against:
- Accepting capabilities with invalid, missing, or mismatched signatures.
- Caching or reusing sessions across different scopes or principals.
- Treating omitted fields as `null` or vice versa in strict schemas.
- Allowing unlogged authorization decisions on sensitive paths.
