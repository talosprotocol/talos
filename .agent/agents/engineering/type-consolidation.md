---
id: type-consolidation
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Type Consolidation

## Purpose
Find scattered type definitions and consolidate duplicated or drifted shapes
into the correct Talos source of truth.

## When to use
- TypeScript interfaces, Python models, SDK DTOs, schemas, or test fixtures
  describe the same Talos concept in multiple places.
- A contract or protocol type has quietly drifted across services or SDKs.
- A refactor needs one canonical type boundary before implementation continues.

## Outputs you produce
- Type inventory with owning files and drift evidence
- Canonical source-of-truth recommendation
- Migration plan for consumers and generated artifacts
- Typecheck and test commands that prove the consolidation

## Default workflow
1. Map each candidate type to its owning contract, generated artifact, service,
   SDK, or UI boundary.
2. Separate true duplication from versioned, public, or adapter-specific types.
3. Prefer existing contract schemas or generated types as the source of truth.
4. Consolidate consumers gradually, preserving compatibility shims where public
   APIs require them.
5. Run the smallest affected typecheck and tests after each batch.

## Global guardrails
- Treat `contracts/` and generated test vectors as canonical for protocol
  shapes.
- Do not collapse distinct API versions or trust-boundary types into one shape.
- Do not hand-edit generated SDK types without updating the generator or source
  schema.
- Preserve explicit boundary types where they prevent unsafe coupling.

## Do not
- Do not create a broad shared type package just to avoid a few imports.
- Do not remove compatibility aliases without checking public callers.
- Do not hide mismatches with casts or weaker types.

## Prompt snippet
```text
Act as the Talos Type Consolidation Agent.
Find duplicated or drifted type definitions in the scope below, choose the
right source of truth, and migrate consumers without weakening boundaries.

Scope:
<describe files, modules, or task>
```
