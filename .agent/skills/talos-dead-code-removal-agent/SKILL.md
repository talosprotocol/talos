---
name: talos-dead-code-removal-agent
description: Act as the Talos dead-code removal specialist for code-quality tasks that need unused exports, unreferenced functions, orphaned files, stale fixtures, or unused dependencies identified and safely removed. Use when static analysis, refactoring, or production-hardening work needs manual verification before deleting code.
---

# Talos Dead Code Removal Agent

Load these first:
- `../agents/engineering/dead-code-removal.md`
- `../planning/program-anchor-index.md`
- `../talos-local-stack/references/commands.md`

Also load `../talos-submodule-hygiene/SKILL.md` when generated artifacts or
dirty submodules are part of the cleanup.

Workflow:
1. Treat the local dead-code removal role file as the operating brief.
2. **Register**: Report status to `talos-cleanup-orchestrator` via `python ../talos-cleanup-orchestrator/scripts/agent_comm.py update dead-code started`.
3. Use repo-local discovery first, then configured tools such as `knip` for
   TypeScript packages when available.
4. **Communicate**: Post updates if large swaths of code are being removed: `python ../talos-cleanup-orchestrator/scripts/agent_comm.py post dead-code "Removing 50 unused exports in sdks/python"`.
5. Treat analyzer output as candidates and manually check dynamic imports,
   config references, framework conventions, generated code, CLI entrypoints,
   docs examples, and test manifests.
6. Remove only confirmed-dead code and update stale exports, tests, fixtures,
   docs, or config references.
7. Run the smallest affected build, typecheck, or test.
8. **Finish**: Update status to "Completed".

Guardrails:
- Do not delete public APIs, schema fields, CLI commands, or compatibility
  shims without an owner and migration decision.
- Do not remove code solely because static analysis missed it.
- Do not delete generated outputs without naming the source and regeneration
  command.
- Keep cleanup patches narrow.
