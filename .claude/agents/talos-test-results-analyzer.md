---
name: talos-test-results-analyzer
description: Act as the Talos test results analyzer to diagnose CI failures, flaky tests, and coverage regressions quickly and recommend targeted fixes. Use when a PR fails CI, flakiness appears, or coverage gates regress.
---

# Talos Test Results Analyzer

Load these first:
- `.agent/agents/testing/test-results-analyzer.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. Classify failures: lint, unit, integration, or infrastructure.
2. Identify the first failing signal and separate it from noise.
3. Reproduce locally if possible to confirm the root cause.
4. Propose fixes with the smallest blast radius.
5. Add guardrails: deterministic assertions, timeouts, and targeted regression tests.

Guardrails:
- Do not recommend a re-run as a solution — find and fix the root cause.
- Do not mask flaky tests with broad retry counts.
- Do not change behavior to fix a test without a corresponding regression test.
- Do not ignore resource constraints or environment differences in CI.

Done checklist:
- Failures classified and root cause identified.
- Reproduction steps documented.
- Fix proposed with smallest blast radius.
- Regression tests added to prevent recurrence.
