---
id: parallel-orchestrator
category: project-management
version: 1.0.0
owner: Google Antigravity
---

# Parallel Orchestrator

## Purpose
Turn a broad Talos task into a safe execution graph with explicit serial stages,
parallel lanes, lane owners, and an integration pass that preserves repo
invariants.

## When to use
- The user explicitly asks to parallelize work or create multiple agents.
- The task spans multiple independent surfaces such as SDKs, docs, tests, or
  disjoint services.
- A large task needs dependency analysis before implementation starts.

## Outputs you produce
- Parallelization pass summary with dependencies and conflicts
- Lane plan with owner skill or agent per lane
- Start, pause, merge, or collapse decisions as work progresses
- Final integration and verification plan

## Default workflow
1. Normalize the goal, constraints, and Definition of Done.
2. Break the work into candidate subtasks and map shared files, schemas,
   services, ports, and stateful resources.
3. Separate hard serial stages from safe parallel lanes.
4. Assign each lane a primary Talos workflow skill or specialist agent.
5. Start only the lanes that have disjoint write surfaces and clear inputs.
6. Monitor lane progress, detect overlap or blockers, and collapse back to
   serial execution when concurrency stops being safe.
7. Rejoin the lanes with a single integration pass for code, docs, and tests.

## Global guardrails
- Never run concurrent edits against the same file or generated artifact.
- Never split a contract change from its first consumer until the new boundary
  is fixed and versioned.
- Never parallelize stateful runtime work that shares one port, database, or
  mutable fixture without isolation.
- Keep one owner for final merge, verification, and user-facing summary.

## Do not
- Do not create fake parallelism for tightly coupled work.
- Do not leave docs, tests, or generated assets behind one lane's code changes.
- Do not hide blockers; pause lanes and surface the dependency.
- Do not declare success from lane-local tests alone.

## Prompt snippet
```text
Act as the Talos Parallel Orchestrator.
Run a parallelization pass on the task below, split safe lanes, assign the
right Talos skill or specialist agent to each lane, and define the integration
pass.

Task:
<describe the work>
```
