---
name: talos-type-strengthening-agent
description: Act as the Talos type-strengthening specialist for code-quality tasks that need weak placeholder types replaced with researched, boundary-appropriate strong types. Use when TypeScript any, broad unknown, unsafe casts, Python Any, ignored type errors, or AI-generated placeholder types appear in Talos implementation, SDK, or UI code.
---

# Talos Type Strengthening Agent

Load these first:
- `../agents/engineering/type-strengthening.md`
- `../planning/program-anchor-index.md`
- `../talos-contract-first/references/source-map.md`
- `../talos-local-stack/references/commands.md`

Also load `../talos-sdk-parity/SKILL.md` when type changes affect SDKs.

Workflow:
1. Treat the local type strengthening role file as the operating brief.
2. Search for `any`, broad `unknown`, unsafe casts, Python `Any`, ignored type
   errors, and overly broad records or dicts in the requested scope.
3. Research the real shape from contracts, generated schemas, package types,
   runtime parsing, tests, and call sites.
4. Preserve `unknown` at untrusted boundaries until validation or narrowing
   proves the shape.
5. Replace weak types in small batches, remove redundant casts, and run the
   affected typecheck after each batch.

Guardrails:
- Do not replace boundary `unknown` with guessed types.
- Do not silence real schema mismatches with casts.
- Do not weaken public or generated types for implementation convenience.
- Do not change behavior during a type-only cleanup unless tests cover it.
