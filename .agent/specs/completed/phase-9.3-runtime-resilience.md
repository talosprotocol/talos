---
description: Phase 9.3 Runtime Loop and Resilience - LOCKED SPEC
---

# Phase 9.3: Runtime Loop and Resilience

## Status

**LOCKED SPEC**

## Goal

Implement crash-safe TGA execution with a Moore machine runtime loop and append-only storage. The runtime MUST recover from crashes without losing trace integrity and MUST NOT replay already-executed tool calls.

---

## Security Invariants (Non-Negotiable)

### I1: Append-Only State Log

- State transitions MUST be append-only and MUST NOT be overwritten.
- Each transition MUST append with a strictly monotonic `sequence_number` per `{trace_id}`.
- Recovery MUST replay the log to reconstruct current state.

### I2: Idempotent Execution

- Write-class tool calls MUST include `tool_call.idempotency_key` (enforced by Phase 9.2).
- Same `{server_id, tool_name, idempotency_key}` MUST NOT re-execute; return cached `tool_effect`.

### I3: Trace Integrity Preserved

- All TGA artifacts MUST be persisted with required IDs and digests.
- If `tool_effect` NOT recorded: recovery MUST retry dispatch (same `tool_call_id`, `idempotency_key`).
- If `tool_effect` IS recorded: recovery MUST NOT re-dispatch.

### I4: Checkpoint Determinism

- `checkpoint_digest` = `sha256(RFC8785_canonical_json(checkpoint_state))` (lowercase hex).

### I5: Hash-Chain for the Log

- Each log entry MUST include `prev_entry_digest` forming a hash chain.

### I6: Single-Writer Concurrency

- At most one active executor MAY append transitions for a given `trace_id` at a time.

### I7: Atomic Persistence

- Artifact + transition MUST commit together in single DB transaction.

---

## State Machine Design (Moore Machine)

### States

`PENDING | AUTHORIZED | EXECUTING | COMPLETED | FAILED | DENIED`

### Allowed Transitions

1. `PENDING -> AUTHORIZED` (SupervisorDecision approved)
2. `PENDING -> DENIED` (SupervisorDecision denied)
3. `AUTHORIZED -> EXECUTING` (ToolCall persisted)
4. `EXECUTING -> COMPLETED` (ToolEffect success)
5. `EXECUTING -> FAILED` (ToolEffect failure)

---

## Phase 9.3.1: Contracts (BLOCKING)

### Deliverables

- `schemas/tga/v1/execution_state.schema.json`
- `schemas/tga/v1/execution_log_entry.schema.json`
- `schemas/tga/v1/execution_checkpoint.schema.json`
- `test_vectors/tga/state_transition_vectors.json`

---

## Phase 9.3.2: Persistence Layer (talos-ai-gateway)

### Component

`app/domain/tga/state_store.py`

### Interface

```python
class TgaStateStore:
    async load_state(trace_id) -> ExecutionState
    async append_log_entry(entry) -> None
    async list_log_entries(trace_id, after_seq) -> list
    async write_checkpoint(checkpoint) -> None
    async load_latest_checkpoint(trace_id) -> ExecutionCheckpoint | None
    async acquire_trace_lock(trace_id) -> None
    async release_trace_lock(trace_id) -> None
```

---

## Phase 9.3.3: Connector Idempotency Cache (BLOCKING)

### Requirement

Persist durable idempotency record keyed by `{server_id, tool_name, idempotency_key}`.
On repeat: return cached `tool_effect`, MUST NOT call tool server.

---

## Phase 9.3.4: Runtime Loop (talos-ai-gateway)

### Component

`app/domain/tga/runtime.py`

### Recovery Logic

1. Acquire trace lock
2. Load checkpoint, validate digest
3. Replay log entries, verify chain
4. If EXECUTING without ToolEffect: re-dispatch same ToolCall
5. If terminal: return result
6. Release lock

---

## Stable Error Codes

- `STATE_INVALID_TRANSITION`
- `STATE_SEQUENCE_GAP`
- `STATE_CHECKSUM_MISMATCH`
- `STATE_RECOVERY_FAILED`
- `STATE_LOCK_ACQUIRE_FAILED`
- `STATE_CONCURRENT_EXECUTION`
