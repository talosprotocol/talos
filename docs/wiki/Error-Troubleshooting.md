---
status: Implemented
audience: Developer
---

# Error Troubleshooting

> **Problem**: Developers need to resolve common errors.  
> **Guarantee**: Error codes, causes, and solutions.  
> **Non-goal**: All possible edge cases.

---

## Error Code Reference

| Code | Name | Description |
|------|------|-------------|
| E001 | `KEY_NOT_FOUND` | Identity or encryption key missing |
| E002 | `SESSION_NOT_ESTABLISHED` | No active session with peer |
| E003 | `DECRYPTION_FAILED` | Cannot decrypt message |
| E004 | `SIGNATURE_INVALID` | Signature verification failed |
| E005 | `CAPABILITY_EXPIRED` | Capability token expired |
| E006 | `CAPABILITY_REVOKED` | Capability was revoked |
| E007 | `SCOPE_VIOLATION` | Action outside capability scope |
| E008 | `PEER_UNREACHABLE` | Cannot connect to peer |
| E009 | `REGISTRY_UNAVAILABLE` | Registry server down |
| E010 | `AUDIT_FAILURE` | Cannot write to audit log |
| E011 | `PREKEY_EXHAUSTED` | Peer has no one-time prekeys |
| E012 | `RATE_LIMITED` | Too many requests |
| E013 | `DATA_CORRUPTION` | Storage corruption detected |
| E014 | `TIMEOUT` | Operation timed out |
| E015 | `INVALID_DID` | Malformed DID |

---

## Common Errors

### E001: Key Not Found

**Symptoms**:
```
TalosError: E001 KEY_NOT_FOUND: Identity key not found at /path/to/data
```

**Causes**:
- Data directory doesn't exist
- Keys were deleted
- Wrong data directory path
- Permission denied

**Solutions**:

```python
# Check data directory exists
import os
assert os.path.exists("/path/to/data")

# Check permissions
assert os.access("/path/to/data", os.R_OK)

# Initialize if new
client = await TalosClient.create(
    "agent",
    data_dir="/path/to/data"  # Will create if missing
)

# Or recover from backup
client = await TalosClient.recover(
    backup_path="/backup/keys.enc",
    password="..."
)
```

---

### E002: Session Not Established

**Symptoms**:
```
TalosError: E002 SESSION_NOT_ESTABLISHED: No session with did:talos:peer
```

**Causes**:
- Session never established
- Session expired
- Session corrupted

**Solutions**:

```python
# Establish session first
bundle = await client.get_prekey_bundle(peer_id)
await client.establish_session(peer_id, bundle)

# Then send
await client.send(peer_id, message)

# Or use auto-establish
await client.send(peer_id, message, auto_establish=True)
```

---

### E003: Decryption Failed

**Symptoms**:
```
TalosError: E003 DECRYPTION_FAILED: MAC verification failed
```

**Causes**:
- Message corrupted in transit
- Session state out of sync
- Wrong key used
- Replay of old message

**Solutions**:

```python
# Reset session
await client.reset_session(peer_id)
bundle = await client.get_prekey_bundle(peer_id)
await client.establish_session(peer_id, bundle)

# Request message resend from peer
```

---

### E004: Signature Invalid

**Symptoms**:
```
TalosError: E004 SIGNATURE_INVALID: Signature verification failed for message
```

**Causes**:
- Message tampered
- Wrong sender key
- Key rotation not propagated
- Man-in-the-middle attempt

**Solutions**:

```python
# Refresh peer's public key
await client.refresh_peer_keys(peer_id)

# Verify peer identity
peer_did = await client.resolve_did(peer_id)
print(f"Peer public key: {peer_did.public_key}")

# If persistent, investigate as security incident
```

---

### E005: Capability Expired

**Symptoms**:
```
TalosError: E005 CAPABILITY_EXPIRED: Capability cap_xxx expired at 2024-01-15T10:00:00Z
```

**Causes**:
- Capability TTL exceeded
- Clock skew between parties

**Solutions**:

```python
# Request new capability
new_cap = await client.request_capability(
    issuer=tool_owner,
    scope="tools/..."
)

# Or renew if renewable
renewed = await client.renew_capability(capability.id)

# Check clock sync
import time
print(f"Local time: {time.time()}")
```

---

### E006: Capability Revoked

**Symptoms**:
```
TalosError: E006 CAPABILITY_REVOKED: Capability cap_xxx was revoked
```

**Causes**:
- Issuer revoked the capability
- Security incident triggered revocation

**Solutions**:

```python
# Check why revoked
revocation = await client.get_revocation(capability.id)
print(f"Reason: {revocation.reason}")

# Request new capability if appropriate
new_cap = await client.request_capability(issuer, scope)
```

---

### E007: Scope Violation

**Symptoms**:
```
TalosError: E007 SCOPE_VIOLATION: Action "write" not in scope "tools/read"
```

**Causes**:
- Attempting action outside capability scope
- Capability too restrictive

**Solutions**:

```python
# Check capability scope
print(f"Capability scope: {capability.scope}")

# Request broader capability
broader_cap = await client.request_capability(
    issuer=tool_owner,
    scope="tools/read_write"
)
```

---

### E008: Peer Unreachable

**Symptoms**:
```
TalosError: E008 PEER_UNREACHABLE: Cannot connect to did:talos:peer
```

**Causes**:
- Peer offline
- Network partition
- Firewall blocking
- Wrong peer address

**Solutions**:

```python
# Check peer status
status = await client.get_peer_status(peer_id)
print(f"Peer status: {status}")

# Try discovery refresh
await client.refresh_peer_discovery(peer_id)

# Queue message for later
await client.send(peer_id, message, on_failure="queue")
```

---

### E009: Registry Unavailable

**Symptoms**:
```
TalosError: E009 REGISTRY_UNAVAILABLE: Cannot connect to registry
```

**Causes**:
- Registry server down
- Network issues
- Wrong registry URL

**Solutions**:

```python
# Use DHT fallback
client = await TalosClient.create(
    "agent",
    discovery=["registry", "dht"]
)

# Or specify backup registry
client = await TalosClient.create(
    "agent",
    registry_urls=[
        "wss://registry1.example.com",
        "wss://registry2.example.com"
    ]
)
```

---

### E010: Audit Failure

**Symptoms**:
```
TalosError: E010 AUDIT_FAILURE: Cannot write to audit log
```

**Causes**:
- Disk full
- Permission denied
- Database corruption

**Solutions**:

```bash
# Check disk space
df -h /path/to/data

# Check permissions
ls -la /path/to/data/audit/

# Repair database
talos audit repair
```

---

### E012: Rate Limited

**Symptoms**:
```
TalosError: E012 RATE_LIMITED: Rate limit exceeded (100/hour)
```

**Causes**:
- Too many requests
- Capability rate limit triggered

**Solutions**:

```python
import asyncio

# Implement backoff
async def send_with_backoff(client, peer, msg, max_retries=3):
    for i in range(max_retries):
        try:
            return await client.send(peer, msg)
        except RateLimitError:
            await asyncio.sleep(2 ** i)
    raise Exception("Rate limit exceeded")

# Request higher limit capability
cap = await client.request_capability(
    issuer=owner,
    scope="tools/api",
    constraints={"rate_limit": "1000/hour"}
)
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = await TalosClient.create(
    "agent",
    log_level="DEBUG"
)
```

### Inspect Session State

```python
# Get session info
session = client.get_session(peer_id)
print(f"Session state: {session.state}")
print(f"Sending chain index: {session.sending_chain_index}")
print(f"Receiving chain index: {session.receiving_chain_index}")
```

### Verify Connectivity

```bash
# Check connectivity
talos diagnose --network

# Test specific peer
talos ping did:talos:peer
```

### Export Diagnostics

```bash
# Export full diagnostic bundle
talos diagnose --export /tmp/debug.tar.gz
```

---

## Getting Help

1. Check this troubleshooting guide
2. Search [GitHub Issues](https://github.com/nileshchakraborty/talos/issues)
3. Enable debug logging and capture output
4. Open new issue with:
   - Error code and message
   - Talos version
   - Python version
   - Relevant logs

---

**See also**: [Python SDK](Python-SDK) | [Observability](Observability) | [Failure Modes](Failure-Modes)
