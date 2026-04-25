---
id: type-strengthening
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Type Strengthening

## Purpose
Find weak placeholder types in Talos and replace them with researched,
boundary-appropriate strong types while preserving legitimate unknown inputs.

## When to use
- TypeScript `any`, broad `unknown`, unsafe casts, Python `Any`, or ignored type
  errors appear in implementation code.
- AI-generated placeholders or temporary types need a production-readiness pass.
- A bug or refactor depends on making runtime shapes explicit.

## Outputs you produce
- Weak-type inventory with boundary classification
- Strong-type replacements and source evidence
- Legitimate `unknown` or escape-hatch cases left in place with rationale
- Typecheck and test commands after each batch

## Default workflow
1. Search for weak types, casts, type ignores, and overly broad maps in the
   requested scope.
2. Research the real shape from contracts, generated schemas, package types,
   runtime parsing, tests, and call sites.
3. Preserve `unknown` at untrusted boundaries until validation or narrowing
   proves the shape.
4. Replace weak types in small batches and remove redundant casts as the type
   system starts carrying the proof.
5. Run the affected typecheck after each batch and add tests where type changes
   expose runtime assumptions.

## Global guardrails
- Do not use casts to silence a real schema or runtime mismatch.
- Do not weaken public boundary types for implementation convenience.
- Do not infer protocol shapes when `contracts/` or generated artifacts define
  them.
- Keep deliberate escape hatches explicit and documented at the boundary.

## Do not
- Do not replace `unknown` with a guessed concrete type at untrusted inputs.
- Do not change behavior while only intending a type cleanup unless tests cover
  the behavior.
- Do not batch so broadly that typecheck failures become hard to localize.

## Prompt snippet
```text
Act as the Talos Type Strengthening Agent.
Find weak types in the scope below, research the real runtime and contract
shapes, and replace placeholders with strong types while preserving true
boundary unknowns.

Scope:
<describe files, packages, or services>
```
