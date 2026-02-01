---
status: Implemented
audience: Business
---

# Ideal Customer Profile (ICP)

> **Problem**: Who should use Talos?  
> **Guarantee**: Clear target segments with use cases.  
> **Non-goal**: Exhaustive market analysis.

---

## Primary ICPs

### ICP 1: Agent Framework Developers

**Who**:
- Teams building multi-agent systems
- LLM orchestration framework maintainers
- AI tool integration developers

**Pain points**:
- No standardized agent identity
- No secure agent-to-agent communication
- No way to audit agent actions
- Tool invocation is insecure

**Talos value**:
- Drop-in identity and encryption layer
- MCP security out of the box
- Audit proofs for debugging and compliance

**Examples**:
- LangChain ecosystem developers
- CrewAI / AutoGPT teams
- Custom agent orchestrators

**Entry point**: SDK integration, `pip install talos-protocol`

---

### ICP 2: Enterprise AI Teams

**Who**:
- Companies deploying autonomous AI workflows
- Internal AI platform teams
- MLOps / AI infrastructure teams

**Pain points**:
- AI actions are not auditable
- Cross-team agent collaboration is ad-hoc
- No capability-based access control
- Compliance requirements are unclear

**Talos value**:
- Non-repudiable audit trails
- Fine-grained capability tokens
- Works with existing infrastructure
- Compliance-ready proofs

**Examples**:
- Financial services AI teams
- Enterprise automation groups
- Customer service AI deployments

**Entry point**: Pilot project with audit requirements

---

### ICP 3: Regulated Industries

**Who**:
- Healthcare AI deployments
- Financial services automation
- Legal tech AI applications
- Government/public sector AI

**Pain points**:
- Regulatory requirements for AI accountability
- Need to prove what AI did
- Data privacy concerns
- Cross-organization trust issues

**Talos value**:
- Blockchain-anchored proofs (immutable)
- Privacy-preserving audit (hash-only)
- Cross-org verification without shared infrastructure
- Compliance documentation

**Examples**:
- HIPAA-compliant AI systems
- SOC 2 certified AI workflows
- GDPR-compliant agent deployments

**Entry point**: Compliance requirement, audit mandate

---

### ICP 4: AI Tool and Service Providers

**Who**:
- MCP tool developers
- AI API providers
- Agent marketplace operators

**Pain points**:
- Don't know who's calling their tools
- Can't control access granularly
- Can't prove usage for billing/disputes
- No standard for secure integration

**Talos value**:
- Verified caller identity
- Capability-based access control
- Provable usage records
- Standard integration pattern

**Examples**:
- Database tool providers
- API gateway operators
- Code execution sandboxes

**Entry point**: Integration guide, capability SDK

---

## Secondary ICPs

### ICP 5: Cross-Organization AI Collaborations

**Who**:
- Partner companies sharing AI agents
- Supply chain AI integrations
- Multi-vendor agent systems

**Pain points**:
- Don't trust partner's infrastructure
- Need neutral verification
- Disputes about what happened

**Talos value**:
- Blockchain as neutral arbiter
- Independent proof verification
- No shared infrastructure required

---

### ICP 6: Open Source AI Communities

**Who**:
- Local LLM enthusiasts (Ollama users)
- Privacy-focused AI developers
- Decentralization advocates

**Pain points**:
- Cloud-based solutions not acceptable
- Want self-hosted everything
- Need privacy without giving up auditability

**Talos value**:
- Works fully offline
- Local-first architecture
- No SaaS dependency
- Open source protocol

---

## ICP Summary Matrix

| ICP | Primary Need | Entry Point | Deal Size |
|-----|--------------|-------------|-----------|
| Agent Frameworks | Identity + Encryption | SDK install | Open source |
| Enterprise AI | Audit + Compliance | Pilot project | $$$ |
| Regulated Industries | Proofs + Compliance | Mandate | $$$$ |
| Tool Providers | Access Control | Integration | $$ |
| Cross-Org | Neutral Trust | Partnership | $$$ |
| Open Source | Privacy + Local | Community | Free |

---

## Qualification Criteria

**Strong fit if**:
- ✅ Building multi-agent systems
- ✅ Need audit trails for AI actions
- ✅ Cross-boundary trust requirements
- ✅ MCP tool invocation use case
- ✅ Compliance/regulatory pressure

**Weak fit if**:
- ❌ Single-agent, single-user system
- ❌ No audit requirements
- ❌ Trust is not a concern
- ❌ Throughput > 10K msg/sec needed (use message queues)

---

**See also**: [Why Talos Wins](business-why-talos-wins) | [Use Cases](features-integrations-mcp-cookbook) | [GTM Plan](business-gtm-plan)
