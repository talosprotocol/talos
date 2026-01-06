---
status: Implemented
audience: Security, Developer
---

# Protocol Guarantees

> **Problem**: Non-cryptographers need to understand Talos security.  
> **Guarantee**: Clear mapping from property to mechanism.  
> **Non-goal**: Full cryptographic proofs—see [Security Proof](Mathematical-Security-Proof).

---

## Guarantee Summary

| Guarantee | How Talos Provides It | Status |
|-----------|----------------------|--------|
| **Confidentiality** | Double Ratchet + E2EE | ✅ Implemented |
| **Authenticity** | Ed25519 identity signatures | ✅ Implemented |
| **Forward Secrecy** | Ephemeral key ratcheting | ✅ Implemented |
| **Post-Compromise Security** | DH ratchet recovery | ✅ Implemented |
| **Non-Repudiation** | Blockchain-anchored audit | ✅ Implemented |
| **Integrity** | Poly1305 MAC + chain hashing | ✅ Implemented |
| **Replay Resistance** | Nonces + ordering | ✅ Implemented |
| **Capability Control** | Scoped, expiring tokens | ✅ Implemented |
| **Verifiability** | Merkle proofs | ✅ Implemented |
| **Censorship Resistance** | P2P routing | ✅ Implemented |
| **Metadata Protection** | Content E2EE, routing visible | ⚠️ Partial |

---

## Detailed Guarantees

### Confidentiality

**Property**: Only intended recipients can read message contents.

**Mechanism**:
- ChaCha20-Poly1305 authenticated encryption
- Per-message keys from Double Ratchet
- No plaintext touches the wire or storage

**What it means**: Even network observers, registry servers, or compromised peers cannot read your messages.

---

### Authenticity

**Property**: Messages provably came from claimed sender.

**Mechanism**:
- Ed25519 digital signatures on every message
- Signatures cover: sender, recipient, timestamp, content hash
- Identity keys are long-lived and verifiable

**What it means**: You can cryptographically verify who sent a message. Spoofing is computationally infeasible.

---

### Forward Secrecy

**Property**: Compromise of current keys does not reveal past messages.

**Mechanism**:
- Double Ratchet advances key on every message
- Symmetric ratchet: HKDF key derivation
- DH ratchet: new ephemeral keys periodically
- Old keys are deleted after use

**What it means**: If an attacker steals your keys today, they cannot decrypt messages from yesterday.

---

### Post-Compromise Security

**Property**: Session recovers security after temporary compromise.

**Mechanism**:
- DH ratchet introduces new randomness
- After sufficient message exchange, attacker loses access
- Even if attacker saw all state at time T, they cannot read messages after re-keying

**What it means**: A breach is not permanent. Security self-heals over time.

---

### Non-Repudiation

**Property**: Participants cannot deny actions they performed.

**Mechanism**:
- All significant events (messages, capabilities, sessions) are logged
- Logs are Merkle-proofed
- Merkle roots are anchored to blockchain
- Proofs are independently verifiable

**What it means**: You can prove in court or to auditors what happened, without trusting any party's word.

---

### Integrity

**Property**: Messages cannot be modified in transit.

**Mechanism**:
- Poly1305 MAC authenticated encryption
- Block hash chaining in audit log
- Validation engine rejects invalid data

**What it means**: Tampering is detectable. Modified messages are rejected.

---

### Replay Resistance

**Property**: Old messages cannot be re-sent to cause duplicate actions.

**Mechanism**:
- Unique message IDs with nonce
- Timestamp validation windows
- Blockchain ordering provides global sequence
- Ratchet state prevents key reuse

**What it means**: Attackers cannot replay captured messages to trigger repeated actions.

---

### Capability Control

**Property**: Actions are authorized by explicit, verifiable grants.

**Mechanism**:
- Capabilities specify scope, constraints, expiry
- Capability hash anchored on-chain
- Tools verify capability before execution
- Revocation is logged and verifiable

**What it means**: Agents can only do what they're explicitly authorized to do, for as long as they're authorized.

---

### Verifiability

**Property**: Claims about the system can be cryptographically verified.

**Mechanism**:
- Merkle proofs for audit log inclusion
- Signature verification for all artifacts
- Blockchain anchors for cross-org trust
- Light client SPV verification

**What it means**: You don't have to trust anyone's word. Everything is provable.

---

### Censorship Resistance

**Property**: No single party can block communication.

**Mechanism**:
- Peer-to-peer architecture
- No central server dependency
- DHT-based peer discovery
- Multiple transport options

**What it means**: If at least one path exists between peers, communication succeeds.

---

### Metadata Protection (Partial)

**Property**: Minimize information leakage about who communicates.

**Current state**:
- ✅ Content is encrypted
- ✅ P2P reduces central observation
- ⚠️ Peer IDs visible at transport layer
- ⚠️ Message timing can be correlated
- ⚠️ Message sizes can be inferred

**Planned**:
- Onion routing
- Traffic padding
- Cover traffic

**What it means**: Content is private, but network-level observers can learn communication patterns.

---

## Security vs. Convenience Tradeoffs

| Tradeoff | Talos Choice | Rationale |
|----------|--------------|-----------|
| Forward secrecy vs. key stability | Forward secrecy | Security over convenience |
| Audit immutability vs. deletion | Immutability | Proof over forgetting |
| Decentralization vs. consistency | Decentralization | Availability over strong consistency |
| Per-message encryption vs. session | Per-message | Granular forward secrecy |

---

## What Guarantees Require

| Guarantee | Requires |
|-----------|----------|
| Confidentiality | Recipient online to exchange keys |
| Forward secrecy | Both parties delete old keys |
| Non-repudiation | Audit log not corrupted locally |
| Post-compromise | DH exchange after compromise |
| Censorship resistance | At least one network path |

---

**See also**: [Threat Model](Threat-Model) | [Cryptography](Cryptography) | [Security Proof](Mathematical-Security-Proof)
