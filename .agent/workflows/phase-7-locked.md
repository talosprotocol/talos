---
description: Phase 7 RBAC Enforcement - LOCKED SPEC
---

# Phase 7: RBAC Enforcement

## Status

LOCKED SPEC

## Goal

Enforce least-privilege authorization at the Gateway using contract-defined RBAC roles and bindings, deterministic scope matching, and a manifest-first Surface Registry that maps external routes to permissions and scope derivation. Enforcement MUST be deny-by-default in production.

---

## Security Invariants (Non-Negotiable)

1. Contract-First RBAC
   RBAC inputs MUST be validated against versioned contracts artifacts in `talos-contracts`:

   - `schemas/rbac/role.schema.json`
   - `schemas/rbac/binding.schema.json`
   - `schemas/gateway/surface_registry.schema.json`
     Service repos MUST NOT define ad hoc RBAC schemas.

2. Deterministic Authorization
   Given identical `(principal, permission, scope, bindings, roles)`, the PolicyEngine MUST produce the exact same `AuthzDecision` including stable reason codes and matched artifacts.

3. Deny-by-Default

   - Unmapped surfaces in production MUST be denied.
   - Missing role or binding references MUST be denied.
   - Invalid scope derivation MUST be denied.

4. Surface Registry Completeness Gate
   All externally reachable routes MUST have a Surface Registry mapping. CI MUST fail on unmapped routes.

5. Auditability
   Every request passing through RBAC middleware MUST emit normalized authz fields in audit events.

---

## Phase 7.0: RBAC Contracts (BLOCKING)

### Repo

`talos-contracts`

### Deliverables

- `schemas/rbac/binding.schema.json`
- Update `schemas/rbac/role.schema.json` to Draft 2020-12 strictness
- `test_vectors/rbac/scope_match_vectors.json`
- `schemas/gateway/surface_registry.schema.json`

### Schema Strictness (All)

- Draft 2020-12
- `schema_id`: const string
- `schema_version`: const `"v1"`
- `additionalProperties: false`
- If `$ref` or composition: `unevaluatedProperties: false`

### Binding Schema (Normative)

```json
{
  "schema_id": "talos.rbac.binding",
  "schema_version": "v1",
  "principal_id": "user_123",
  "team_id": "team_abc",
  "bindings": [
    {
      "binding_id": "bind_001",
      "role_id": "role_admin",
      "scope": {
        "scope_type": "repo",
        "attributes": { "repo": "talosprotocol/talos" }
      }
    }
  ]
}
```

### Scope Matching Semantics (Normative)

1. `global` matches any request scope, specificity = 0
2. `scope_type` MUST equal (no implicit cross-type matching)
3. Attribute matching:
   - Exact match: +2 specificity
   - Wildcard `"*"`: +1 specificity
4. Tie-break: highest specificity, then lexicographically smallest `binding_id`

---

## Phase 7.1: Gateway PolicyEngine (BLOCKING)

### Repo

`talos-ai-gateway`

### Deliverables

- `app/domain/rbac/models.py`
- `app/domain/rbac/policy_engine.py`
- `app/middleware/rbac.py`
- Tests with `scope_match_vectors.json`

### AuthzDecision (Normative)

```json
{
  "allowed": true,
  "reason_code": "RBAC_PERMISSION_ALLOWED",
  "principal_id": "user_123",
  "permission": "secrets.read",
  "request_scope": { "scope_type": "repo", "attributes": { "repo": "..." } },
  "matched_role_ids": ["role_admin"],
  "matched_binding_ids": ["bind_001"],
  "effective_role_id": "role_admin",
  "effective_binding_id": "bind_001"
}
```

### PolicyEngine Interface

```python
class PolicyEngine:
    async def load_roles(self) -> dict[str, Role]
    async def load_bindings(self, principal_id: str) -> list[Binding]
    async def resolve(self, principal_id: str, permission: str, request_scope: Scope) -> AuthzDecision
```

---

## Phase 7.2: Surface Registry (BLOCKING)

### Repo

`talos-ai-gateway` + `talos-contracts`

### Surface Registry Schema

```json
{
  "schema_id": "talos.gateway.surface_registry",
  "schema_version": "v1",
  "routes": [
    {
      "method": "GET",
      "path_template": "/v1/secrets/{secret_id}",
      "permission": "secrets.read",
      "scope_template": {
        "scope_type": "secret",
        "attributes": { "secret_id": "{secret_id}" }
      }
    }
  ]
}
```

### Completeness Gate

- CI MUST fail on unmapped routes
- Production: deny unmapped with `RBAC_SURFACE_UNMAPPED_DENIED`

---

## Stable Error Codes

- `RBAC_SURFACE_UNMAPPED_DENIED`
- `RBAC_PERMISSION_DENIED`
- `RBAC_SCOPE_MISMATCH`
- `RBAC_BINDING_NOT_FOUND`
- `RBAC_ROLE_NOT_FOUND`
- `RBAC_POLICY_ERROR`
- `RBAC_PERMISSION_ALLOWED`

---

## Audit Requirements

Every RBAC-enforced request MUST emit:

- `authz_decision`: `"ALLOW" | "DENY"`
- `authz_reason_code`: stable code
- `permission`: string
- `scope_type`: string
- `scope_attributes`: object
- `matched_role_ids` / `matched_binding_ids` (only when allowed)

---

## Verification Plan

### Unit Tests

- Scope matching against vectors
- Deterministic tie-breaking
- Stable reason codes

### Integration Tests

- Unmapped route denied in production
- Mapped route requires permission + scope match
- Audit fields present on allow and deny

### Adversarial Vectors

- Binding references missing role
- Duplicate binding_ids
- Wildcard overuse
- Placeholder mismatch in scope derivation
