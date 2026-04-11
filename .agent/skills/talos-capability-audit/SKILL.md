---
name: talos-capability-audit
description: Use when changing capability issuance, authz enforcement, gateway policy checks, audit logging, agent identity, session validation, revocation, or security-sensitive tests in Talos. Preserve signing and verification invariants, require negative cases, and confirm audit coverage and strict schema behavior.
---

# Talos Capability Audit

Use this skill for security-sensitive Talos changes around identity,
capabilities, sessions, gateway authorization, and audit trails.

Load only what the task needs:
- `references/checklist.md`
- The closest module `AGENTS.md`
- The implementation files on the validation path

Workflow:
1. Identify the trust boundary: issuer, subject, resource, action, session, and
   audit sink.
2. Trace the full validation path before editing. Check creation, transport,
   verification, caching, revocation, and logging.
3. Preserve strictness first: signatures, expiry windows, replay protection,
   scope checks, and schema rejection rules.
4. Add negative coverage for malformed, expired, replayed, or over-scoped
   inputs. Security-sensitive paths should not rely on happy-path tests alone.
5. Verify that important authorization decisions still emit auditable events or
   keep their documented logging behavior.

Guardrails:
- Do not introduce unsigned or weakly validated fallbacks.
- Do not weaken replay, revocation, or expiry handling for convenience.
- Do not mock away critical security checks if a real-path test is practical.
- Do not silently broaden capability scope, delegation, or tool access.

Done checklist:
- Validation path reviewed end to end.
- Negative tests added or updated for the changed behavior.
- Audit behavior verified for allow and deny paths when applicable.
- Final summary names the preserved invariants and any residual risk.
