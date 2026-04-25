---
id: ops-sweeper
category: project-management
version: 1.0.0
owner: OpenAI Codex
---

# Ops Sweeper

## Purpose
Run the standard Talos analysis sweep across dirty worktrees, CI/build logs,
and UI surface parity, then route the next work to the correct owner.

## When to use
- A Talos task starts with "analyse the project", "find blockers", or
  "understand the current state" across multiple surfaces.
- CI failure triage, UI parity, and submodule hygiene are all plausibly in
  scope and should be checked together first.
- The goal is to reduce repeated setup work before implementation starts.

## Outputs you produce
- Combined sweep report
- Routing packet with owned next lane
- Recommended next skill or specialist agent
- Scoped verification commands

## Default workflow
1. Run the combined ops sweep helper.
2. Reduce the combined findings to the smallest owned problem statement.
3. Separate confirmed findings from "still needs inspection".
4. Route the next step to the narrowest Talos workflow or specialist agent.
5. Keep the user summary concise and implementation-oriented.

## Do not
- Do not dump raw helper output without interpreting it.
- Do not skip the hygiene pass when the repo or submodules are dirty.
- Do not treat parity or CI output as definitive without naming the owning
  path.
