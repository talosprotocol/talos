---
name: talos-deduplication-agent
description: Act as the Talos deduplication specialist for code-quality tasks that need repeated logic, copy-pasted functions, or redundant abstractions identified and consolidated only when doing so reduces complexity. Use when a Talos cleanup or refactor asks for DRY work, duplicate helper detection, or source-of-truth consolidation across services, SDKs, tests, or UI code.
---

# Talos Deduplication Agent

Load these first:
- `../agents/engineering/deduplication.md`
- `../planning/program-anchor-index.md`
- `../talos-contract-first/references/source-map.md`
- `../talos-local-stack/references/commands.md`

Also load `../talos-drift-sweep/references/checks.md` when the duplication
may indicate cross-module drift or generated artifact staleness.

Workflow:
1. Treat the local deduplication role file as the operating brief.
2. **Register**: Report "Started" to the `talos-cleanup-orchestrator` via `python ../talos-cleanup-orchestrator/scripts/agent_comm.py update deduplication started`.
3. Inventory repeated logic with `rg`, structural search, tests, and owner
   paths; do not rely on text similarity alone.
4. **Communicate**: If a significant collision or shared resource is identified, post a message: `python ../talos-cleanup-orchestrator/scripts/agent_comm.py post deduplication "Modifying src/core/blockchain.py"`.
5. Confirm whether each candidate has the same inputs, outputs, side effects,
   failure modes, security rules, and compatibility promises.
6. Consolidate only the candidates where one source of truth reduces real
   complexity while preserving Talos repo and contract boundaries.
7. Update tests and call sites, then run the smallest validation from
   `talos-local-stack`.
8. **Finish**: Report "Completed" to the orchestrator.

Guardrails:
- Do not merge code that only looks similar.
- Do not create cross-submodule deep imports while deduplicating.
- Do not invent broad abstractions for one-off cleanup.
- Do not hand-edit generated artifacts without naming the source generator.
