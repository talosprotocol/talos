---
status: Implemented
audience: Security, Developer
---

# Audit Scope

> **Problem**: People assume wrong things about what's audited.  
> **Guarantee**: Explicit definition of what is and isn't recorded.  
> **Non-goal**: Covering every possible event.

---

## What Is Audited

### ✅ Message Events

| Field                 | Stored | Notes                 |
| --------------------- | ------ | --------------------- |
| Content hash          | ✅ Yes | SHA-256 of plaintext  |
| Sender ID             | ✅ Yes | DID or peer ID        |
| Recipient ID          | ✅ Yes | DID or peer ID        |
| Timestamp             | ✅ Yes | ISO 8601              |
| Sender signature      | ✅ Yes | Ed25519               |
| Message type          | ✅ Yes | TEXT, FILE, MCP, etc. |
| **Plaintext content** | ❌ No  | Only hash stored      |
| **Encrypted content** | ❌ No  | Not persisted         |

**Implication**: You can prove a message was sent, but you cannot recover its contents from the audit log alone.

---

### ✅ Session Events

| Event                  | Audited          |
| ---------------------- | ---------------- |
| Session established    | ✅ Yes           |
| Session terminated     | ✅ Yes           |
| Peer identities        | ✅ Yes           |
| Session ID             | ✅ Yes           |
| Prekey bundle exchange | ✅ Yes           |
| Ratchet state          | ❌ No (security) |

---

### ✅ Capability Events

| Event                      | Audited          |
| -------------------------- | ---------------- |
| Capability granted         | ✅ Yes           |
| Capability scope           | ✅ Yes           |
| Capability constraints     | ✅ Yes           |
| Capability expiry          | ✅ Yes           |
| Capability revoked         | ✅ Yes           |
| Revocation reason          | ✅ Yes           |
| Delegation chain           | ✅ Yes           |
| **Capability token value** | ❌ No (security) |

**Implication**: You can prove a capability was granted, but cannot reconstruct the token.

---

### ✅ Identity Events

| Event               | Audited              |
| ------------------- | -------------------- |
| Identity created    | ✅ Yes               |
| Public key          | ✅ Yes               |
| DID document        | ✅ Yes (if anchored) |
| Key rotation        | ✅ Yes               |
| Identity revocation | ✅ Yes               |
| **Private key**     | ❌ No (never)        |

---

### ✅ MCP Tool Events

| Event                     | Audited            |
| ------------------------- | ------------------ |
| Tool invocation request   | ✅ Yes             |
| Tool ID                   | ✅ Yes             |
| Invoking agent            | ✅ Yes             |
| Capability reference      | ✅ Yes             |
| Invocation hash           | ✅ Yes             |
| Tool response hash        | ✅ Yes (if signed) |
| **Tool parameters**       | ⚠️ Hash only       |
| **Tool response content** | ⚠️ Hash only       |

**Implication**: You can prove which tool was called by whom, but not the exact input/output.

---

## What Is NOT Audited

### ❌ Message Contents

Plaintext message contents are **never** stored in the audit log.

**Why**: Privacy. The audit log may be shared or anchored publicly.

**What's stored instead**: SHA-256 hash of the plaintext.

**Verification**: If you have the plaintext, you can prove it matches the hash.

---

### ❌ Encryption Keys

Session keys, ratchet state, and ephemeral keys are **never** audited.

**Why**: Security. Auditing keys would undermine forward secrecy.

---

### ✅ Network Metadata

| Metadata          | Audited | Notes                                              |
| ----------------- | ------- | -------------------------------------------------- |
| IP addresses      | ✅ HMAC | Hashed with SHA256 + Private Salt (Key-ID tracked) |
| IP Trust          | ✅ Yes  | Hashed ONLY if derived from trusted proxy hop      |
| Transport details | ❌ No   |                                                    |
| Routing paths     | ❌ No   |                                                    |
| Connection times  | ❌ No   |                                                    |

**Why**: IP Hashing allows security teams to correlate threats/abuse without storing PII in the persistent log. If the IP is from an untrusted client, it is omitted to prevent log pollution.

---

### ❌ Local Agent State

| State               | Audited |
| ------------------- | ------- |
| Agent configuration | ❌ No   |
| Local storage       | ❌ No   |
| Memory state        | ❌ No   |
| Pending messages    | ❌ No   |

**Why**: Out of scope. Local state is agent's responsibility.

---

## Audit Levels

Talos supports configurable audit verbosity:

| Level      | What's Logged                            |
| ---------- | ---------------------------------------- |
| `minimal`  | Message hashes, session starts/ends      |
| `standard` | + Capabilities, identity events          |
| `verbose`  | + All MCP invocations, detailed metadata |
| `debug`    | + Internal protocol events (dev only)    |

```python
client = TalosClient.create("agent", audit_level="standard")
```

---

## Privacy Considerations

### What Can Be Proven

With audit log access, you can prove:

- ✅ A message was sent from A to B at time T
- ✅ A capability was granted with scope S
- ✅ A tool was invoked by agent A
- ✅ An identity existed with public key K

### What Cannot Be Proven (Without Original Data)

- ❌ What the message said
- ❌ What the tool parameters were
- ❌ What the tool returned
- ❌ Why a capability was granted

### Selective Disclosure

If you have the original data, you can:

1. Compute its hash
2. Show it matches the audit entry
3. Prove the entry exists via Merkle proof

This enables **privacy-preserving accountability**: reveal only what you choose.

---

## Blockchain Anchoring

The following is anchored on-chain:

| Data               | On-Chain          |
| ------------------ | ----------------- |
| Merkle root        | ✅ Yes (periodic) |
| Identity anchors   | ✅ Yes (optional) |
| Capability hashes  | ✅ Yes (optional) |
| Revocation events  | ✅ Yes            |
| **Full audit log** | ❌ No             |
| **Any content**    | ❌ No             |

**Frequency**: Audit roots anchored every N minutes or M entries (configurable).

---

## Summary Table

| Category             | Logged | Hash Only | Not Logged |
| -------------------- | ------ | --------- | ---------- |
| Message existence    | ✅     |           |            |
| Message content      |        | ✅        |            |
| Participant IDs      | ✅     |           |            |
| Session events       | ✅     |           |            |
| Session keys         |        |           | ✅         |
| Capabilities granted | ✅     |           |            |
| Capability tokens    |        |           | ✅         |
| Tool invocations     | ✅     |           |            |
| Tool parameters      |        | ✅        |            |
| Identity events      | ✅     |           |            |
| Private keys         |        |           | ✅         |
| Network metadata     |        | HMAC      |            |

---

**See also**: [Audit Explorer](Audit-Explorer) | [Security Properties](Security-Properties) | [Protocol Guarantees](Protocol-Guarantees)
