---
name: talos-research-first
description: Use when starting any task that requires codebase research, symbol discovery, or dependency mapping. This skill ensures you understand the "why" and "where" before suggesting "how" or "what".
---

# Talos Research First

Use this skill to avoid shallow assumptions and ensure you have full context
before modifying code.

Load these first:
- `../planning/program-anchor-index.md`
- `../../../AGENTS.md`
- `../../../CONTRIBUTING.md`

Workflow:
1. **Explore:** Use `codebase_investigator` or `grep_search` to map the
   symbols, modules, and dependencies related to the task.
2. **Trace:** Identify every consumer of the symbols you plan to change. Use
   `rg` or `grep_search` to follow the data flow across Talos repos.
3. **Validate:** Read the source code of the identified areas. Do not trust
   summaries or outdated docs. Look for invariants, edge cases, and side effects.
4. **Propose:** Only after completing steps 1-3, propose a strategy or
   implementation plan. Explain the rationale behind the chosen path.

Non-negotiables:
- Do not skip the investigation phase. No "just-in-case" changes.
- Do not ignore cross-component boundaries. Use `talos-contract-first` if
  the change crosses a service or SDK boundary.
- Do not rely on single-file context. Talos is a multi-repo system; trace
  the impact across services, SDKs, and dashboards.

Done checklist:
- All related symbols and their consumers identified and listed.
- Dependencies (internal and external) mapped and verified.
- Potential side effects and regressions documented.
- Proposed strategy explicitly references the research findings.
