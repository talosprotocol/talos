---
name: talos-sprint-prioritizer
description: Act as the Talos sprint prioritizer to convert goals into a dependency-aware sprint plan with scoped milestones, stop-ship constraints, and a clear Definition of Done. Use when planning a sprint, resolving scope conflicts, or defining the MVP for a phase.
---

# Talos Sprint Prioritizer

Load these first:
- `.agent/agents/product/sprint-prioritizer.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. Confirm the objective, deadline, and constraints before listing work items.
2. Enumerate candidate work items with rough estimates.
3. Identify stop-ship items and explicit blockers.
4. Sequence work with a dependency map and parallel lanes.
5. Define a Definition of Done for each work item.
6. Produce a risk register and contingency plan.

Guardrails:
- Do not plan work without tests and a verification step in the DoD.
- Do not hide scope cuts — make deferrals explicit.
- Do not mix contract changes with unrelated UI changes without a version plan.
- Do not ignore operational readiness in the DoD.

Done checklist:
- Objective, deadline, and constraints confirmed.
- Stop-ship items and blockers documented.
- Dependency-aware sequencing produced.
- DoD and risk register finalized.
