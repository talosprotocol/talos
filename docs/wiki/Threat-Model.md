---
status: Implemented
audience: Security, Developer
---

# Threat Model

> **Problem**: Security reviewers need to know what Talos defends against.  
> **Guarantee**: Explicit threat enumeration with mitigations.  
> **Non-goal**: Defend against everything—see [Non-Goals](Non-Goals).

---

## What Talos Defends Against

### 1. Man-in-the-Middle (MITM)

**Threat**: Attacker intercepts and modifies communication between agents.

**Mitigation**:
- End-to-end encryption with authenticated key exchange
- X25519 ECDH with Ed25519 signature verification
- Session keys bound to verified identities

**Status**: ✅ Defended

---

### 2. Replay Attacks

**Threat**: Attacker re-transmits captured messages to cause duplicate actions.

**Mitigation**:
- Message IDs with nonce
- Timestamp validation
- Blockchain ordering provides global sequence
- Double Ratchet prevents key reuse

**Status**: ✅ Defended

---

### 3. Impersonation

**Threat**: Attacker pretends to be a legitimate agent.

**Mitigation**:
- Ed25519 digital signatures on all messages
- Identity bound to keypair
- Prekey bundles signed by identity key
- Optional DID anchoring on-chain

**Status**: ✅ Defended

---

### 4. Key Compromise (Current)

**Threat**: Attacker obtains an agent's current session key.

**Mitigation**:
- Forward secrecy via Double Ratchet
- Each message derives a new key
- Old keys are deleted after use
- Compromise of key N does not reveal messages 1…N-1

**Status**: ✅ Defended (past messages)

---

### 5. Key Compromise (Future / Break-in Recovery)

**Threat**: Attacker compromises session state but communication continues.

**Mitigation**:
- Ratchet advances on every message
- New DH exchanges restore security
- Attacker loses access after sufficient ratcheting

**Status**: ✅ Defended (after DH exchange)

---

### 6. Metadata Leakage (Partial)

**Threat**: Attacker learns who communicates with whom, when, and how often.

**Mitigation**:
- P2P routing reduces central observation
- Message content is encrypted
- Future: onion routing planned

**Status**: ⚠️ Partially Defended

**What leaks**:
- Peer IDs at transport layer
- Timing of messages
- Message sizes

**See**: [Security Properties](Security-Properties)

---

### 7. Censorship

**Threat**: Network operator blocks agent communication.

**Mitigation**:
- P2P architecture with no central server
- DHT-based peer discovery
- Multiple transport options
- Resilient to single-node failures

**Status**: ✅ Defended (with caveats)

**Limitation**: If all peers are blocked, no communication is possible.

---

### 8. Rogue Peers

**Threat**: Malicious peers join the network and attempt to:
- Flood with invalid data
- Disrupt routing
- Harvest metadata

**Mitigation**:
- Lightweight proof-of-work on blocks
- Signature verification on all messages
- Validation engine rejects invalid blocks
- Peer reputation (planned extension)

**Status**: ✅ Defended

---

### 9. Audit Log Tampering

**Threat**: Agent or attacker modifies historical audit records.

**Mitigation**:
- Append-only Merkle tree structure
- Hash chaining prevents insertion/deletion
- Blockchain anchoring provides external witness
- Merkle proofs are independently verifiable

**Status**: ✅ Defended

---

### 10. Capability Abuse

**Threat**: Agent uses capability beyond its authorized scope.

**Mitigation**:
- Capabilities are scoped and expiring
- Enforcement at tool/resource level
- Revocation is committed and verifiable
- Capability hashes anchored on-chain

**Status**: ✅ Defended

---

## What Talos Does NOT Defend Against

> [!CAUTION]
> The following threats are explicitly outside Talos scope.

### Endpoint Compromise

**Threat**: Attacker gains control of the agent's host machine.

**Impact**: Attacker can:
- Extract private keys
- Read decrypted messages
- Impersonate the agent

**Why not defended**:
- This is an OS/hardware security problem
- Talos assumes the endpoint is trusted
- See [Hardening Guide](Hardening-Guide) for mitigations

---

### Prompt Injection

**Threat**: Malicious input causes LLM to take unintended actions.

**Impact**: Agent may invoke tools incorrectly.

**Why not defended**:
- This is an LLM security problem
- Talos secures *transport and authorization*, not *model behavior*
- Capabilities limit blast radius, but don't prevent injection

---

### Malicious Tools

**Threat**: A tool performs harmful actions when invoked.

**Impact**: Agent executes harmful operations.

**Why not defended**:
- Talos proves *who invoked what*
- Talos cannot verify *what the tool does*
- This is a tool validation / sandboxing problem

---

### Denial of Service (Network-Level)

**Threat**: Attacker floods network with traffic, preventing communication.

**Why partially defended**:
- Proof-of-work rate limits spam
- But high-bandwidth attacks can still disrupt
- This is a network infrastructure problem

---

### Coercion / Legal Compulsion

**Threat**: Agent operator is legally forced to disclose keys.

**Why not defended**:
- Keys can be disclosed under compulsion
- Forward secrecy protects *past* messages
- But current and future are vulnerable
- This is a legal / operational problem

---

## Threat Summary Table

| Threat | Status | Notes |
|--------|--------|-------|
| MITM | ✅ Defended | E2EE + authenticated exchange |
| Replay | ✅ Defended | Nonces + ordering + ratchet |
| Impersonation | ✅ Defended | Ed25519 signatures |
| Key Compromise (past) | ✅ Defended | Forward secrecy |
| Key Compromise (future) | ✅ Defended | Break-in recovery |
| Metadata Leakage | ⚠️ Partial | Content hidden, routing visible |
| Censorship | ✅ Defended | P2P, no central server |
| Rogue Peers | ✅ Defended | Validation + PoW |
| Audit Tampering | ✅ Defended | Merkle + blockchain |
| Capability Abuse | ✅ Defended | Scoped + revocable |
| Endpoint Compromise | ❌ Out of scope | OS/hardware problem |
| Prompt Injection | ❌ Out of scope | LLM problem |
| Malicious Tools | ❌ Out of scope | Tool validation problem |
| Network DoS | ⚠️ Partial | PoW helps, not eliminated |
| Legal Compulsion | ❌ Out of scope | Operational problem |

---

**See also**: [Non-Goals](Non-Goals) | [Security Properties](Security-Properties) | [Hardening Guide](Hardening-Guide)
