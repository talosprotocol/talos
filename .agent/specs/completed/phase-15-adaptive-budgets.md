---
description: Phase 15 Adaptive Budgets - LOCKED SPEC
---

# Phase 15: Adaptive Budgets (LOCKED)

## 1. Goal

Prevent resource depletion and runaway costs for autonomous agents.

## 2. Technical Invariants

- **Atomic Enforcement**: Budget checks and decrements MUST be atomic (Redis `INCRBY` / `DECRBY`).
- **Enforcement Modes**:
  - `off`: Telemetry only.
  - `warn`: Log exceedance.
  - `hard`: Reject request (HTTP 402/429).

## 3. Implementation Details

- **Service**: `BudgetService`.
- **Cleanup**: `BudgetCleanupWorker` for reservation expiry.

## 4. Verification

- `verify_budget_ops.py` must pass 100/100 under high concurrency.
