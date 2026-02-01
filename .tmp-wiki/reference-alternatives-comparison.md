---
status: Implemented
audience: Everyone
---

# Alternatives Comparison

> **Problem**: How does Talos compare to existing solutions?  
> **Guarantee**: Honest comparison with clear differentiators.  
> **Non-goal**: Marketing—just facts.

---

## Comparison Matrix

| Solution | Agent Identity | Forward Secrecy | Audit Trail | Capabilities | Decentralized | Agent-Native |
|----------|---------------|-----------------|-------------|--------------|---------------|--------------|
| **Talos** | ✅ Cryptographic | ✅ Double Ratchet | ✅ Blockchain-anchored | ✅ Scoped/revocable | ✅ P2P | ✅ Built for agents |
| Matrix | ✅ User-based | ✅ Megolm | ⚠️ Server logs | ❌ None | ⚠️ Federated | ❌ Human-centric |
| Signal | ✅ Phone-based | ✅ Double Ratchet | ❌ None | ❌ None | ❌ Centralized | ❌ Human-centric |
| gRPC + mTLS | ⚠️ Service certs | ❌ None | ❌ None | ❌ None | ❌ Client-server | ❌ Service-centric |
| Kafka | ❌ None | ❌ None | ⚠️ Log retention | ❌ None | ❌ Broker-based | ❌ Infra-centric |
| NATS | ❌ None | ❌ None | ❌ None | ⚠️ Accounts | ❌ Cluster-based | ❌ Infra-centric |
| libp2p | ⚠️ Peer IDs | ⚠️ Noise only | ❌ None | ❌ None | ✅ P2P | ⚠️ Transport only |
| OIDC | ✅ User tokens | ❌ None | ❌ None | ⚠️ Scopes | ❌ IdP-dependent | ❌ Human-centric |
| DIDComm | ✅ DIDs | ⚠️ Optional | ❌ None | ❌ None | ✅ Decentralized | ⚠️ Credential-focused |

---

## Detailed Comparisons

### vs. Matrix

**Matrix** is a federated chat protocol with Megolm E2EE.

| Aspect | Matrix | Talos |
|--------|--------|-------|
| Primary use | Human chat rooms | Agent-to-agent communication |
| Identity | User accounts on homeservers | Cryptographic keypairs |
| Forward secrecy | Session-level (Megolm) | Per-message (Double Ratchet) |
| Audit | Server logs | Blockchain-anchored proofs |
| Capabilities | None | First-class, scoped |
| Decentralization | Federated (homeservers) | Fully P2P |

**When to use Matrix**: Human collaboration, chat rooms, bridges to other platforms.

**When to use Talos**: Autonomous agents, tool invocation, audit-critical workflows.

---

### vs. Signal

**Signal** is the gold standard for human E2EE messaging.

| Aspect | Signal | Talos |
|--------|--------|-------|
| Primary use | Human messaging | Agent communication |
| Identity | Phone numbers | Cryptographic DIDs |
| Forward secrecy | ✅ Double Ratchet | ✅ Double Ratchet |
| Audit | None (privacy-first) | First-class (accountability-first) |
| Capabilities | None | Scoped authorization |
| Server | Centralized (Signal servers) | P2P |

**When to use Signal**: Private human communication.

**When to use Talos**: Agents that need to prove what they did.

---

### vs. gRPC + mTLS

**gRPC + mTLS** is standard service-to-service transport security.

| Aspect | gRPC + mTLS | Talos |
|--------|-------------|-------|
| Primary use | Microservices | Agent communication |
| Identity | Service certificates | Agent keypairs |
| Forward secrecy | None per message | Per-message ratcheting |
| Audit | None built-in | Blockchain-anchored |
| Capabilities | None | First-class |
| Trust model | CA-based | Self-sovereign |

**When to use gRPC + mTLS**: Internal service mesh, known services.

**When to use Talos**: Cross-org agents, audit requirements, dynamic authorization.

---

### vs. Kafka / SQS / NATS

**Message queues** provide reliable message delivery.

| Aspect | Message Queues | Talos |
|--------|---------------|-------|
| Primary use | Event streaming, decoupling | Secure agent messaging |
| Encryption | TLS in transit | E2EE per message |
| Identity | Broker ACLs | Cryptographic per-agent |
| Audit | Log retention | Merkle proofs |
| Capabilities | Topic-level | Fine-grained per-action |
| Trust | Trust the broker | Trust cryptography |

**When to use message queues**: High-throughput pub/sub, event sourcing.

**When to use Talos**: When you can't trust the infrastructure, need proof.

---

### vs. libp2p

**libp2p** is a modular P2P networking stack.

| Aspect | libp2p | Talos |
|--------|--------|-------|
| Primary use | P2P transport | Secure agent protocol |
| Identity | Peer IDs | DIDs + prekey bundles |
| Encryption | Noise framework | Double Ratchet |
| Forward secrecy | Session-level | Per-message |
| Audit | None | First-class |
| Capabilities | None | First-class |

**When to use libp2p**: Building P2P applications, IPFS ecosystem.

**When to use Talos**: When you need identity, authorization, and audit on top.

---

### vs. OIDC / OAuth

**OIDC** provides human identity federation.

| Aspect | OIDC | Talos |
|--------|------|-------|
| Primary use | Human SSO | Agent identity |
| Identity | Provider-issued tokens | Self-sovereign keys |
| Trust model | Trust the IdP | Trust cryptography |
| Forward secrecy | None | Per-message |
| Audit | IdP logs | Blockchain-anchored |
| Decentralization | IdP-dependent | Fully decentralized |

**When to use OIDC**: Human login, enterprise SSO.

**When to use Talos**: Agents operating across trust boundaries.

---

### vs. DIDComm

**DIDComm** is a W3C protocol for DID-based messaging.

| Aspect | DIDComm | Talos |
|--------|---------|-------|
| Primary use | Verifiable credentials | Agent communication |
| Identity | DIDs | DIDs (compatible) |
| Encryption | JWE | Double Ratchet |
| Forward secrecy | Optional | Mandatory |
| Audit | None | First-class |
| MCP focus | None | Native |

**When to use DIDComm**: Credential exchange, identity wallets.

**When to use Talos**: Agent-to-agent + tool invocation + audit.

---

## Why Talos Wins for Agents

The unique Talos combination:

1. **Agent-native identity**: Not users, not services—agents
2. **Per-message forward secrecy**: Not just session encryption
3. **Blockchain-anchored audit**: Proofs, not logs
4. **First-class capabilities**: Authorization is core, not bolted on
5. **MCP integration**: Built for tool invocation
6. **Decentralized**: No trust in infrastructure

No existing solution provides all of these together.

---

**See also**: [Why Talos Wins](business-why-talos-wins) | [Non-Goals](non-goals) | [Talos in 60 Seconds](getting-started-talos-60-seconds)
