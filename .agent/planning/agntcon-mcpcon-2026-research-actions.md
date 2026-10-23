# AGNTCon + MCPCon 2026 — Talos Research and Next Actions

Status: research backlog; **not** verified implementations or approved architecture. Source: https://events.linuxfoundation.org/agntcon-mcpcon-north-america/program/schedule/ (October 22–23, 2026). These notes summarize published session descriptions, not full slide contents. Validate open-source projects, specifications, security assumptions, and licensing before adopting.

## Architectural decision direction

Reuse existing DID, AGNTCY Directory, A2A Agent Cards, MCP OAuth, Sigstore/Cosign, token exchange, and policy decision infrastructure wherever appropriate. Talos should concentrate on interoperable policy, constrained delegation, trustworthy enforcement, and verifiable audit evidence. Identity verification is **not** authorization. Audit attribution is **not** proof of a real-world person's participation without separately verified user identity and authorization evidence.

## P0 — Research and prototype

1. **Human → agent → tool identity lineage / intersection authorization.** Source: “Poster: A Zero-Trust Identity Model for Production Agents.” Investigate OAuth subject vs actor, agent identity, user identity, effective permission intersection, immutable lineage, cross-framework identity. Deliver: contract schema + test vectors for subject, actor, delegator, tool, audience, and permission intersection. Never silently substitute agent identity for user identity.
2. **Recursive delegation and attenuation.** Source: “When Agents Spawn Agents: Securing Recursive Delegation in Multi-Agent Systems.” Investigate proposed RDCP, signed spawn intent, grant-before-token issuance, OAuth Token Exchange/RAR, DPoP/mTLS, AuthZEN, gateway checks, subtree revocation, and receipts. Deliver: A→B→C threat model and deny tests for privilege escalation, forged lineage, replay, confused deputy, expired or revoked child grants.
3. **Hosted MCP server runtime enforcement.** Source: “Authorization After OAuth: Controlling Tools on Hosted MCP Servers You Don’t Own.” Investigate Pomerium's identity-aware bridge pattern and compatibility with Talos. Prototype allowing GitHub PR creation while blocking merge at the proxy, without changes to hosted server; audit tool name, identity, arguments (with data minimization). Prove requests cannot bypass gateway within declared trust boundary.
4. **User-scoped token brokering.** Source: “Stop Running Agents as Service Accounts: User-Scoped Access for Enterprise Tool Calls.” Investigate Keycloak as broker, issuer trust, token audience restrictions, per-agent tool/scope catalog, centralized OAuth. Deliver: token exchange sequence diagram and per-user audit evidence; never expose broad downstream credentials to agents.
5. **MCP tool rug-pull defense.** Source: “MCP Rug Pulls in the Wild: Live Attacks and How to Stop Them.” Investigate cryptographic tool identity, approved definition hashes, drift alerts, and runtime monitoring. Deliver: tests for post-approval tool definition mutation and malicious replacement.
6. **Tamper-evident action evidence.** Source: “Prove What Your Agent Did: Tamper-Evident Audit Trails for Tool Calls.” Locate and assess claimed MIT TypeScript implementation using SHA-256 hash chaining and session Merkle roots. Deliver: library due diligence (maintenance, licensing, threat model) and tampering-detection tests. Clarify that tamper evidence alone does not prove source events truthful.
7. **Capability-first sandboxing.** Source: “Your Agent Sandbox Is Built Backwards.” Explore zero initial authority, narrowly minted capabilities, one-use grants, monotonic attenuation, and enforcement by trusted runtime or gateway. Deliver: capability lifecycle specification and deny-by-default test suite.
8. **A2A discovery and delegation integration.** Source: “Workshop: Hands-on A2A: Service Discovery and Multi-Agent Delegation.” Reuse Agent Cards and standards-compliant discovery; assess existing AGNTCY Directory and DID identity claims. Deliver: adapter spike with separate verification, trust decision, and authorization decision.

## P1 — Adjacent sessions worth investigating

9. “Evolution, not Revolution: How MCP is Reshaping OAuth” — CIMD, RFC 9728 resource metadata, enterprise-managed authorization, auth-server separation.
10. “From DCR to CIMD: MCP Client Identity in Production” — redirect trust, SSRF, metadata cache, key rotation, revocation, tenant isolation, human→agent→tool→API attribution.
11. “Demo Theater: DO NOT Give AI Agents Credentials!” — egress credential injection and brokering.
12. “Securing Multi-Server MCP Access at Scale” — multi-tenant MCP multiplexing, legacy API exposure, governance.
13. “Agent Router” — compare tool visibility policy, model routing, and budget controls against Talos; avoid duplicating router functionality.
14. “Agent Governance Lives in the OS” — compare gateway controls with OS-level enforcement for local shell/filesystem actions.
15. “The Other Half of MCP Apps” / “What Your MCP Server Does When Nobody's Looking” — revisit when slide details or code are accessible.

## Recommended execution sequence

- **Next 1:** Build a standards/OSS reuse matrix: capability, existing solution, API/library, maturity, license, Talos adapter, gaps. Check AGNTCY's current authorization scope; do not assume it is identity-only.
- **Next 2:** Write canonical authorization contracts in talos-contracts: authenticated actor, human subject, delegation chain, resource/tool/action, context, policy version, allow/deny, expiry, revocation, evidence ID.
- **Next 3:** Build a minimal MCP policy-enforcement proof-of-concept with a protected allow/deny operation; demonstrate bypass controls.
- **Next 4:** Build A→B→C least-privilege delegation and revocation tests; require a human/root principal and signed evidence where applicable.
- **Next 5:** Evaluate existing signed audit/receipt libraries and produce a tamper-evidence prototype.
- **Next 6:** Integrate A2A/AGNTCY identity and discovery as adapters, not new identity protocols.

## Acceptance / anti-drift rules

- Preserve talos-contracts as source of truth; no cross-repo deep imports.
- Explicit deny-by-default; identity verification never grants access by itself.
- Verify audience, expiry, scope, actor/subject binding, replay protection, and revocation where relevant.
- Never issue child permissions broader than parent's effective permissions.
- Every enforced tool call emits privacy-aware audit evidence with provenance and policy decision.
- Test both compliant and adversarial clients; do not rely solely on SDK hooks for enforcement.
- Keep claims labeled as session description, confirmed OSS capability, or Talos design hypothesis.
