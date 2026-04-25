---
name: talos-ops-sweep
description: Use when a Talos change, project pass, or failing build needs one coordinated sweep across CI/build triage, UI surface parity, and dirty-worktree or submodule hygiene before implementation starts. Run the three automation passes, merge the findings, and route the next work to the right owning surface.
---

# Talos Ops Sweep

Use this skill when the recurring Talos workflow is "inspect first, classify
the real surface, then route the fix".

Load:
- `../planning/program-anchor-index.md`
- `../talos-ci-triage/SKILL.md`
- `../talos-ui-surface-parity/SKILL.md`
- `../talos-submodule-hygiene/SKILL.md`

Workflow:
1. Start with the dirty surface. If the repo or submodules are dirty, run the
   hygiene pass first so root-level noise does not hide the real scope.
2. If a build or CI failure exists, reduce it to the first actionable signal
   with the CI triage pass before picking any repro commands.
3. If dashboard, API Workbench, or TUI work is in scope, inventory those
   surfaces and classify parity gaps before proposing implementation.
4. Merge the three outputs into one routing packet: owned surface, failure or
   parity class, cleanup actions, and the smallest next verification step.
5. Only then choose the implementation skill or specialist agent for the next
   lane.

Helper:
- `python3 .agent/skills/talos-ops-sweep/scripts/run_ops_sweep.py --repo-path . --submodules --format markdown`
- Add `--ci-log path/to/log.txt` when CI or local failure logs are available.

Guardrails:
- Do not jump straight to implementation when the dirty surface, failing
  surface, or UI ownership is still ambiguous.
- Do not let one noisy CI log line override submodule or worktree evidence.
- Do not mix confirmed findings with speculative roadmap items.

Done checklist:
- Dirty surface classified.
- CI signal reduced or explicitly marked absent.
- UI surface inventory included when relevant.
- Next owner skill or specialist agent is named.
