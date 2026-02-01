---
status: Implemented
audience: Developer
---

# MCP Cookbook

> **Problem**: Developers need concrete recipes for securing MCP.  
> **Guarantee**: End-to-end examples for common patterns.  
> **Non-goal**: MCP protocol details—see [MCP Integration](mcp-integration).

---

## Recipe 1: Secure Tool Invocation

**Goal**: Invoke an MCP tool with cryptographic authorization.

### Setup

```python
from talos import TalosClient

# Agent that will invoke the tool
async with TalosClient.create("invoker-agent") as invoker:
    # Tool owner grants capability
    capability = received_capability  # From tool owner
    
    # Invoke the tool
    result = await invoker.mcp_call(
        peer_id=tool_owner_id,
        method="filesystem/read_file",
        params={"path": "/data/config.json"},
        capability=capability
    )
    
    print(f"Result: {result}")
```

### What's Happening

1. Invoker presents capability token
2. Tool verifies: signature, scope, expiry, revocation
3. If valid, tool executes MCP method
4. Both sides log to audit
5. Result returned via encrypted channel

---

## Recipe 2: Tool Provider Setup

**Goal**: Expose an MCP tool securely via Talos.

### Server Side

```python
from talos import TalosClient, MCPServer

async with TalosClient.create("tool-provider") as provider:
    # Define the tool
    @provider.mcp_tool("filesystem/read_file")
    async def read_file(path: str, capability: Capability) -> str:
        # Capability is automatically verified before this runs
        # Additional business logic checks
        if not path.startswith("/data/"):
            raise PermissionError("Path not allowed")
        
        with open(path, "r") as f:
            return f.read()
    
    # Start serving
    await provider.serve_mcp(port=8766)
```

### Granting Access

```python
# Grant capability to specific agent
capability = await provider.grant_capability(
    subject="did:talos:authorized_agent",
    scope="filesystem/read_file",
    constraints={"paths": ["/data/*"]},
    expires_in=3600  # 1 hour
)

# Send capability to agent (via Talos message)
await provider.send(authorized_agent_id, capability.to_bytes())
```

---

## Recipe 3: Secrets Never in LLM

**Goal**: Pass secrets to tools without exposing to LLM.

### The Problem

```
LLM → "Call database with password: hunter2"  # BAD!
```

### The Solution

```python
# Store secret in Talos secure storage
secret_ref = await agent.store_secret(
    key="db_password",
    value="actual_password_here",
    expires_in=3600
)

# LLM only sees the reference
prompt_to_llm = f"""
Call the database tool with:
- query: SELECT * FROM users
- credential_ref: {secret_ref.id}  # Just an ID, not the secret
"""

# Tool resolves the reference server-side
@provider.mcp_tool("database/query")
async def query(query: str, credential_ref: str, capability: Capability):
    # Resolve secret from Talos secure storage
    password = await provider.resolve_secret(credential_ref, capability)
    # Secret never touches the LLM
    return execute_query(query, password)
```

### Audit Trail

```json
{
  "type": "TOOL_INVOCATION",
  "method": "database/query",
  "agent": "did:talos:invoker",
  "secret_ref_used": "secret_7f3k2m",  // Reference, not value
  "timestamp": "2024-01-15T10:00:00Z"
}
```

---

## Recipe 4: Time-Limited Tool Access

**Goal**: Grant tool access for exactly 15 minutes.

```python
# Grant 15-minute lease
capability = await provider.grant_capability(
    subject="did:talos:temp_agent",
    scope="tools/api/call",
    expires_in=900,  # 15 minutes
    renewable=False   # Cannot extend
)

# After 15 minutes, capability is automatically invalid
# No manual revocation needed
```

### For Longer Work with Renewals

```python
capability = await provider.grant_capability(
    subject="did:talos:worker",
    scope="tools/api/call",
    expires_in=900,
    renewable=True,
    max_renewals=4  # Can extend up to 1 hour total
)

# Worker renews before expiry
renewed = await worker.renew_capability(capability.id)
```

---

## Recipe 5: Audit Tool Usage

**Goal**: Verify what tools were called and by whom.

### Query Audit Log

```python
# Get all tool invocations by an agent
invocations = await client.audit.query(
    type="TOOL_INVOCATION",
    agent="did:talos:suspect_agent",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31)
)

for inv in invocations:
    print(f"Tool: {inv.method}")
    print(f"Time: {inv.timestamp}")
    print(f"Capability: {inv.capability_id}")
    print(f"Result hash: {inv.result_hash}")
```

### Verify Specific Invocation

```python
# Get Merkle proof for an invocation
proof = await client.audit.get_proof(invocation_hash)

# Verify independently (can be done by third party)
assert client.audit.verify_proof(proof)

# Check blockchain anchor
anchor = await client.audit.get_anchor(proof.root)
print(f"Anchored in tx: {anchor.tx_hash}")
```

---

## Recipe 6: Cross-Org Tool Sharing

**Goal**: Share a tool across organizational boundaries.

### Org A (Tool Owner)

```python
# Org A owns the tool
async with TalosClient.create("org-a-tool") as org_a:
    # Grant capability to Org B's agent
    capability = await org_a.grant_capability(
        subject="did:talos:org_b_agent",
        scope="tools/analytics/run_report",
        constraints={
            "data_scope": ["shared_dataset"],
            "max_rows": 10000
        },
        expires_in=86400  # 24 hours
    )
    
    # Anchor capability hash for cross-org verification
    await org_a.anchor_capability(capability)
```

### Org B (Tool User)

```python
async with TalosClient.create("org-b-agent") as org_b:
    # Verify capability is valid (including on-chain check)
    is_valid = await org_b.verify_capability(
        capability,
        check_anchor=True  # Verify against blockchain
    )
    
    if is_valid:
        result = await org_b.mcp_call(
            peer_id=org_a_tool_id,
            method="analytics/run_report",
            params={"report": "monthly_summary"},
            capability=capability
        )
```

### Audit Verification (Either Org)

```python
# Either org can verify the interaction happened
proof = await client.audit.get_proof(invocation_hash)
assert client.audit.verify_proof(proof)
# Proof is valid without trusting the other org
```

---

## Recipe 7: Scoped Filesystem Access

**Goal**: Allow agent to read only specific directories.

```python
# Grant read-only access to /data and /config
capability = await provider.grant_capability(
    subject=agent_id,
    scope="filesystem/read",
    constraints={
        "allowed_paths": ["/data/*", "/config/*.json"],
        "forbidden_paths": ["/data/secrets/*"],
        "max_file_size_kb": 1024
    }
)

# Tool enforces constraints
@provider.mcp_tool("filesystem/read")
async def read(path: str, capability: Capability):
    # Constraints are checked automatically before this runs
    # Additional validation for defense in depth
    if "secrets" in path:
        raise PermissionError("Secrets directory not allowed")
    return read_file(path)
```

---

## Recipe 8: Rate-Limited API Calls

**Goal**: Prevent agent from overwhelming an API.

```python
capability = await provider.grant_capability(
    subject=agent_id,
    scope="api/call",
    constraints={
        "rate_limit": "100/hour",
        "burst_limit": 10,
        "cooldown_seconds": 1
    }
)

# Rate limiting is enforced automatically
# Excess calls are rejected with RateLimitExceeded error
```

---

## Recipe 9: Tool Invocation with Intent

**Goal**: Require explicit intent statement for high-risk operations.

```python
# For high-risk operations, create intent first
intent = await agent.create_intent(
    action="database/delete_records",
    params={
        "table": "users",
        "condition": "inactive = true"
    },
    justification="Quarterly cleanup of inactive accounts per policy 7.2"
)

# Tool requires intent for destructive operations
@provider.mcp_tool("database/delete_records", require_intent=True)
async def delete_records(table: str, condition: str, intent: Intent):
    # Intent is verified: signature, matches params, logged
    return execute_delete(table, condition)

# Invoke with intent
result = await agent.mcp_call(
    method="database/delete_records",
    params={"table": "users", "condition": "inactive = true"},
    capability=capability,
    intent=intent
)
```

---

## Recipe 10: Emergency Tool Revocation

**Goal**: Immediately disable a compromised agent's tool access.

```python
# Revoke all capabilities for an agent
await provider.revoke_all_capabilities(
    subject="did:talos:compromised_agent",
    reason="security incident",
    evidence=incident_report_hash
)

# Or revoke specific capability
await provider.revoke_capability(
    capability_id="cap_7f3k2m",
    reason="abuse detected"
)

# Revocation is:
# - Immediate locally
# - Logged to audit
# - Anchored on-chain
# - Propagated to peers
```

---

## Common Patterns Summary

| Pattern | Key Configuration |
|---------|-------------------|
| Time-limited access | `expires_in=900` |
| Renewable leases | `renewable=True, max_renewals=N` |
| Scoped paths | `constraints={"allowed_paths": [...]}` |
| Rate limiting | `constraints={"rate_limit": "N/period"}` |
| Secrets isolation | `resolve_secret()` server-side |
| Cross-org trust | `anchor_capability()` + `check_anchor=True` |
| High-risk ops | `require_intent=True` |

---

**See also**: [MCP Integration](mcp-integration) | [Agent Capabilities](authorization-agent-capabilities) | [Audit Explorer](observability-audit-explorer)
