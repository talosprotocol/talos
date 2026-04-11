---
name: talos-contract-first
description: Use when changing Talos schemas, API contracts, vectors, or any cross-component boundary. Start from `contracts/` or the owning spec, preserve anti-drift rules, avoid deep cross-repo imports, update affected consumers, and add or refresh vectors, tests, and docs before considering the task complete.
---

# Talos Contract First

Use this skill for protocol, schema, API, and boundary-sensitive work in the
Talos monorepo.

Load only what the task needs:
- `references/source-map.md`
- `../planning/program-anchor-index.md`
- The closest module `AGENTS.md`
- The owning spec or docs page for the affected contract

Workflow:
1. Identify the source of truth first. For protocol and payload changes, that is
   usually `contracts/` or a spec that points to the contract.
2. Trace every consumer with `rg` before editing. In Talos, a small schema or
   field change can hit services, SDKs, docs, dashboards, and tests.
3. Make the smallest change that preserves published boundaries. Prefer public
   artifacts and generated outputs over hand-written copies.
4. Update vectors, tests, and docs in the same pass when behavior, ordering,
   signing inputs, or validation changes.
5. Validate narrowly first, then widen scope if the change crosses service or
   submodule boundaries.

Non-negotiables:
- Do not add deep cross-repo imports or duplicate logic that should come from
  canonical contracts.
- Do not change hashed, signed, ordered, or authz-sensitive behavior without
  tests or vectors.
- Do not introduce nullable optional fields where Talos expects omission.
- Do not leave submodule pointer changes unexplained when a change spans repos.

Done checklist:
- Source-of-truth contract or spec updated, or explicitly confirmed unchanged.
- Affected consumers traced and updated through supported boundaries.
- Tests and vectors added or refreshed where required.
- Docs or operator notes updated if behavior changed.
- Final summary calls out invariants, validation, and any submodule pointer
  updates.
