---
id: error-handling-cleanup
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Error Handling Cleanup

## Purpose
Find error handling that hides failures in Talos and remove silent swallowing or
masking fallbacks while preserving real recovery, cleanup, logging, and
user-facing reporting boundaries.

## When to use
- Try/catch, broad `except`, promise `.catch`, fallback defaults, or defensive
  branches may be hiding defects.
- A production-readiness pass needs error handling to fail loudly where
  recovery is not real.
- A bug report points to swallowed errors, misleading fallbacks, or missing
  audit/log evidence.

## Outputs you produce
- Error-handling inventory with keep, change, or remove decisions
- Boundary rationale for retained recovery paths
- Patch that exposes hidden failures safely
- Tests or smoke checks for the changed failure mode

## Default workflow
1. Search the scope for catch blocks, broad exception handlers, fallback
   defaults, ignored promises, and defensive returns.
2. Classify each handler as recovery, logging, cleanup, user-facing reporting,
   compatibility fallback, or error hiding.
3. Remove or tighten handlers that mask real failures, and preserve handlers
   that create actionable logs, cleanup resources, or return intentional API
   errors.
4. Keep security redaction and audit obligations intact when surfacing errors.
5. Add or update tests for negative paths and run the smallest affected
   validation.

## Global guardrails
- No silent fallbacks for auth, capability, audit, signing, schema validation,
  persistence, or billing-sensitive paths.
- Do not leak secrets or sensitive payloads while making errors more visible.
- Do not convert recoverable user-facing errors into crashes without an API
  compatibility decision.
- Prefer typed, structured errors at service boundaries.

## Do not
- Do not keep catch blocks that only return default success or empty data.
- Do not hide an upstream failure behind an unrelated generic message.
- Do not remove cleanup or rollback handlers that protect state consistency.

## Prompt snippet
```text
Act as the Talos Error Handling Cleanup Agent.
Inspect the scope below for swallowed errors, masking fallbacks, and broad
defensive handlers. Remove error hiding while preserving real recovery and
reporting boundaries.

Scope:
<describe files, packages, or services>
```
