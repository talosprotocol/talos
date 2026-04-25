# Ops Sweep

Run this when a Talos task needs the standard analysis pass before any
implementation starts.

## Purpose

Combine the three recurring setup steps into one entrypoint:

- CI/build triage
- dashboard/API Workbench/TUI parity inventory
- dirty-worktree and submodule hygiene classification

## Command

```bash
python3 .agent/skills/talos-ops-sweep/scripts/run_ops_sweep.py \
  --repo-path . \
  --submodules \
  --format markdown
```

Add a CI or local failure log when available:

```bash
python3 .agent/skills/talos-ops-sweep/scripts/run_ops_sweep.py \
  --repo-path . \
  --submodules \
  --ci-log path/to/ci.log \
  --format markdown
```

## When to use

- “Analyse the project and subprojects”
- “Find blockers”
- “What is actually failing?”
- “Classify the real work surface before we edit”

## Output

The helper emits one combined report with:

- hygiene classification
- optional CI first-signal triage
- UI surface inventory

Use that report to pick the next Talos workflow skill or specialist agent.
