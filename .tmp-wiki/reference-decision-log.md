---
status: Implemented
audience: Developer, Contributor
---

# Decision Log

> **Problem**: Contributors need to understand why Talos is designed this way.  
> **Guarantee**: Explicit rationale for key design choices.  
> **Non-goal**: Justifying every line of code—just strategic decisions.

---

## Format

Each entry follows:
- **Decision**: What we chose
- **Alternatives**: What we considered
- **Rationale**: Why we chose this
- **Consequences**: Tradeoffs accepted

---

## Cryptography

### DEC-001: Double Ratchet over Static Encryption

**Decision**: Use Signal's Double Ratchet for all message encryption.

**Alternatives**:
- Static shared secret (simpler)
- TLS session keys (standard)
- Megolm (Matrix's group protocol)

**Rationale**:
- Per-message forward secrecy is the strongest guarantee
- Post-compromise security via DH ratchet
- Well-audited, proven in Signal
- Agents may operate for extended periods—static keys are dangerous

**Consequences**:
- Higher complexity in session management
- State must be maintained per-peer
- Session recovery is more complex

---

### DEC-002: Ed25519 + X25519 over RSA

**Decision**: Use Curve25519-based cryptography for all operations.

**Alternatives**:
- RSA-2048/4096 (legacy compatibility)
- NIST P-256 (enterprise acceptance)
- Post-quantum candidates (future-proofing)

**Rationale**:
- Modern, fast, small keys (32 bytes)
- Same security level as RSA-3072
- Ed25519: deterministic, no random number attacks
- SafeCurves compliant

**Consequences**:
- No legacy RSA compatibility
- Post-quantum migration planned but not implemented

---

### DEC-003: ChaCha20-Poly1305 over AES-GCM

**Decision**: Use ChaCha20-Poly1305 for symmetric encryption.

**Alternatives**:
- AES-GCM (hardware acceleration)
- AES-CBC + HMAC (legacy)

**Rationale**:
- Same cipher as TLS 1.3
- Fast on devices without AES-NI
- Resistant to timing attacks
- Single-pass authenticated encryption

**Consequences**:
- Slightly slower on AES-NI hardware
- No hardware acceleration benefit

---

## Architecture

### DEC-004: P2P over Client-Server

**Decision**: Fully peer-to-peer architecture with optional registry.

**Alternatives**:
- Client-server (simpler deployment)
- Federated (Matrix-style)
- Hybrid (libp2p + servers)

**Rationale**:
- No central point of failure or control
- Censorship resistance
- Agents can operate without infrastructure
- Registry is optional, not required

**Consequences**:
- NAT traversal complexity
- Peer discovery is harder
- No guaranteed message delivery without persistence

---

### DEC-005: WebSocket over TCP

**Decision**: Use WebSocket as primary transport.

**Alternatives**:
- Raw TCP (simpler)
- gRPC (bidirectional streaming)
- QUIC (modern, fast)

**Rationale**:
- Bidirectional without polling
- Built-in framing
- Works through HTTP proxies
- Easy upgrade to WebRTC later

**Consequences**:
- HTTP overhead
- QUIC migration planned

---

### DEC-006: LMDB over SQLite

**Decision**: Use LMDB for local storage.

**Alternatives**:
- SQLite (relational, familiar)
- RocksDB (LSM-tree)
- In-memory only (simplest)

**Rationale**:
- O(1) reads by key
- ACID transactions
- Memory-mapped for speed
- Already proven in blockchain storage

**Consequences**:
- No SQL queries
- Requires index management
- Platform-specific binaries

---

## Protocol

### DEC-007: Lightweight PoW over Consensus

**Decision**: Use proof-of-work for spam prevention, not consensus.

**Alternatives**:
- Full consensus (BFT)
- Proof-of-stake
- No spam protection

**Rationale**:
- Each node maintains local chain
- No global agreement needed for messaging
- Configurable difficulty
- Consensus is overkill for audit logs

**Consequences**:
- Not suitable for shared state
- Chain is per-node, not global

---

### DEC-008: Merkle Proofs over Full Replication

**Decision**: Use Merkle proofs for audit verification.

**Alternatives**:
- Full chain replication
- Trusted audit server
- No verification

**Rationale**:
- Light clients can verify without full chain
- O(log n) proof size
- Standard, well-understood
- Enables SPV-style verification

**Consequences**:
- Requires proof generation infrastructure
- Proofs must be stored or regenerated

---

### DEC-009: Capabilities over ACLs

**Decision**: First-class capability tokens, not just access control lists.

**Alternatives**:
- Role-based access control (RBAC)
- Static ACLs
- No authorization

**Rationale**:
- Capabilities are transferable
- Delegation is natural
- Revocation is explicit
- Better fit for agent autonomy

**Consequences**:
- Token management complexity
- Must handle expiry and revocation

---

## Audit

### DEC-010: Blockchain Anchoring over Database Logs

**Decision**: Anchor audit roots to blockchain.

**Alternatives**:
- Database with append-only flag
- Signed timestamps only
- Third-party audit service

**Rationale**:
- Cross-org trust without shared infrastructure
- Neutral verification
- Long-term availability
- Regulatory friendliness

**Consequences**:
- Chain dependency (optional but recommended)
- Periodic anchoring cost
- Latency for proof finality

---

### DEC-011: Surgical Blockchain Use

**Decision**: Only anchor hashes, never content.

**Alternatives**:
- Full message storage on-chain
- Full capability storage on-chain
- No blockchain

**Rationale**:
- Cost: blockchain storage is expensive
- Privacy: content should not be public
- Scale: messages happen at high frequency
- Speed: blockchain writes are slow

**Consequences**:
- Must maintain off-chain data
- Proofs require off-chain audit log access

---

## Identity

### DEC-012: DIDs over Usernames

**Decision**: Use W3C DIDs for identity.

**Alternatives**:
- Usernames (human-friendly)
- UUIDs (simple)
- Phone numbers (Signal-style)

**Rationale**:
- Self-sovereign, no registry required
- Interoperable with DID ecosystem
- Key-based, not account-based
- Supports key rotation via DID documents

**Consequences**:
- DID resolution complexity
- Anchoring optional but recommended

---

## MCP Integration

### DEC-013: Tunnel MCP, Don't Replace

**Decision**: Secure MCP traffic, don't reinvent MCP.

**Alternatives**:
- New RPC protocol
- MCP fork
- MCP shim

**Rationale**:
- MCP is established for tool invocation
- Talos adds security layer, not functionality
- Preserve MCP compatibility
- Focus on transport and authorization

**Consequences**:
- Dependent on MCP evolution
- Can't fix MCP design issues

---

## Future Decisions (Planned)

| Decision | Status | Description |
|----------|--------|-------------|
| DEC-014 | Planned | Intent + Execution proof separation |
| DEC-015 | Planned | Policy engine integration (OPA/Cedar) |
| DEC-016 | Planned | Group messaging protocol |
| DEC-017 | Planned | Post-quantum migration path |

---

**See also**: [Architecture](architecture-overview) | [Cryptography](security-cryptography) | [Future Improvements](research-future-improvements)
