# Phase 9: talos-governance-agent (TGA)

This phase defines a production-grade governance agent named `talos-governance-agent`.

## Goal

Build an operator agent that can read, reason, propose, and execute operational actions with:

- strict security boundaries
- capability-based authorization
- encrypted transport (Talos)
- end-to-end audit traceability

## Non-negotiable principles (locked)

1. No direct tool calls
   - TGA calls tools only via Talos-protected MCP, typically through the gateway.

2. Contract-first
   - All schemas and vectors live in `talos-contracts`.

3. Supervisor authority
   - All nontrivial writes require supervisor decision and (when approved) a minted capability.

4. Determinism
   - Writes require idempotency keys.
   - Schemas must be stable.

## Concrete repo tree

### New repo: talos-governance-agent/

Recommended structure:

- `cmd/`
  - `tga/` (CLI entrypoint)
- `internal/`
  - `runtime/` (agent loop, message handling)
  - `supervisor/` (approval logic, risk tiers, capability minting)
  - `validation/` (schema validation, vector runner integration)
  - `connectors/`
    - `gateway/` (Talos gateway client)
    - `mcp/` (MCP client wrapper)
    - `a2a/` (A2A and A2-multi transport adapter)
- `tests/`
  - `integration/`
  - `vectors/` (copied from contracts release set in CI)
- `configs/`
  - `policies/` (supervisor policy config)

### talos-contracts/

- `schemas/talos_governance_agent/`
  - `action_request.schema.json`
  - `supervisor_decision.schema.json`
  - `tool_call.schema.json`
- `test_vectors/talos_governance_agent/`
  - `valid.json`
  - `invalid.json`

### talos-mcp-connector/

- MCP tool servers used by TGA:
  - `mcp-github`
  - `mcp-docs`
  - `mcp-social`
  - `mcp-onchain`

Hard rule: tool servers must not allow raw passthrough to third-party APIs.

## Runtime workflow (MVP)

1. Propose
   - TGA produces an `ActionRequest`.

2. Decide
   - Supervisor returns a `SupervisorDecision`:
     - `deny`
     - `needs_approval`
     - `approve` with a minted capability

3. Execute
   - TGA constructs a `ToolCall` using the minted capability and calls via gateway.

4. Observe
   - Tool returns deterministic effect identifiers.

5. Audit chain
   - The audit system can reconstruct: plan -> proposal -> decision -> tool_call -> effect.

## Risk tiers (locked intent)

- Tier 0: read-only, auto-approve
- Tier 1: write, requires explicit approval
- Tier 2: high risk, requires multi-approval or offline signing

## Schemas

The canonical Draft 2020-12 schemas for v1 are in:

- `schemas/talos_governance_agent/action_request.schema.json`
- `schemas/talos_governance_agent/supervisor_decision.schema.json`
- `schemas/talos_governance_agent/tool_call.schema.json`

## MVP exit criteria

- Supervisor gating works end-to-end for Tier 1 writes.
- All TGA payloads validate against contracts schemas.
- No direct tool calls bypass gateway.
- A2A channel used for multi-agent coordination.
