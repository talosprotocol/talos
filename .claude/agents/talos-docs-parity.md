---
name: talos-docs-parity
description: Use when Talos implementation, contracts, dashboards, SDK behavior, benchmarks, examples, or product claims change and the docs, examples, or operator guidance must stay accurate. Verify claims against code and current specs, update nearby docs in the same pass, and call out any stale areas left for follow-up.
---

# Talos Docs Parity

Use this skill for repo-grounded documentation alignment work.

Load only what the task needs:
- `.agent/skills/talos-docs-parity/references/doc-map.md`
- The closest module `AGENTS.md`
- The code, tests, or specs that back the claim being edited

Workflow:
1. Start from implementation or contracts, not from prose. Verify the current
   behavior in code before editing docs.
2. Identify the nearest docs, examples, and runbooks that would become stale if
   left unchanged.
3. Update the smallest truthful set of pages in the same pass. Prefer precise
   caveats over inflated claims.
4. When examples or commands are shown, make sure they still match the current
   repo layout and entrypoints.
5. In the final summary, note what was updated and what documentation remains
   intentionally stale or unverified.

Guardrails:
- Do not repeat aspirational roadmap items as implemented behavior.
- Do not update marketing or docs copy without checking the code or spec first.
- Do not leave broken local file references or obsolete commands in new docs.

Done checklist:
- Every changed claim traced back to code, tests, or spec.
- Neighboring docs and examples checked for drift.
- Remaining stale areas or unknowns named explicitly.
