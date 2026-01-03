---
status: Implemented
audience: Developer, Compliance
---

# Audit Use Cases

> **Problem**: Users need to understand audit applications.  
> **Guarantee**: Concrete scenarios for audit usage.  
> **Non-goal**: Implementation details—see [Audit Explorer](Audit-Explorer).

---

## Use Case 1: Compliance Reporting

### Scenario

Regulated enterprise needs to demonstrate AI agent accountability to auditors.

### Requirements

- Show what agents did during audit period
- Prove actions were authorized
- Demonstrate no tampering

### Talos Solution

```bash
# Export audit for period
talos audit export \
  --from 2024-01-01 \
  --to 2024-03-31 \
  --format json \
  --include-proofs \
  > Q1_2024_compliance.json
```

### Report Contents

```json
{
  "period": {"from": "2024-01-01", "to": "2024-03-31"},
  "summary": {
    "total_messages": 15234,
    "total_tool_invocations": 892,
    "capabilities_granted": 45,
    "capabilities_revoked": 3
  },
  "blockchain_anchors": [
    {"root": "0x...", "tx": "0x...", "block": 12345}
  ],
  "entries": [...]
}
```

### Auditor Verification

```bash
# Auditor verifies independently
talos audit verify-export Q1_2024_compliance.json
# ✅ All proofs valid
# ✅ Chain anchors confirmed
```

---

## Use Case 2: Dispute Resolution

### Scenario

Agent A claims Agent B failed to perform agreed action.

### Requirements

- Prove what was requested
- Prove what was (or wasn't) done
- Neutral verification

### Talos Solution

```python
# Party A: Get proof of request
request_proof = await client.audit.get_proof(request_hash)

# Party B: Get proof of response (if exists)
response_proof = await client.audit.get_proof(response_hash)

# Arbitrator: Verify both
assert arbitrator.verify_proof(request_proof)
assert arbitrator.verify_proof(response_proof)
```

### Evidence Package

```json
{
  "dispute_id": "dispute_123",
  "claimant": "did:talos:agent_a",
  "respondent": "did:talos:agent_b",
  "evidence": {
    "request": {
      "hash": "0x...",
      "timestamp": "2024-01-15T10:00:00Z",
      "proof": {...}
    },
    "response": {
      "hash": "0x...",
      "timestamp": "2024-01-15T10:00:05Z",
      "proof": {...}
    }
  },
  "blockchain_verification": {
    "both_anchored": true,
    "anchor_tx": "0x..."
  }
}
```

---

## Use Case 3: Post-Incident Forensics

### Scenario

Security incident detected; need to understand what happened.

### Requirements

- Timeline of agent actions
- Capability usage analysis
- Identify anomalies

### Talos Solution

```python
# Query all actions by suspected agent
actions = await client.audit.query(
    agent="did:talos:suspect",
    from_time=incident_start,
    to_time=incident_end
)

# Analyze capability usage
capabilities_used = await client.audit.query(
    type="CAPABILITY_USE",
    agent="did:talos:suspect"
)

# Check for anomalies
for action in actions:
    if action.timestamp.hour not in normal_hours:
        print(f"Anomaly: {action}")
```

### Forensic Report

```json
{
  "incident_id": "INC-2024-001",
  "timeline": [
    {
      "time": "2024-01-15T02:30:00Z",
      "event": "Unusual login time",
      "hash": "0x...",
      "verified": true
    },
    {
      "time": "2024-01-15T02:31:00Z",
      "event": "Capability escalation",
      "hash": "0x...",
      "verified": true
    }
  ],
  "root_cause": "Compromised credentials",
  "evidence_chain": "Complete and verified"
}
```

---

## Use Case 4: Tool Usage Billing

### Scenario

Tool provider needs to bill based on usage.

### Requirements

- Count invocations per agent
- Verify against customer records
- Handle disputes

### Talos Solution

```python
# Count invocations for billing period
invocations = await client.audit.query(
    type="TOOL_INVOCATION",
    tool="tools/api/call",
    from_time=billing_start,
    to_time=billing_end
)

# Generate bill with proofs
bill = {
    "period": {"start": billing_start, "end": billing_end},
    "invocations": len(invocations),
    "proofs": [client.audit.get_proof(i.hash) for i in invocations]
}
```

### Billing Record

```json
{
  "customer": "did:talos:enterprise_agent",
  "period": "2024-01",
  "usage": {
    "api_calls": 1523,
    "data_transferred_mb": 45.2
  },
  "verification": {
    "all_invocations_proven": true,
    "root_hash": "0x..."
  }
}
```

---

## Use Case 5: Capability Grant Audit

### Scenario

Security review of who has access to what.

### Requirements

- List all active capabilities
- Track delegation chains
- Identify over-privileged agents

### Talos Solution

```python
# Get all capability grants
grants = await client.audit.query(type="CAP_GRANT")

# Build capability map
capability_map = {}
for grant in grants:
    subject = grant.data["subject"]
    if subject not in capability_map:
        capability_map[subject] = []
    capability_map[subject].append(grant.data)

# Find over-privileged agents
for agent, caps in capability_map.items():
    if len(caps) > threshold:
        print(f"Review: {agent} has {len(caps)} capabilities")
```

---

## Use Case 6: SLA Verification

### Scenario

Prove service level agreement compliance.

### Requirements

- Response time tracking
- Availability evidence
- Third-party verifiable

### Talos Solution

```python
# Calculate response times from audit
requests = await client.audit.query(type="MCP_REQUEST")
responses = await client.audit.query(type="MCP_RESPONSE")

response_times = []
for req in requests:
    resp = find_matching_response(req, responses)
    if resp:
        delta = resp.timestamp - req.timestamp
        response_times.append(delta)

sla_compliance = {
    "p50": percentile(response_times, 50),
    "p95": percentile(response_times, 95),
    "p99": percentile(response_times, 99),
    "sla_met": percentile(response_times, 95) < sla_target
}
```

---

## Use Case 7: Multi-Org Collaboration Audit

### Scenario

Two organizations collaborated; need joint audit.

### Requirements

- Both parties contribute evidence
- Neither can tamper
- Neutral verification

### Talos Solution

Both organizations:
1. Export their audit logs with proofs
2. Proofs reference same blockchain anchors
3. Third party verifies both sides

```python
# Org A exports
org_a_audit = await org_a_client.audit.export(
    peers=["did:talos:org_b_agent"],
    include_proofs=True
)

# Org B exports
org_b_audit = await org_b_client.audit.export(
    peers=["did:talos:org_a_agent"],
    include_proofs=True
)

# Arbitrator reconciles
combined = reconcile_audits(org_a_audit, org_b_audit)
assert combined.consistent  # Both sides agree
```

---

## Summary Table

| Use Case | Key Audit Feature |
|----------|------------------|
| Compliance | Merkle proofs + blockchain anchors |
| Disputes | Neutral third-party verification |
| Forensics | Timeline reconstruction |
| Billing | Invocation counting with proofs |
| Access review | Capability grant tracking |
| SLA | Timestamped request/response pairs |
| Multi-org | Cross-organization proof reconciliation |

---

**See also**: [Audit Explorer](Audit-Explorer) | [Audit Scope](Audit-Scope) | [Protocol Guarantees](Protocol-Guarantees)
