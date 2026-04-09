---
name: talos-parallelize
description: Use when a Talos task should be split into safe parallel lanes, when the user asks for parallel agents, or when a large change needs an explicit preflight pass to decide what can and cannot run concurrently. Analyze dependencies, assign the right Talos workflow skill or specialist agent to each lane, start only disjoint work in parallel, monitor the lanes, and collapse back to serial execution when overlap appears.
---

# Talos Parallelize

Load these first:
- `../../../.agent/agents/project-management/parallel-orchestrator.md`
- `../../../.agent/planning/program-anchor-index.md`
- `references/checklist.md`
- `assets/task-template.json`
- `assets/schemas/`

Then load only the lane-specific skill references you need:
- `../talos-contract-first/references/source-map.md`
- `../talos-capability-audit/references/checklist.md`
- `../talos-sdk-parity/references/sdk-map.md`
- `../talos-docs-parity/references/doc-map.md`
- `../talos-local-stack/references/commands.md`
- `../talos-governance-agent/references/tga-map.md`

Workflow:
1. Run a parallelization pass before implementation. Identify the goal, serial
   prerequisites, candidate subtasks, shared write surfaces, and verification
   boundary.
2. Build lanes only for disjoint work. Each lane must have clear inputs,
   output files, verification commands, and one primary skill or specialist
   agent.
3. Use existing Talos skills to specialize each lane instead of inventing a
   new workflow for every task.
4. Start read-only discovery, disjoint edits, and independent test slices in
   parallel. Keep shared-file edits, contract freezes, generated assets, and
   final verification serialized.
5. Monitor the lanes continuously. If two lanes converge on the same file,
   contract, runtime port, or fixture, stop parallel execution and merge back
   to a serial path.
6. Finish with one integration pass that reconciles code, docs, tests, and any
   generated outputs.
7. When the task is large enough to justify an artifact, write a small JSON
   task manifest and run `scripts/parallelize_task.py` to emit the lane plan.
8. While the lanes are active, maintain a tiny status JSON and run
   `scripts/monitor_parallel_plan.py` to decide whether to start, pause,
   resume, or merge lanes.
9. For a persistent run, use `scripts/orchestrate_parallel_run.py` to create a
   run directory with `manifest.json`, `plan.json`, and `status.json`, then
   update task states as the lanes move.
10. Use `scripts/orchestrate_parallel_run.py handoffs <run-dir>` to emit the
    concrete lane prompts for tasks that should start or resume now.

Planner helper:
- `scripts/parallelize_task.py <task.json>` emits a JSON lane plan with stage
  ordering, conflict reasons, and suggested Talos skills.
- `scripts/parallelize_task.py <task.json> --format markdown` emits a Markdown
  plan you can paste into the working notes.
- Start from `assets/task-template.json` and fill in candidate subtasks,
  `writes`, `depends_on`, `runtime_resources`, and `verify`.
- Start from `assets/status-template.json` while monitoring active lanes.
- `scripts/monitor_parallel_plan.py <plan.json> <status.json>` emits lane
  actions such as `start`, `continue`, `pause`, `resume`, `advance_stage`, or
  `merge_and_verify`.
- `scripts/orchestrate_parallel_run.py init <task.json> <run-dir>` creates a
  persistent run directory and emits the first decision.
- `scripts/orchestrate_parallel_run.py decide <run-dir>` recomputes next
  actions from saved state.
- `scripts/orchestrate_parallel_run.py set-state <run-dir> <task-id> <state>`
  updates one lane in `status.json`.
- `scripts/orchestrate_parallel_run.py handoffs <run-dir>` emits per-lane
  prompts with the suggested Talos skill, write scope, verification, and reason
  to act now.
- All of these artifacts are validated against the JSON schemas in
  `assets/schemas/` so malformed task manifests or run-state files fail early.

Lane-to-skill defaults:
- Contract or schema boundary: `$talos-contract-first`
- Authz, capability, audit, identity: `$talos-capability-audit`
- Cross-SDK propagation: `$talos-sdk-parity`
- Docs and examples: `$talos-docs-parity`
- Runtime commands and validation: `$talos-local-stack`
- Supervisor-gated agent flows: `$talos-governance-agent`
- Backend-heavy implementation: `$talos-backend-architect-agent`
- API and negative-path testing: `$talos-api-tester-agent`
- Infra and deployment work: `$talos-infra-maintainer-agent`
- Frontend/dashboard work: `$talos-frontend-developer-agent`
- Model/tooling flows: `$talos-ai-engineer-agent`

Guardrails:
- Do not parallelize concurrent edits to the same file or directory-level
  generated output.
- Do not split migrations or contract bumps from their required first
  consumers without an explicit version plan.
- Do not run two lanes that need the same local service instance unless they
  are read-only and port-safe.
- Do not skip the serial merge and verification pass.
