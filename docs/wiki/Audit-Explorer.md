---
status: Implemented
audience: Developer, Operator
repository: talos-dashboard, talos-audit-service
---

# Audit Explorer

> **Problem**: Developers need to inspect and verify audit proofs.  
> **Guarantee**: CLI commands and Dashboard UI to explore message hashes, signature chains, and Merkle proofs.  
> **Dashboard**: `deploy/repos/talos-dashboard/` | **Service**: `deploy/repos/talos-audit-service/`

---

## Dashboard UI

The Talos Dashboard (`http://localhost:3000`) provides a visual audit explorer:

- **Event Timeline**: View all audit events chronologically
- **Proof Verification**: Click any event to verify its Merkle proof
- **Export**: Download audit reports in JSON/CSV
- **Real-time**: Live updates via WebSocket

---

```bash
# Show recent audit entries
talos audit log --last 10

# Verify a specific message
talos audit verify <message-hash>

# Export audit trail
talos audit export --from 2024-01-01 --format json
```

---

## CLI Commands

### `talos audit log`

Display audit log entries.

```bash
# Last 10 entries
talos audit log --last 10

# Entries for a specific peer
talos audit log --peer did:talos:abc123

# Entries in time range
talos audit log --from 2024-01-01 --to 2024-01-31

# Verbose output with hashes
talos audit log --verbose
```

**Output format**:
```
┌────────┬─────────────────────────┬───────────┬─────────────────┐
│ Height │ Timestamp               │ Type      │ Hash (short)    │
├────────┼─────────────────────────┼───────────┼─────────────────┤
│ 142    │ 2024-01-15 10:23:45    │ MESSAGE   │ 0x4d2e...8f3a   │
│ 141    │ 2024-01-15 10:22:12    │ CAP_GRANT │ 0x7b1c...2e4f   │
│ 140    │ 2024-01-15 10:20:01    │ SESSION   │ 0x9a3f...1b7c   │
└────────┴─────────────────────────┴───────────┴─────────────────┘
```

---

### `talos audit verify`

Verify a Merkle proof for a specific entry.

```bash
# Verify by message hash
talos audit verify 0x4d2e8f3a...

# Verify with full proof output
talos audit verify 0x4d2e8f3a... --verbose

# Verify against specific root (cross-check)
talos audit verify 0x4d2e8f3a... --root 0x8a3f1b7c...
```

**Output**:
```
Verifying audit entry: 0x4d2e8f3a...

Entry Details:
  Type:      MESSAGE
  Sender:    did:talos:alice_7f3k2m
  Recipient: did:talos:bob_9x2p1q
  Timestamp: 2024-01-15T10:23:45Z
  Block:     142

Merkle Proof:
  Path:      [0x1a2b..., 0x3c4d..., 0x5e6f...]
  Root:      0x8a3f1b7c...
  Depth:     8

Verification: ✅ VALID

Proof is cryptographically valid.
Entry exists in audit log at stated position.
```

---

### `talos audit show`

Display detailed information about an entry.

```bash
# Show entry by hash
talos audit show 0x4d2e8f3a...

# Show entry by height
talos audit show --height 142
```

**Output**:
```
Audit Entry #142
════════════════════════════════════════════

Hash:        0x4d2e8f3a...
Type:        MESSAGE
Timestamp:   2024-01-15T10:23:45Z
Block:       142

Participants:
  Sender:    did:talos:alice_7f3k2m
  Recipient: did:talos:bob_9x2p1q

Signatures:
  Sender:    0x7f3k2m4n... (VALID ✅)

Content Hash: 0xabcd1234...
  (Content not stored, only commitment)

Chain Link:
  Previous:  0x9a3f1b7c... (block 141)
  Next:      0x2b4d6e8f... (block 143)
```

---

### `talos audit chain`

Display chain structure and verify integrity.

```bash
# Verify entire chain
talos audit chain verify

# Show chain summary
talos audit chain summary

# Show specific range
talos audit chain show --from 100 --to 150
```

**Output (verify)**:
```
Chain Verification
══════════════════════════════════════════

Total Blocks:     2,847
Checked:          2,847
Valid:            2,847
Broken Links:     0

Hash Chain:       ✅ VALID
Signatures:       ✅ ALL VALID
Timestamps:       ✅ MONOTONIC

Overall Status:   ✅ CHAIN INTEGRITY VERIFIED
```

---

### `talos audit root`

Display current Merkle root and anchoring status.

```bash
# Show current root
talos audit root

# Show root at specific height
talos audit root --height 100

# Check blockchain anchor status
talos audit root --check-anchor
```

**Output**:
```
Current Audit Root
══════════════════════════════════════════

Root Hash:    0x8a3f1b7c...
Height:       2,847
Timestamp:    2024-01-15T10:30:00Z

Blockchain Anchor:
  Chain:      Ethereum L2 (Optimism)
  TX:         0x5c6d7e8f...
  Block:      45,678,901
  Confirmed:  ✅ YES (128 confirmations)

Last Anchored: 2024-01-15T10:00:00Z
Entries Since: 47
```

---

### `talos audit export`

Export audit data for external systems.

```bash
# Export to JSON
talos audit export --format json > audit.json

# Export to CSV
talos audit export --format csv > audit.csv

# Export with proofs
talos audit export --format json --include-proofs

# Export specific range
talos audit export --from 2024-01-01 --to 2024-01-31
```

---

## Programmatic Access

### Python SDK

```python
from talos import TalosClient

async with TalosClient.create("my-agent") as client:
    # Get audit log
    entries = client.audit.get_entries(limit=100)
    
    # Get specific entry
    entry = client.audit.get_entry(message_hash)
    
    # Verify proof
    proof = client.audit.get_proof(message_hash)
    is_valid = client.audit.verify_proof(proof)
    
    # Get current root
    root = client.audit.get_root()
    
    # Check if entry exists
    exists = client.audit.contains(message_hash)
```

### Query by Type

```python
# Get all capability grants
grants = client.audit.query(
    type="CAP_GRANT",
    from_time=datetime(2024, 1, 1),
    to_time=datetime(2024, 1, 31)
)

# Get all messages with a peer
messages = client.audit.query(
    type="MESSAGE",
    peer="did:talos:bob_9x2p1q"
)

# Get revocations
revocations = client.audit.query(type="REVOCATION")
```

---

## Proof Structure

A Merkle proof contains:

```json
{
  "entry_hash": "0x4d2e8f3a...",
  "root": "0x8a3f1b7c...",
  "height": 142,
  "path": [
    {"position": "left", "hash": "0x1a2b3c4d..."},
    {"position": "right", "hash": "0x5e6f7g8h..."},
    {"position": "left", "hash": "0x9i0j1k2l..."}
  ],
  "timestamp": "2024-01-15T10:23:45Z"
}
```

**Verification algorithm**:
1. Start with `entry_hash`
2. For each step in `path`:
   - If `position` is "left": `hash = H(step.hash || current)`
   - If `position` is "right": `hash = H(current || step.hash)`
3. Final `hash` must equal `root`

---

## Audit Entry Types

| Type | Description | What's Logged |
|------|-------------|---------------|
| `MESSAGE` | Message sent/received | Content hash, participants, timestamp |
| `SESSION` | Session established | Peer IDs, session ID |
| `CAP_GRANT` | Capability granted | Scope, constraints, recipient |
| `CAP_REVOKE` | Capability revoked | Capability ID, reason |
| `KEY_ROTATE` | Key rotation | Old/new key hashes |
| `IDENTITY` | Identity event | DID, anchor transaction |

---

## Integration Examples

### SIEM Integration

```python
# Stream to SIEM
async for entry in client.audit.stream():
    siem.send({
        "timestamp": entry.timestamp,
        "type": entry.type,
        "hash": entry.hash,
        "peer": entry.peer,
        "proof": client.audit.get_proof(entry.hash)
    })
```

### Compliance Export

```bash
# Export for auditor
talos audit export \
  --format json \
  --include-proofs \
  --include-signatures \
  --from 2024-01-01 \
  --to 2024-03-31 \
  > Q1_2024_audit.json
```

---

**See also**: [Audit Scope](Audit-Scope) | [Audit Use Cases](Audit-Use-Cases) | [Proof Lifecycle](Proof-Lifecycle)
