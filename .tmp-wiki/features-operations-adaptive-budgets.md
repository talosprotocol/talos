# Adaptive Budgets (Phase 15)

Adaptive Budgets provide atomic cost enforcement and resource constraints for autonomous AI agents.

## Overview

The `BudgetService` prevents runaway costs by tracking resource usage (tokens, API calls, compute) and enforcing limits in real-time.

## Enforcement Modes

| Mode | Behavior |
| --- | --- |
| `off` | Tracking only, no enforcement. |
| `warn` | Logs a warning when limits are exceeded but allows the request. |
| `hard` | Terminates requests immediately when limits are exceeded. |

## Architecture

### Components

- **`BudgetService`**: The core logic for tracking and checking balances.
- **`BudgetCleanupWorker`**: Expires stale resource reservations.
- **`BudgetReconcile`**: Periodically reconciles database state with real-time usage for long-running jobs.

## Usage

### SDK Example

```python
from talos_sdk import TalosClient

client = TalosClient()
with client.budget_context(max_tokens=1000):
    # This block is protected by the budget service
    response = client.call_tool("llm/generate", prompt="Hello")
```

## Admin API

- `GET /admin/v1/budgets/{principal_id}`: View current usage and limits for an agent.
- `PATCH /admin/v1/budgets/{principal_id}`: Update limits or enforcement mode.

## Verification

The budget system is verified with the `verify_budget_ops.py` script, which tests concurrency safety and atomic decrement/increment operations.

```bash
python scripts/verify_budget_ops.py
```
