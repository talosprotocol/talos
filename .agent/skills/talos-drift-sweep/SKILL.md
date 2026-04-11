---
name: talos-drift-sweep
description: Use when checking Talos for cross-repo drift, stale `.agent` propagation, duplicated protocol logic, broken submodule assumptions, or inconsistent docs and code boundaries. Prefer existing verification scripts and boundary checks, summarize concrete drift findings, and separate confirmed issues from unverified risk.
---

# Talos Drift Sweep

Use this skill for anti-drift and repository health checks.

Load:
- `references/checks.md`
- `../planning/program-anchor-index.md`

Workflow:
1. Identify the likely drift class: schema duplication, cross-repo import leak,
   stale `.agent` sync, stale docs, or submodule mismatch.
2. Use the existing checks first before inventing a new one.
3. When a check fails, trace the exact file, module, or generated artifact that
   drifted.
4. Separate confirmed breakage from likely but unverified risk in the summary.
5. If the fix touches multiple repos or submodules, name the required follow-up
   explicitly.

Guardrails:
- Do not describe “drift” abstractly without naming the concrete duplicated or
  stale artifact.
- Do not assume all submodules are meant to move together; verify ownership and
  intended boundaries.
- Do not create new generated content flows when an existing sync script already
  owns the artifact.

Done checklist:
- Drift class identified.
- Existing checks run or consciously skipped with reason.
- Findings are concrete and scoped.
- Follow-up repo or submodule actions called out.
