---
status: Implemented
audience: Operator
---

# Failure Modes

> **Problem**: Operators need to understand how Talos fails.  
> **Guarantee**: Documented failure scenarios and behaviors.  
> **Non-goal**: Prevention—see [Hardening Guide](guides-hardening-guide).

---

## Failure Categories

| Category | Impact | Recovery |
|----------|--------|----------|
| Network | Communication interrupted | Automatic reconnection |
| Storage | Data access issues | Depends on corruption level |
| Cryptographic | Security compromised | Key rotation |
| State | Inconsistency | Re-synchronization |

---

## Network Failures

### Peer Disconnection

**Situation**: Connection to peer lost mid-session.

**Behavior**:
- Messages queued locally
- Automatic reconnection attempts
- Session state preserved

**Recovery**:
```python
# Automatic - no action needed
# Messages delivered when connection restored
```

**Timeout**: Configurable (default: 30 seconds between retries)

---

### Registry Unavailable

**Situation**: Cannot reach registry server.

**Behavior**:
- New peer discovery fails
- Existing sessions continue working
- Falls back to DHT discovery if enabled

**Recovery**:
- Automatic when registry available
- Enable DHT as backup:
  ```python
  client = await TalosClient.create(
      "agent",
      discovery=["registry", "dht"]  # Fallback order
  )
  ```

---

### Network Partition

**Situation**: Network split isolates groups of peers.

**Behavior**:
- Agents on same side can communicate
- Cross-partition messages queued
- Capability revocation may not propagate

**Security implication**:
- Stale revocation lists during partition
- Configure grace periods appropriately

**Recovery**:
- Automatic merge when partition heals
- Queued messages delivered
- Revocation lists synchronized

---

### Complete Network Loss

**Situation**: Agent has no network connectivity.

**Behavior**:
- Offline mode (if enabled)
- Local audit continues
- No message delivery

**Configuration**:
```python
client = await TalosClient.create(
    "agent",
    offline_mode=True,  # Allow offline operation
    queue_limit=1000    # Max queued messages
)
```

---

## Storage Failures

### LMDB Corruption

**Situation**: Audit database corrupted.

**Symptoms**:
- Read errors
- Inconsistent block heights
- Verification failures

**Recovery**:
```bash
# Check database integrity
talos audit verify-chain

# If corruption detected, rebuild from peers
talos audit rebuild --from-peers

# Or restore from backup
talos audit restore --backup /path/to/backup
```

---

### Disk Full

**Situation**: Storage exhausted.

**Behavior**:
- New audit entries fail
- Messages may not send (audit required)
- Warning logged

**Prevention**:
```python
client = await TalosClient.create(
    "agent",
    audit_config={
        "max_size_gb": 10,
        "prune_after_anchor": True  # Remove after blockchain anchor
    }
)
```

---

### Key File Corruption

**Situation**: Identity key file corrupted.

**Impact**:
- Cannot sign messages
- Cannot establish sessions
- Identity effectively lost

**Recovery**:
```bash
# Restore from backup
talos recover --backup /path/to/backup.enc

# Or create new identity (old capabilities lost)
talos init --new-identity
```

**Prevention**: Regular encrypted backups

---

## Cryptographic Failures

### Key Compromise Detected

**Situation**: Evidence of unauthorized key use.

**Immediate actions**:
```bash
# Emergency key rotation
talos emergency-rotate --revoke-old --reason "compromise detected"
```

**Impact**:
- Old sessions invalidated
- Peers notified of revocation
- New sessions must be established

---

### Session State Corruption

**Situation**: Ratchet state inconsistent between peers.

**Symptoms**:
- Decryption failures
- MAC verification errors
- Messages marked as unreadable

**Recovery**:
```python
# Re-establish session from scratch
await client.reset_session(peer_id)
await client.establish_session(peer_id, peer_bundle)
```

**Data loss**: Messages in transit during corruption may be lost.

---

### Invalid Signatures

**Situation**: Received message has invalid signature.

**Behavior**:
- Message rejected
- Logged as security event
- Peer not automatically blocked (could be corruption)

**Investigation**:
```bash
# Check recent signature failures
talos audit query --type SIGNATURE_FAILURE --last 100
```

---

## State Failures

### Split Brain (Multi-Instance)

**Situation**: Same identity running on multiple hosts.

**Symptoms**:
- Conflicting session states
- Duplicate message IDs
- Audit log divergence

**Detection**:
```bash
# Check for duplicate peer announcements
talos diagnose --check-duplicates
```

**Recovery**:
1. Stop all instances
2. Determine authoritative state
3. Rotate keys (security precaution)
4. Resume single instance

---

### Clock Skew

**Situation**: System clock significantly wrong.

**Impact**:
- Capability expiry mismatched
- Timestamp validation failures
- Audit ordering issues

**Detection**:
```bash
# Check clock synchronization
talos diagnose --check-clock
```

**Resolution**:
- Sync with NTP
- Restart agent after clock correction

---

### Stale Revocation List

**Situation**: Revocation list not updated.

**Risk**: Revoked capabilities still accepted.

**Behavior modes**:
| Mode | Behavior |
|------|----------|
| `strict` | Fail if revocation list stale > 5min |
| `permissive` | Warn but allow with grace period |
| `offline` | Use cached list indefinitely |

**Configuration**:
```python
client = await TalosClient.create(
    "agent",
    revocation_mode="strict",
    revocation_max_age=300  # 5 minutes
)
```

---

## Message Delivery Failures

### Message Loss vs Delay

| Scenario | Behavior |
|----------|----------|
| Peer offline | Queued, delivered when online |
| Network timeout | Retried automatically |
| Peer rejected | Error returned to sender |
| Invalid capability | Error, message not sent |

### Delivery Timeout

**Configuration**:
```python
result = await client.send(
    peer_id,
    message,
    timeout=30,           # Wait 30 seconds
    retry_count=3,        # Retry 3 times
    on_failure="queue"    # Queue if still failing
)
```

---

### Replay Detection

**Situation**: Duplicate message received.

**Behavior**:
- Second copy silently dropped
- Logged for monitoring
- No error to sender

**Window**: Replay detection window is configurable (default: 1 hour).

---

## Audit Failures

### Anchor Failure

**Situation**: Cannot anchor audit root to blockchain.

**Behavior**:
- Local audit continues
- Retries with exponential backoff
- Alert generated

**Impact**: Proofs not externally verifiable until anchored.

**Recovery**: Automatic when blockchain available.

---

### Proof Verification Failure

**Situation**: Merkle proof fails to verify.

**Possible causes**:
| Cause | Resolution |
|-------|------------|
| Corrupted proof | Request new proof |
| Tampered log | Serious security incident |
| Wrong root | Check against correct anchor |

**Investigation**:
```bash
# Verify proof manually
talos audit verify-proof --proof proof.json --root 0x...
```

---

## Recovery Procedures Summary

| Failure | Command |
|---------|---------|
| Network issues | `talos diagnose --network` |
| Database corruption | `talos audit rebuild` |
| Key issues | `talos recover --backup` |
| Session corruption | `await client.reset_session()` |
| Split brain | Stop all, rotate keys, resume one |
| Clock skew | Sync NTP, restart |

---

## Monitoring for Failures

```yaml
# Prometheus alerts for failure detection
groups:
- name: talos-failures
  rules:
  - alert: AuditAnchorFailure
    expr: talos_audit_anchor_failures > 0
    
  - alert: SessionEstablishmentFailures
    expr: rate(talos_session_failures[5m]) > 0.1
    
  - alert: SignatureVerificationFailures
    expr: talos_signature_failures > 0
    
  - alert: RevocationListStale
    expr: talos_revocation_list_age_seconds > 600
```

---

**See also**: [Hardening Guide](guides-hardening-guide) | [Observability](features-observability-observability) | [Troubleshooting](guides-error-troubleshooting)
