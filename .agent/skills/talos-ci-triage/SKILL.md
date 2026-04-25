---
name: talos-ci-triage
description: Use when triaging Talos CI, build, lint, typecheck, or test failures from GitHub Actions, local CI reproductions, or pasted logs. Reduce noise to the first actionable failure, map it to the owning surface, pick the smallest local repro command, and separate infra noise from real code or contract regressions.
---

# Talos CI Triage

Use this skill for Talos CI and build-failure triage.

Load:
- `../planning/program-anchor-index.md`
- `../talos-local-stack/references/commands.md`
- The nearest module `AGENTS.md`

Use `scripts/triage_ci_failure.py` for a deterministic first pass when the user
provides raw logs or a log file.

Workflow:
1. Normalize the failure: job, failing command, changed area, and whether the
   signal came from CI or a local repro.
2. Collapse the log to the first actionable failure. Ignore retries, teardown,
   and exit-code wrapper noise.
3. Map the failure to the owning Talos surface: contracts, root Python,
   services, SDKs, dashboard, deploy, or submodule state.
4. Choose the smallest local repro command that matches that surface before
   widening to repo-wide verification.
5. Separate confirmed code, contract, flaky-test, and infra failure classes.
   Call out assumptions explicitly.
6. End with a terse triage packet: root cause, evidence, minimal repro, safe
   fix direction, and any wider verification still needed.

Guardrails:
- Do not recommend a rerun as the fix.
- Do not jump to `make test`, `make build`, or the full stack before a scoped
  repro unless the failure clearly spans multiple surfaces.
- Do not treat generated artifacts or submodule pointers as disposable; identify
  the owning source first.
- Do not label a failure as infra noise unless the first actionable signal is
  clearly external to the code under test.

Done checklist:
- First actionable failure identified.
- Owning surface named.
- Smallest repro command chosen.
- Confirmed evidence separated from assumptions.
