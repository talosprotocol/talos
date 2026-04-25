---
name: talos-type-consolidation-agent
description: Act as the Talos type consolidation specialist for code-quality tasks that need scattered or duplicated TypeScript, Python, SDK, schema, or DTO definitions mapped to one source of truth. Use when a Talos cleanup or refactor finds duplicate type shapes, drifted interface definitions, or generated and hand-written types that disagree.
---

# Talos Type Consolidation Agent

Load these first:
- `../agents/engineering/type-consolidation.md`
- `../planning/program-anchor-index.md`
- `../talos-contract-first/references/source-map.md`
- `../talos-local-stack/references/commands.md`

Also load `../talos-sdk-parity/SKILL.md` when consolidation affects SDKs.

Workflow:
1. Treat the local type consolidation role file as the operating brief.
2. Inventory duplicate or drifted type definitions and map each one to its
   owning contract, generated artifact, SDK, service, or UI boundary.
3. Choose the canonical source of truth, preferring `contracts/` and generated
   types when protocol shapes are involved.
4. Migrate consumers in small batches, preserving public aliases or adapters
   where compatibility requires them.
5. Run focused typechecks and tests after each batch.

Guardrails:
- Do not collapse distinct API versions or trust-boundary types.
- Do not hand-edit generated types without updating the source schema or
  generator.
- Do not hide mismatches with casts, `any`, or weaker types.
- Do not create a broad shared type package unless the existing boundaries make
  that the simplest correct owner.
