---
status: Implemented
audience: Everyone
---

# Non-Goals

> **Problem**: Readers assume Talos does everything.  
> **Guarantee**: Explicit boundaries prevent misadoption.  
> **Non-goal**: This page is not criticism—it's clarity.

---

## Talos Is Not

### ❌ A General-Purpose Message Queue

Talos is **not** Kafka, RabbitMQ, or SQS.

**Why not**:
- No pub/sub fan-out
- No message persistence by default
- No topic-based routing
- Not optimized for throughput over security

**Use Talos when**: You need secure, authenticated, auditable messaging.

**Use message queues when**: You need high-throughput pub/sub without cryptographic identity.

---

### ❌ A Workflow Engine

Talos is **not** Temporal, Airflow, or Step Functions.

**Why not**:
- No workflow state machines
- No retry policies
- No saga orchestration
- No visual flow design

**Use Talos when**: Agents need secure communication during workflows.

**Use workflow engines when**: You need complex process orchestration.

---

### ❌ An AI Agent Framework

Talos is **not** LangChain, CrewAI, or AutoGPT.

**Why not**:
- Talos does not define agent behavior
- No prompting, no chains, no tools
- No memory management
- No LLM integration logic

**Use Talos when**: Your agent framework needs secure inter-agent communication.

**Use agent frameworks when**: You need to build agent logic and orchestration.

---

### ❌ A Sandbox for Malicious Agents

Talos **does not** protect against agents that:
- Are intentionally malicious
- Execute harmful tool calls
- Violate their own organization's policies

**Why not**:
- Talos secures *transport*, not *behavior*
- Capabilities limit scope but don't sandbox execution
- A malicious agent with valid capability can still cause harm

**What Talos provides**:
- Proof of who did what
- Non-repudiable audit for accountability
- Blast radius limitation via scoped capabilities

---

### ❌ Endpoint Security

Talos **does not** protect against:
- Compromised host machines
- Stolen private keys
- Malware on agent endpoints
- Physical access attacks

**Why not**:
- This is OS, hardware, and operational security
- Talos assumes agent endpoints are trusted
- Key management is the agent operator's responsibility

**See**: [Hardening Guide](Hardening-Guide) for mitigations.

---

### ❌ A Privacy Silver Bullet

Talos **does not** provide:
- Complete metadata hiding
- Sender/receiver anonymity
- Traffic analysis resistance
- Plausible deniability

**Why not**:
- Routing metadata is visible at transport layer
- Timing and message sizes can be correlated
- Full anonymity requires onion routing (planned future)

**What Talos provides**:
- Content confidentiality (E2EE)
- P2P reduces central observation
- Optional future metadata protections

---

### ❌ A Replacement for mTLS

Talos **is not** just mTLS with extra steps.

**Differences**:
- mTLS: transport-level, server identity
- Talos: application-level, agent identity
- mTLS: no forward secrecy per message
- Talos: Double Ratchet with key rotation
- mTLS: no audit trail
- Talos: blockchain-anchored proofs
- mTLS: no capability model
- Talos: scoped, revocable capabilities

**Use mTLS when**: You need transport security between services.

**Use Talos when**: You need agent identity, capabilities, and audit.

---

### ❌ A Blockchain for Data Storage

Talos **does not** store:
- Message contents on-chain
- Tool payloads on-chain
- Agent state on-chain
- Media or files on-chain

**Why not**:
- Cost: blockchain storage is expensive
- Latency: on-chain writes are slow
- Privacy: on-chain data is public
- Scale: doesn't work at message volume

**What blockchain does in Talos**:
- Identity anchors (rare)
- Capability commitment hashes (occasional)
- Audit root hashes (periodic, batched)
- Revocation events (rare)

---

### ❌ Real-Time Streaming

Talos **is not optimized for**:
- Audio/video streaming
- Sub-millisecond latency
- Continuous data flows

**Why not**:
- Cryptographic overhead per message
- Ratcheting on every message
- Audit commitment latency
- Not designed for throughput

**Future**: WebRTC integration planned for real-time use cases.

---

## Summary Table

| Capability | Talos Provides | Does Not Provide |
|------------|----------------|------------------|
| Secure messaging | ✅ | ❌ High-throughput pub/sub |
| Agent identity | ✅ | ❌ Agent behavior logic |
| Capability control | ✅ | ❌ Sandboxed execution |
| Audit trail | ✅ | ❌ Endpoint protection |
| Privacy | ✅ Content | ❌ Complete anonymity |
| Blockchain | ✅ Trust anchor | ❌ Data storage |

---

## Why This Matters

Documenting non-goals:
- **Prevents misadoption**: Users choose Talos correctly
- **Builds trust**: Honesty signals maturity
- **Focus development**: Scope stays crisp
- **Supports integrations**: Clear boundaries enable composition

---

**See also**: [Threat Model](Threat-Model) | [Why Talos Wins](Why-Talos-Wins)
