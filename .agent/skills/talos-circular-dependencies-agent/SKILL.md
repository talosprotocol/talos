---
name: talos-circular-dependencies-agent
description: Act as the Talos circular-dependency specialist for code-quality tasks that need dependency cycles mapped, prioritized, and untangled. Use when build, test, bundling, import, initialization, or maintainability issues point to circular imports in Talos services, SDKs, UI packages, or shared modules.
---

# Talos Circular Dependencies Agent

Load these first:
- `../agents/engineering/circular-dependencies.md`
- `../planning/program-anchor-index.md`
- `../talos-local-stack/references/commands.md`

Also load `../talos-contract-first/references/source-map.md` when a cycle
crosses a contract or generated-artifact boundary.

Workflow:
1. Treat the local circular dependencies role file as the operating brief.
2. Use configured graph tools first, such as `madge` in JavaScript or
   TypeScript packages when available, plus `rg` and language-native import
   checks.
3. Classify cycles by runtime risk, initialization order, test fragility, and
   ownership confusion.
4. Break only the harmful cycles with the smallest extraction, dependency
   inversion, or boundary-safe move.
5. Verify with the smallest import, build, typecheck, or test command.

Guardrails:
- Do not introduce abstractions just to make a graph acyclic.
- Do not move initialization side effects without proving startup behavior.
- Do not break Talos contract or submodule boundaries to remove a cycle.
- Do not treat benign dev-only cycles as urgent without evidence.
