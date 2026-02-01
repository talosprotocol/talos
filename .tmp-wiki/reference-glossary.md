---
status: Implemented
audience: Everyone
---

# Glossary

> **Problem**: New readers encounter unfamiliar terms.  
> **Guarantee**: Clear, consistent definitions.  
> **Non-goal**: Deep explanations—see linked pages.

---

## A

### ACL (Access Control List)

A set of rules specifying which peers can access which resources. In Talos, ACLs are fine-grained and cryptographically enforced. See [Access Control](features-authorization-access-control).

### Agent

An autonomous software entity that can:

- Hold cryptographic keys
- Act on its own behalf
- Sign messages and intents
- Be audited post-hoc

Agents are the primary actors in Talos, distinct from human users or traditional services.

### Attestation

A signed statement by one identity about another. Used for trust and reputation extension points.

### Audit Log

An append-only record of significant events (messages, capability grants, sessions). Merkle-proofed and optionally blockchain-anchored. See [Audit Explorer](features-observability-audit-explorer).

---

## C

### Capability

A token that authorizes a specific action, constrained by:

- **Scope**: What action/resource
- **Expiry**: When it ends
- **Constraints**: Rate limits, parameters
- **Delegation**: Whether it can be passed on

See [Agent Capabilities](features-authorization-agent-capabilities).

---

## D

### Delegation

The act of passing a capability from one agent to another, potentially with reduced scope.

### DID (Decentralized Identifier)

A W3C standard for self-sovereign identifiers. In Talos, DIDs can be anchored on-chain. Format: `did:talos:<unique-id>`. See [DIDs & DHT](features-identity-dids-dht).

### DHT (Distributed Hash Table)

A peer-to-peer data structure for decentralized lookup. Talos uses Kademlia-style DHT for peer discovery.

### Double Ratchet

The Signal protocol's key derivation algorithm providing forward secrecy. Every message uses a new key; old keys are deleted. See [Double Ratchet](features-messaging-double-ratchet).

---

## E

### E2EE (End-to-End Encryption)

Encryption where only the communicating parties can decrypt—no intermediary (including Talos infrastructure) can read the content.

---

## F

### Forward Secrecy

A property where compromise of current keys does not compromise past messages. Achieved through ephemeral key ratcheting.

---

## I

### Identity

A cryptographic keypair representing an agent:

- **Ed25519**: For signing
- **X25519**: For encryption
- **Peer ID**: Hash of public key

Identities can optionally be anchored as DIDs.

### Intent

A signed declaration of what an agent wants to do, distinct from execution. Capabilities authorize intent; sessions enable execution.

---

## M

### Merkle Proof

A cryptographic proof that a piece of data exists in a Merkle tree. Used for audit verification without revealing the full log.

### MCP (Model Context Protocol)

Anthropic's protocol for LLM-tool communication. Talos secures MCP through encrypted tunneling. See [MCP Integration](features-integrations-mcp-integration).

---

## N

### Non-repudiation

The property that an agent cannot deny having performed an action, because it is cryptographically signed and audited.

---

## P

### Peer

Another agent in the network that you can communicate with.

### Peer ID

A unique identifier for an agent, derived from its public key. Format: `did:talos:<hash>` or raw hex.

### Prekey Bundle

A package of public keys that allows another agent to initiate a secure session without prior contact. Contains:

- Identity public key
- Signed prekey
- One-time prekeys (optional)

### Proof

A verifiable cryptographic attestation. In Talos, usually a Merkle proof of audit log inclusion.

---

## R

### Ratchet

A cryptographic mechanism that moves forward irreversibly. In Double Ratchet, keys are derived and immediately deleted, preventing backward derivation.

### Revocation

The act of invalidating an identity or capability. Revocation events are committed to the audit log and optionally anchored on-chain.

---

## S

### Session

An encrypted communication channel between two agents, established via prekey bundle exchange and maintained with Double Ratchet.

### SPV (Simplified Payment Verification)

Light client verification using Merkle proofs instead of full chain validation. See [Light Client](research-light-client).

---

## T

### Trust Anchor

An on-chain commitment (identity hash, capability hash, audit root) that provides external verifiability.

---

## V

### Validation

Verification that a block, message, or proof meets protocol rules. Talos uses 5-layer validation. See [Validation Engine](security-validation-engine).

---

**See also**: [Mental Model](getting-started-mental-model) | [Protocol Guarantees](architecture-protocol-guarantees)
