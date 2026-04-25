---
id: dead-code-removal
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Dead Code Removal

## Purpose
Find unused exports, unreferenced functions, orphaned files, and stale fixtures
in Talos, then remove only code that is manually confirmed dead.

## When to use
- A cleanup task asks for unused code or orphaned files to be removed.
- Static-analysis tools flag unused exports or dependencies.
- A refactor leaves old entrypoints, fixtures, or helpers behind.

## Outputs you produce
- Dead-code candidate list with evidence and confidence
- Manual verification notes for dynamic or convention-based references
- Safe removal patch and compatibility notes
- Focused validation commands

## Default workflow
1. Start with repo-local discovery, `rg`, test manifests, import graphs, and
   package scripts before adding new tooling.
2. Use tools such as `knip` for configured TypeScript packages when available,
   but treat their output as candidates, not proof.
3. Manually check dynamic imports, config references, framework conventions,
   code generation, CLI entrypoints, and docs examples.
4. Remove only confirmed-dead code and update tests, fixtures, docs, or exports
   that referenced it.
5. Run the smallest build, typecheck, or test that would catch accidental
   removal.

## Global guardrails
- Public APIs, CLI commands, schema fields, and generated artifacts require an
  owner and compatibility decision before removal.
- Do not remove code solely because one static analyzer did not see it.
- Do not delete generated outputs without naming the source and regeneration
  command.
- Keep cleanup patches narrow and reversible.

## Do not
- Do not remove compatibility shims that active users or submodules may still
  depend on.
- Do not collapse a dead-code cleanup into unrelated refactors.
- Do not leave broken exports, docs examples, or test manifests behind.

## Prompt snippet
```text
Act as the Talos Dead Code Removal Agent.
Find unused exports, unreferenced functions, and orphaned files in the scope
below. Verify manually before removing, including dynamic and generated paths.

Scope:
<describe files, modules, or task>
```
