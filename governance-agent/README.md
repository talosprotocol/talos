# Talos Governance Agent (TGA)

**Repo Role**: Supervisor component that enforces capability-based authorization for AI agent actions.

## Overview

The Talos Governance Agent (TGA) implements the **Supervisor** pattern from the Talos Protocol. It acts as a policy enforcement point between AI agents and the tools they invoke, ensuring:

1. **Authorization**: Every action requires a valid, scoped capability token
2. **Audit**: All decisions are logged in a tamper-evident hash chain
3. **Blast Radius Limitation**: High-risk actions require explicit supervisor approval

## The Supervisor Model

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent                                 │
│            "I want to delete /projects/demo"                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ ActionRequest
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TGA Supervisor                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Parse intent & classify risk (READ/WRITE/HIGH_RISK)  │   │
│  │  2. Check policy: Is this allowed? Is scope valid?       │   │
│  │  3. Decision: APPROVE / DENY / ESCALATE                  │   │
│  │  4. If approved: Mint short-lived Capability Token       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ SupervisorDecision + Capability
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Tool Execution                             │
│  • Validate capability matches tool + args                      │
│  • Execute only if capability is valid and unexpired            │
│  • Log ToolCall with capability attestation                     │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

```
governance-agent/
├── src/
│   └── tga/
│       ├── domain/           # Core business logic
│       │   ├── models.py     # ActionRequest, SupervisorDecision, ToolCall
│       │   └── logic.py      # TgaValidator, hash chain verification
│       ├── infrastructure/   # Persistence layer
│       │   ├── memory_store.py   # In-memory store for testing
│       │   └── sqlite_store.py   # SQLite-backed audit log
│       └── tools/            # MCP tool implementations
└── tests/
```

## Domain Models

### Risk Levels

| Level | Description | Example |
|-------|-------------|---------|
| `READ` | No state changes | List files, read config |
| `WRITE` | Reversible state changes | Create file, update record |
| `HIGH_RISK` | Irreversible or sensitive | Delete data, send email, transfer funds |

### ActionRequest

Submitted by an agent when it wants to perform an action:

```python
class ActionRequest(BaseModel):
    trace_id: UUID          # Correlation ID for the entire flow
    plan_id: UUID           # ID of the agent's plan
    action_request_id: UUID # Unique ID for this request
    agent_id: UUID          # Identity of the requesting agent
    ts: datetime            # Timestamp
    risk_level: RiskLevel   # READ, WRITE, or HIGH_RISK
    intent: str             # Human-readable description
    resources: List[Dict]   # Resources being accessed
    proposal: Dict          # The actual tool call to execute
    digest: str             # SHA-256 hash for tamper detection
```

### SupervisorDecision

The Supervisor's response to an ActionRequest:

```python
class SupervisorDecision(BaseModel):
    action_request_id: UUID       # Links to the request
    action_request_digest: str    # Hash of the request (tamper-evident)
    decision: str                 # "APPROVE" | "DENY" | "ESCALATE"
    rationale: Optional[str]      # Why this decision was made
    minted_capability: Optional[str]  # Signed capability token (if approved)
    digest: str                   # Hash of this decision
```

### ExecutionLogEntry

Immutable audit log entry forming a hash chain:

```python
class ExecutionLogEntry(BaseModel):
    trace_id: UUID
    seq: int                    # Sequence number in chain
    prev_entry_digest: str      # Hash of previous entry (chain link)
    entry_digest: str           # Hash of this entry
    from_state: ExecutionState  # PENDING → AUTHORIZED → EXECUTING → COMPLETED
    to_state: ExecutionState
    artifact_type: ArtifactType # action_request | supervisor_decision | tool_call
    artifact_digest: str        # Hash of the artifact
```

## Hash Chain Verification

The TGA maintains a tamper-evident audit log using a hash chain:

```
Genesis → Entry[0] → Entry[1] → Entry[2] → ...
           │           │           │
           └─ prev_entry_digest ──┘
```

Each entry's `prev_entry_digest` references the previous entry's `entry_digest`, creating an immutable chain. The `TgaValidator.verify_hash_chain()` method validates chain integrity:

```python
from tga.domain.logic import TgaValidator

validator = TgaValidator()
is_valid, divergence_point = validator.verify_hash_chain(entries)
if not is_valid:
    print(f"Chain broken at sequence {divergence_point}")
```

## Integration Example

```python
from tga.domain.models import ActionRequest, RiskLevel
from tga.domain.logic import TgaValidator
from datetime import datetime
import uuid

# 1. Agent submits an action request
request = ActionRequest(
    trace_id=uuid.uuid4(),
    plan_id=uuid.uuid4(),
    action_request_id=uuid.uuid4(),
    agent_id=uuid.uuid4(),
    ts=datetime.utcnow(),
    risk_level=RiskLevel.WRITE,
    intent="Create a new project directory",
    resources=[{"type": "filesystem", "path": "/projects/new-demo"}],
    proposal={"tool": "filesystem", "action": "mkdir", "path": "/projects/new-demo"},
    digest="..."  # Computed by calculate_digest()
)

# 2. Supervisor evaluates and decides
# (Policy engine would check: Is agent authorized for this scope?)

# 3. If approved, mint a capability token
# (Short-lived, scoped to exact operation)

# 4. Log everything to the hash chain
# (Immutable audit trail)
```

## Hypervisor vs Supervisor

| Role | Mode | Description |
|------|------|-------------|
| **Hypervisor** | Passive | Monitors all agent activity, logs intents |
| **Supervisor** | Active | Holds signing keys, mints capability tokens |

The Hypervisor observes ("Why is the agent accessing `/etc/shadow`?"), while the Supervisor enforces ("This agent cannot access system files").

## Why This Matters

**The Two-Person Rule for AI**: Just as financial systems require dual authorization for large transactions, TGA enforces a separation between:
- **The Agent** (wants to act)
- **The Policy** (authorizes the action)

This creates a **Liability Shield**: if an AI agent causes damage, the audit log proves exactly what was authorized, by whom, and why.

## Development

```bash
# Install dependencies
cd governance-agent
pip install -e .

# Run tests
pytest tests/

# Type checking
mypy src/
```

## References

1. [Talos Protocol Specification](../PROTOCOL.md)
2. [Capability Token Design](../docs/features/capability-management.md)
3. [Audit Service](../services/audit)
4. [Why Talos Wins](../docs/business/why-talos-wins.md)

## License

Licensed under the Apache License 2.0. See [LICENSE](../LICENSE).
