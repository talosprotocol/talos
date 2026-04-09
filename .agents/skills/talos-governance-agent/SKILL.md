---
name: talos-governance-agent
description: Use when working on Talos governance-agent or TGA behavior, supervisor decisions, approval gates, minted capabilities, tool-call orchestration, or operator workflows. Preserve no-direct-tool-call rules, supervisor authority, schema validation, deterministic effect tracing, and audit chain reconstruction.
---

# Talos Governance Agent

Use this skill for governance-agent and TGA-oriented work.

Load only what the task needs:
- `references/tga-map.md`
- `../../../.agent/planning/tga-plan.md`
- `../../../.agent/planning/program-anchor-index.md`
- The closest module `AGENTS.md`

Workflow:
1. Identify where the change sits in the TGA flow: propose, decide, execute,
   observe, or audit.
2. Confirm the approval and capability model before editing. Nontrivial writes
   must remain supervisor-gated.
3. Preserve the execution boundary: tools are reached via Talos-protected paths,
   typically through the gateway, not by direct third-party calls.
4. Update schemas, validation, and idempotency handling when payload shapes or
   decision logic change.
5. Add or update tests that prove the chain can still be reconstructed across
   action request, supervisor decision, tool call, and resulting effect.

Guardrails:
- Do not add direct tool bypasses around gateway or MCP protections.
- Do not weaken supervisor approval for write or high-risk actions.
- Do not accept unvalidated or non-deterministic model output as an execution
  artifact.

Done checklist:
- TGA stage and risk tier identified.
- Supervisor and capability invariants preserved.
- Validation and audit chain coverage updated.
- Final summary calls out the affected stage and verification scope.
