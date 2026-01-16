---
description: Phase 9.2 Tool Servers Read/Write Separation - LOCKED SPEC
---

# Phase 9.2: Tool Servers Read/Write Separation and Document Hardening

## Status

**LOCKED SPEC**

## Goal

Implement least-privilege tool execution by classifying tools as **read** or **write**, enforcing classification **manifest-first**, and hardening document operations with **size limits** and **normative hashing** for auditability and tamper detection.

---

## Security Invariants (Non-Negotiable)

1. **Manifest-First Classification**
   Tool classification MUST come from `schemas/mcp/tool_registry.schema.json` (a versioned contracts artifact).
   Heuristics are dev-only fallback and MUST fail closed in production.

2. **Defense in Depth**
   Enforcement MUST occur at:

   - Connector (PRIMARY, closest to execution)
   - Gateway (SECONDARY, belt-and-suspenders)

3. **Normative Hashing**
   Content hash preimage MUST be explicitly defined:

   - `utf8`: UTF-8 encoding of the exact string bytes
   - `base64`: base64-decoded bytes
     NO newline normalization.
     Hash mismatch MUST deny execution BEFORE tool invocation.

4. **Registry Parity**
   Gateway and connector MUST use the same pinned tool registry version to prevent split-brain enforcement.

5. **Deny-by-Default**
   If `{server_id, tool_name}` is not present in the registry, tool is **UNCLASSIFIED** and MUST be denied in production.

---

## Phase 9.2.0: Tool Registry Contract (BLOCKING)

### Deliverable

`schemas/mcp/tool_registry.schema.json`

### Schema Headers and Strictness

- `schema_id`: const `"talos.mcp.tool_registry"`
- `schema_version`: const `"v1"`
- `additionalProperties: false`
- If `$ref` or composition is used: root MUST include `unevaluatedProperties: false`

### Structure (Normative)

```json
{
  "schema_id": "talos.mcp.tool_registry",
  "schema_version": "v1",
  "server_id": "mcp-github",
  "server_version": "1.0.0",
  "tools": [
    {
      "tool_name": "create-pr",
      "tool_class": "write",
      "is_document_op": true,
      "document_spec": {
        "content_encoding": "utf8",
        "write_content_pointers": ["/body", "/files/0/content"],
        "read_content_pointers": [],
        "max_read_bytes": 10485760,
        "max_write_bytes": 5242880,
        "max_batch_bytes": 52428800
      }
    }
  ]
}
```

### Required Fields

- `server_id`
- `tools[].tool_name` (exact match)
- `tools[].tool_class`: `"read" | "write"`
- `tools[].is_document_op`: boolean
- If `is_document_op=true`, `tools[].document_spec` REQUIRED
- `document_spec.content_encoding`: `"utf8" | "base64"`
- `document_spec.write_content_pointers`: required for write document ops
- `document_spec.read_content_pointers`: required for read document ops
- Size fields default to: 10MB read, 5MB write, 50MB batch if not provided

### Pointer Dialect

All content location references MUST be **JSON Pointer (RFC 6901)**, not JSONPath.

### Deny-by-Default Rule

If `{server_id, tool_name}` missing from registry:

- `TOOL_UNCLASSIFIED_DENIED` in production

---

## Phase 9.2.1: Connector Enforcement (PRIMARY)

### Repo

`talos-mcp-connector`

### Component

`connector/domain/tool_policy.py`

### Enforcement Rules

#### A) Registry Resolution

- Resolve policy from `{server_id, tool_name}`
- If UNCLASSIFIED: deny with `TOOL_UNCLASSIFIED_DENIED` (prod)

#### B) Tool Class vs Capability

If `capability.constraints.read_only == true` AND registry `tool_class == "write"`:

- deny with `TOOL_CLASS_MISMATCH`

#### C) Document Operation Validation

**Pre-exec (write tools):**

- Extract bytes from `write_content_pointers` in request args
- Decode per `content_encoding`
- Enforce: each item ≤ `max_write_bytes`, total ≤ `max_batch_bytes`
- Compute per-item hashes: `sha256(preimage_bytes)` (lowercase hex)
- If `expected_document_hashes` provided, must match; mismatch → `DOC_HASH_MISMATCH`
- Deny occurs BEFORE tool invocation

**Post-exec (read tools):**

- Extract bytes from `read_content_pointers` in tool result
- Enforce: each item ≤ `max_read_bytes`, total ≤ `max_batch_bytes`
- Compute per-item hashes and attach to `tool_effect`

#### D) Deterministic Hash Attachment

Connector MUST populate `tool_effect.document_hashes[]`:

```json
{
  "document_hashes": [{ "pointer": "/body", "hash": "…", "size_bytes": 1234 }],
  "batch_total_bytes": 1289,
  "content_hash_alg": "sha256"
}
```

#### E) Idempotency

If registry `tool_class == "write"`:

- `tool_call.idempotency_key` REQUIRED
- Missing → `IDEMPOTENCY_KEY_REQUIRED`

### Stable Error Codes

- `TOOL_UNCLASSIFIED_DENIED`
- `TOOL_CLASS_MISMATCH`
- `DOC_SIZE_EXCEEDED`
- `DOC_HASH_MISMATCH`
- `DOC_CONTENT_POINTER_INVALID`
- `DOC_ENCODING_INVALID`
- `IDEMPOTENCY_KEY_REQUIRED`

---

## Phase 9.2.2: Gateway Enforcement (SECONDARY)

### Repo

`talos-ai-gateway`

### Rules

1. Validate `tool_call` schema
2. Load pinned tool registry (same version) and re-derive `tool_class`
3. Enforce: UNCLASSIFIED → deny, `read_only=true` cannot invoke `write`
4. If agent `tool_call.tool_class` mismatches registry → `TOOL_CLASS_DECLARATION_MISMATCH`
5. Emit audit events with `tool_class`, `document_hashes`, `batch_total_bytes`

**Gateway MUST NOT trust agent-provided `tool_class` for authorization.**

---

## Phase 9.2.3: Schema Updates

### `tool_call.schema.json`

- `tool_class` (optional, informational)
- `expected_document_hashes[]`
- `content_hash_alg`: const `"sha256"`

### `tool_effect.schema.json`

- `effect_id`: strict UUIDv7
- `document_hashes[]`
- `batch_total_bytes`
- `content_hash_alg`: const `"sha256"`

---

## Anti-Bypass Notes (Normative)

- Unknown tools: Dev MAY allow with warnings; Prod MUST deny
- Registry MUST be from versioned contracts artifacts, not ad hoc JSON
- Connector and gateway MUST share the same registry version
