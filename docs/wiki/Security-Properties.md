---
status: Implemented
audience: Security
---

# Security Properties

> **Problem**: Engineers need formal security property definitions.  
> **Guarantee**: Clear status of each property.  
> **Non-goal**: Formal proofs—see [Security Proof](Mathematical-Security-Proof).

---

## Property Status Legend

| Status | Meaning |
|--------|---------|
| ✅ **Achieved** | Fully implemented and tested |
| ⚠️ **Partial** | Implemented with caveats |
| 🎯 **Goal** | Targeted but not fully achieved |
| 📋 **Planned** | On roadmap |

---

## Core Security Properties

### Confidentiality

**Definition**: Only intended recipients can read message contents.

**Status**: ✅ **Achieved**

**Implementation**:
- ChaCha20-Poly1305 authenticated encryption
- Per-message keys from Double Ratchet
- No plaintext in transit or storage

**Caveats**: None

---

### Authenticity

**Definition**: Messages provably originate from claimed sender.

**Status**: ✅ **Achieved**

**Implementation**:
- Ed25519 digital signatures on all messages
- Identity bound to keypair
- Signature verification mandatory

**Caveats**: None

---

### Integrity

**Definition**: Messages cannot be modified without detection.

**Status**: ✅ **Achieved**

**Implementation**:
- Poly1305 MAC on encrypted content
- Hash chaining in audit log
- Block validation rejects tampering

**Caveats**: None

---

### Forward Secrecy

**Definition**: Compromise of current keys doesn't reveal past messages.

**Status**: ✅ **Achieved**

**Implementation**:
- Double Ratchet with per-message key derivation
- Old keys deleted after use
- Symmetric ratchet on every message

**Caveats**: Requires both parties to delete old keys

---

### Post-Compromise Security (PCS)

**Definition**: Security recovers after temporary key compromise.

**Status**: ✅ **Achieved**

**Implementation**:
- DH ratchet introduces new randomness
- New DH exchange restores security
- Attacker loses access after healing

**Caveats**: Requires DH exchange (not every message)

---

### Non-Repudiation

**Definition**: Participants cannot deny actions they performed.

**Status**: ✅ **Achieved**

**Implementation**:
- All significant events logged
- Merkle-proofed audit log
- Blockchain anchoring for external verification

**Caveats**: Depends on key security at endpoints

---

### Replay Resistance

**Definition**: Old messages cannot trigger duplicate actions.

**Status**: ✅ **Achieved**

**Implementation**:
- Unique message IDs with nonce
- Timestamp validation
- Ratchet state prevents key reuse
- Deduplication window

**Caveats**: Window-based (configurable, default 1 hour)

---

### Capability Confinement

**Definition**: Capabilities cannot be used beyond their scope.

**Status**: ✅ **Achieved**

**Implementation**:
- Scoped tokens with constraints
- Expiry enforcement
- Revocation checking
- Delegation narrows scope

**Caveats**: Enforcement at tool layer; Talos provides policy, not sandbox

---

## Partial Properties

### Metadata Protection

**Definition**: Minimize leakage about who communicates.

**Status**: ⚠️ **Partial**

**What's protected**:
- Message content (E2EE)
- Payload structure

**What leaks**:
- Peer IDs at transport layer
- Message timing
- Message sizes
- Communication graph

**Planned improvements**:
- Onion routing
- Traffic padding
- Cover traffic

---

### Deniability

**Definition**: Participants can deny participation.

**Status**: ⚠️ **Partial**

**Reality**:
- Signatures provide non-repudiation (intended)
- This conflicts with deniability (by design)

**Talos choice**: Non-repudiation over deniability for audit use cases.

---

### Availability

**Definition**: System remains usable under attack.

**Status**: ⚠️ **Partial**

**What's provided**:
- P2P reduces single point of failure
- Proof-of-work limits spam
- Multiple registry fallback

**What's not solved**:
- Network-level DDoS
- Complete network isolation
- All-peer collusion

---

## Planned Properties

### Post-Quantum Security

**Definition**: Security against quantum computer attacks.

**Status**: 📋 **Planned**

**Roadmap**:
- CRYSTALS-Kyber for key exchange
- CRYSTALS-Dilithium for signatures
- Hybrid mode during transition

---

### Group Forward Secrecy

**Definition**: Forward secrecy for group messages.

**Status**: 📋 **Planned**

**Roadmap**:
- MLS (Messaging Layer Security) style groups
- Or Sender Keys model

---

### Anonymous Routing

**Definition**: Hide communication endpoints.

**Status**: 📋 **Planned**

**Roadmap**:
- Onion routing integration
- Mix networks consideration

---

## Property Matrix

| Property | Status | Notes |
|----------|--------|-------|
| Confidentiality | ✅ Achieved | E2EE mandatory |
| Authenticity | ✅ Achieved | Ed25519 signatures |
| Integrity | ✅ Achieved | MAC + hash chains |
| Forward Secrecy | ✅ Achieved | Per-message |
| Post-Compromise Security | ✅ Achieved | DH ratchet |
| Non-Repudiation | ✅ Achieved | Audit proofs |
| Replay Resistance | ✅ Achieved | Windowed |
| Capability Confinement | ✅ Achieved | Policy level |
| Metadata Protection | ⚠️ Partial | Content only |
| Deniability | ⚠️ Partial | Not a goal |
| Availability | ⚠️ Partial | P2P helps |
| Post-Quantum | 📋 Planned | Roadmap |
| Group FS | 📋 Planned | Roadmap |
| Anonymity | 📋 Planned | Roadmap |

---

## Formal Model

For formal security proofs, see [Mathematical Security Proof](Mathematical-Security-Proof).

Key assumptions:
1. Cryptographic primitives are secure
2. Random number generation is unpredictable
3. Endpoints are not compromised
4. Network attacker is Dolev-Yao

---

**See also**: [Threat Model](Threat-Model) | [Protocol Guarantees](Protocol-Guarantees) | [Cryptography](Cryptography)
