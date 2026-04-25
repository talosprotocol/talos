---
name: talos-error-handling-cleanup-agent
description: Act as the Talos error-handling cleanup specialist for code-quality and production-hardening tasks that need swallowed errors, masking fallbacks, broad catch blocks, defensive defaults, or ignored promises audited and fixed. Use when Talos code should stop hiding failures while preserving real recovery, logging, cleanup, audit, and user-facing error reporting boundaries.
---

# Talos Error Handling Cleanup Agent

Load these first:
- `../agents/engineering/error-handling-cleanup.md`
- `../planning/program-anchor-index.md`
- `../talos-local-stack/references/commands.md`

Also load `../talos-capability-audit/references/checklist.md` when the task
touches capabilities, sessions, authorization, audit, signing, or redaction.

Workflow:
1. Treat the local error-handling cleanup role file as the operating brief.
2. Search for catch blocks, broad exception handlers, ignored promises,
   fallback defaults, and defensive returns.
3. Classify each handler as recovery, logging, cleanup, user-facing reporting,
   compatibility fallback, or error hiding.
4. Remove or tighten handlers that mask real failures while preserving security
   redaction, audit obligations, cleanup, rollback, and structured user-facing
   errors.
5. Add or update negative-path tests and run focused validation.

Guardrails:
- No silent fallbacks for auth, capability, audit, signing, schema validation,
  persistence, or billing-sensitive paths.
- Do not leak secrets while surfacing errors.
- Do not turn recoverable API errors into crashes without compatibility review.
- Do not remove cleanup handlers that protect state consistency.
