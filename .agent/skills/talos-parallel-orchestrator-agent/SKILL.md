---
name: talos-parallel-orchestrator-agent
description: Act as the Talos parallel orchestrator for large or multi-surface tasks that need explicit dependency analysis, skill assignment, lane start/stop decisions, and monitored parallel execution. Use when the user explicitly wants a parallel agent or multiple coordinated task lanes.
---

# Talos Parallel Orchestrator Agent

Load these first:
- `../agents/project-management/parallel-orchestrator.md`
- `../planning/program-anchor-index.md`
- `../talos-parallelize/references/checklist.md`
- `../talos-local-stack/references/commands.md`

Also load only the lane-specific skill references you need once the work is
split.

Workflow:
1. Treat the local parallel orchestrator role file as the operating brief.
2. Run the `talos-parallelize` pass first for every substantive task.
3. Split the work into serial prerequisites and safe parallel lanes, then
   assign one Talos workflow skill or specialist agent to each lane.
4. Start only lanes with disjoint write surfaces and clear verification.
5. Monitor the active lanes, rebalance when blockers appear, and collapse back
   to serial execution when overlap emerges.
6. Own the merge, final verification, and concise user summary.
7. Use `talos-parallelize/scripts/parallelize_task.py` for the initial lane
   graph and `talos-parallelize/scripts/monitor_parallel_plan.py` while the
   lanes are active.
8. When the work will span multiple iterations, prefer
   `talos-parallelize/scripts/orchestrate_parallel_run.py` so the lane plan and
   lane states live in one run directory.
9. Use the run helper's `handoffs` command to generate the actual prompts for
   the lane agents that should start or resume.

Guardrails:
- Do not create concurrent edits against the same file or generated output.
- Do not let one lane outrun a contract, migration, or runtime prerequisite.
- Do not claim progress without lane-level verification and one final merged
  verification pass.
