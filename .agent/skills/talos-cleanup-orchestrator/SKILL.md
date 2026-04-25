---
name: talos-cleanup-orchestrator
description: Orchestrate a multi-agent parallel cleanup pass. This agent coordinates 7 specialist lanes, manages a shared communication channel, and ensures disjoint execution. Use when the user wants to parallelize the 7-track code quality cleanup.
---

# Talos Cleanup Orchestrator

This agent manages the "Cleanup Task Force" by splitting the 7-track cleanup into parallel lanes and maintaining a shared communication state.

## Core Responsibilities
1. **Plan**: Analyze the codebase and split the 7 tracks into safe parallel lanes using `talos-parallelize`.
2. **Coordinate**: Use `scripts/agent_comm.py` to maintain a shared state file (`CLEANUP_STATE.json`).
3. **Communicate**: Post messages and updates to the shared channel so lane agents can "see" each other's progress and warnings.
4. **Handoff**: Generate context-rich prompts for the specialist agents (Deduplication, Dead Code, etc.) including the current shared state.

## Shared Communication Channel
The orchestrator maintains `CLEANUP_STATE.json` with:
- **Tasks**: Current status of each cleanup track.
- **Messages**: Cross-agent warnings (e.g., "Deduplication found a conflict in `src/core`").
- **Shared Resources**: Files currently being modified to prevent collisions.

## Workflow
1. **Initialize**: Run `python scripts/agent_comm.py init CLEANUP_STATE.json`.
2. **Parallelize**: Map the 7 tracks to lanes.
   - Track 3 (Dead Code) and Track 1 (Deduplication) often overlap.
   - Track 5 (Type Strengthening) can run in parallel with Track 6 (Error Handling).
3. **Dispatch**: For each active lane, generate a prompt that includes:
   - The specialist skill to use.
   - The current `CLEANUP_STATE.json` content.
   - Specific write boundaries.
4. **Monitor**: Periodically check `CLEANUP_STATE.json` for updates from agents and rebalance lanes if conflicts arise.

## Tools
- `python scripts/agent_comm.py post <sender> <message>`: Post a message to the channel.
- `python scripts/agent_comm.py update <task_id> <status> [details]`: Update task progress.
- `python scripts/agent_comm.py get`: Read the full state.

## Guardrails
- NEVER allow two agents to write to the same file simultaneously.
- ENSURE all agents report their "Start" and "Finish" to the state file.
- RECONCILE all findings in a final Integration Pass.
