---
status: Planned
audience: Developer
---

# Group Messaging

> **Problem**: Multi-agent coordination needs group communication.  
> **Guarantee**: Roadmap for secure group messaging.  
> **Non-goal**: Current implementation—this is planned.

---

## Current State

**Status**: 📋 **Planned** (not yet implemented)

Talos currently supports:
- ✅ 1:1 encrypted messaging
- ✅ Per-message forward secrecy
- ❌ Native group messaging

**Workaround**: Hub-and-spoke via coordinator agent.

---

## Design Options

### Option 1: Sender Keys

**Model**: Each member maintains a sending chain; receivers track all chains.

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Agent A │     │ Agent B │     │ Agent C │
│ chain_a │     │ chain_b │     │ chain_c │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     ▼               ▼               ▼
  ┌──────────────────────────────────────┐
  │          Group: agents_abc           │
  │  All members receive all chains      │
  └──────────────────────────────────────┘
```

**Pros**:
- Simple to implement
- Efficient (O(1) per message)
- Used by Signal groups

**Cons**:
- No post-compromise security per-message
- Adding members requires key distribution

---

### Option 2: MLS (Messaging Layer Security)

**Model**: IETF standard with tree-based key agreement.

```
                    Group Key
                       │
            ┌──────────┴──────────┐
            │                     │
      ┌─────┴─────┐         ┌─────┴─────┐
      │           │         │           │
    Agent A   Agent B   Agent C   Agent D
```

**Pros**:
- Post-compromise security
- Efficient updates (O(log n))
- IETF standard (RFC 9420)

**Cons**:
- More complex implementation
- Higher coordination overhead

---

### Option 3: Hybrid Model

**Model**: MLS for group key management + Double Ratchet for messages.

```
MLS Tree       →    Epoch Key    →    Double Ratchet
(key updates)       (shared)          (PFS per message)
```

**Pros**:
- Best of both worlds
- Post-compromise via MLS
- Per-message PFS via ratchet

**Cons**:
- Most complex
- Highest overhead

---

## Planned Approach

**Recommendation**: Start with **Sender Keys**, migrate to **MLS** later.

### Phase 1: Sender Keys (Near-term)

```python
# Future API
group = await client.create_group(
    name="coordination-group",
    members=["did:talos:a", "did:talos:b", "did:talos:c"]
)

await group.send(b"Hello everyone!")
```

### Phase 2: MLS (Long-term)

```python
# Future API with MLS
group = await client.create_group(
    name="secure-group",
    protocol="mls",  # Use MLS
    members=[...]
)

# Automatic key rotation on membership change
await group.add_member("did:talos:d")
await group.remove_member("did:talos:a")
```

---

## Security Properties by Model

| Property | Sender Keys | MLS | Hybrid |
|----------|-------------|-----|--------|
| Confidentiality | ✅ | ✅ | ✅ |
| Authenticity | ✅ | ✅ | ✅ |
| Forward Secrecy | ⚠️ Per-epoch | ⚠️ Per-epoch | ✅ Per-message |
| Post-Compromise | ❌ | ✅ | ✅ |
| Member Add | O(n) | O(log n) | O(log n) |
| Member Remove | O(n) | O(log n) | O(log n) |

---

## Group Audit

Group messages audit differently:

```json
{
  "type": "GROUP_MESSAGE",
  "group_id": "group_7f3k2m",
  "sender": "did:talos:alice",
  "recipients": ["did:talos:bob", "did:talos:carol"],
  "content_hash": "0x...",
  "epoch": 5
}
```

---

## Group Capabilities

```python
# Grant capability to group (planned)
capability = await owner.grant_group_capability(
    group_id="group_7f3k2m",
    scope="tools/shared_resource",
    require_consensus=True  # All members must agree
)
```

---

## Workaround: Coordinator Pattern

Until native group messaging:

```python
# Coordinator relays to all members
async def broadcast(coordinator, members, message):
    for member in members:
        await coordinator.send(member, message)

# Or parallel sends
await asyncio.gather(*[
    coordinator.send(m, message) for m in members
])
```

**Limitations**:
- Coordinator sees all messages
- O(n) messages per broadcast
- No atomic delivery

---

## Timeline

| Phase | Feature | Target |
|-------|---------|--------|
| 1 | Coordinator pattern (docs) | Now |
| 2 | Sender Keys implementation | Q2 2025 |
| 3 | MLS integration | Q4 2025 |
| 4 | Hybrid mode | 2026 |

---

**See also**: [Double Ratchet](double-ratchet) | [Future Improvements](research-future-improvements) | [Security Properties](security-cryptography)
