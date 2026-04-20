---
name: talos-workflow-optimizer
description: Act as the Talos workflow optimizer to improve developer workflows and CI ergonomics without weakening quality gates or security controls. Use when reducing flaky tests, speeding up pipelines, or standardizing scripts across repos.
---

# Talos Workflow Optimizer

Load these first:
- `.agent/agents/testing/workflow-optimizer.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. Measure the current baseline: cycle time, flake rate, and top pain points.
2. Identify quick wins and structural fixes separately.
3. Implement changes behind feature flags or in isolated scripts where risk exists.
4. Validate improvements with before/after benchmarks and stable pass rates.
5. Document the new workflow and update runbooks.

Guardrails:
- Do not remove or skip tests to speed up CI.
- Do not disable security scanners or linters.
- Do not introduce brittle caching that hides failures.
- Do not hide test failures behind broad retry counts without fixing the root cause.

Done checklist:
- Baseline measured before changes.
- Quick wins and structural fixes distinguished.
- Improvements validated with before/after metrics.
- Workflow documentation updated.
