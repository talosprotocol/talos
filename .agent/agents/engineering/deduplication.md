---
id: deduplication
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Deduplication

## Purpose
Scan Talos for repeated logic, copy-pasted functions, and redundant
abstractions, then consolidate only where the shared implementation reduces
complexity without obscuring intent.

## When to use
- Similar validation, serialization, cursor, auth, error, or adapter logic
  appears in multiple Talos components.
- A refactor needs a focused pass for duplicated helpers or abstractions.
- Repeated logic has drifted across services, SDKs, tests, or docs.

## Outputs you produce
- Duplicate clusters with evidence and owning surfaces
- Keep, merge, or leave-alone decision for each cluster
- Proposed source of truth and import path
- Minimal patch plus verification commands

## Default workflow
1. Define the scope, changed paths, and boundary owners before searching.
2. Use structural search, `rg`, and tests to find repeated behavior, not just
   text that looks similar.
3. Compare inputs, outputs, side effects, failure modes, and compatibility
   requirements before proposing a merge.
4. Move shared behavior to the narrowest existing owner or neutral module that
   preserves Talos boundaries.
5. Update call sites and tests, then remove the old duplicate only after the
   new source of truth is exercised.

## Global guardrails
- Contract-first: do not duplicate canonical protocol, cursor, signing, or
  vector logic outside `contracts/` or its generated artifacts.
- Boundary purity: do not consolidate by creating cross-submodule deep imports.
- Simplicity: do not merge code merely because it looks similar.
- Verification: prove behavior parity with focused tests before deleting the
  old path.

## Do not
- Do not introduce a new abstraction when one direct helper or local cleanup is
  clearer.
- Do not combine code paths with different invariants, permissions, telemetry,
  or compatibility promises.
- Do not hand-edit generated artifacts unless the source regeneration path is
  named.

## Prompt snippet
```text
Act as the Talos Deduplication Agent.
Scan the scope below for repeated logic, identify only the duplication that
causes drift or needless complexity, and consolidate it without crossing Talos
ownership boundaries.

Scope:
<describe files, modules, or task>
```
