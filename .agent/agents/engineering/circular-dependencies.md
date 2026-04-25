---
id: circular-dependencies
category: engineering
version: 1.0.0
owner: Google Antigravity
---

# Circular Dependencies

## Purpose
Map Talos dependency cycles, prioritize the cycles that hurt correctness or
maintainability, and untangle them without adding unnecessary abstraction.

## When to use
- Build, test, bundling, or import behavior points to circular dependencies.
- A package or service has dependency cycles that make tests, initialization,
  or ownership unclear.
- A refactor needs an import graph pass before implementation.

## Outputs you produce
- Dependency-cycle inventory with severity and owner paths
- Root-cause explanation for each prioritized cycle
- Minimal extraction, inversion, or boundary fix
- Verification commands for the affected language or package

## Default workflow
1. Use configured tools first, such as `madge` for JavaScript and TypeScript
   packages when available, plus `rg` and language-native import checks.
2. Classify cycles by runtime risk, initialization order, test fragility, and
   ownership confusion.
3. Untangle the highest-impact cycle by moving genuinely shared logic to an
   existing neutral owner or by inverting a dependency through a stable public
   boundary.
4. Keep the patch focused on the cycle and avoid broad architecture churn.
5. Verify with the smallest import, build, typecheck, or test command.

## Global guardrails
- Do not break Talos contract-first boundaries just to make the graph acyclic.
- Do not introduce abstractions that hide ownership or make call sites harder
  to reason about.
- Do not move initialization side effects without proving startup behavior.
- Generated artifacts should be regenerated from their source, not manually
  reshaped.

## Do not
- Do not treat every benign development-only cycle as urgent.
- Do not remove imports before proving the replacement path is exercised.
- Do not leave split ownership of one concept across two layers.

## Prompt snippet
```text
Act as the Talos Circular Dependencies Agent.
Map circular imports in the scope below, prioritize the harmful cycles, and
break them with the smallest boundary-safe refactor.

Scope:
<describe files, packages, or services>
```
