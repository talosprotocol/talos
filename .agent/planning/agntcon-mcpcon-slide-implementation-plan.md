# AGNTCon + MCPCon 2026: Slide-Based Talos Action Plan

Status: proposed research and implementation, not shipped features. Based on attendee slides covering AGNTCY identity, Agent Router, and Cassie Shum/Praxa. Complements agntcon-mcpcon-2026-research-actions.md.

## Architecture principle
Reuse existing DID:web, DID documents, JWKS, Ed25519, AGNTCY Directory, Agent Cards, A2A, MCP, Cosign, OAuth/token exchange, gateway/router, OpenTelemetry and CI/CD systems. Talos owns policy, constrained delegation, authorization enforcement, revocation and security audit correlation. Discovery and cryptographic identity are not authorization. Agent-reported retrospectives are not independently verified execution proof.

## P0: investigate
1. AGNTCY directory record/CID, publisher Cosign signature, agent DID identity claim, DID document key binding, rotation/revocation, trust anchors and replay defense. Treat publisher and agent attestations separately; static signed claims do not imply live runtime authentication.
2. Persistent agent identity vs per-run credentials: SPIFFE/SPIRE, OAuth token exchange, proof-of-possession, short-lived scope/audience, human initiator, tenant and delegation chain.
3. Existing MCP gateway/router: MCPRoute toolSelector, JWT scopes/claims, CEL, upstream credentials, Envoy ext_proc/Wasm, local and hosted options. Test enforcement against direct tool invocation, not merely filtered discovery.
4. Secure context propagation: task spec/standards/decisions vs verified authorization context; privacy, freshness, provenance and MCP/A2A compatibility.
5. Evidence and verification: agent retrospective vs telemetry vs independently verified authorization and tool outcome; signed receipts and tamper evidence.
6. Autonomous safeguards: stop/revoke, runtime termination, tool/time/cost budgets, risk-based human approvals and execution limits.
7. Security visibility and value metrics: policy violations, audit coverage, revocation effectiveness, security-related rework, post-deployment signals.

## P0: implement after validation
- Define contract-first schemas in talos-contracts for agent DID, publisher signature, identity claim, run ID, initiator, tenant, delegation, scope, audience, policy version, decision, enforcement point, evidence references, timestamps and verification status.
- Build AGNTCY adapter verifying publisher and agent attestations separately; never infer authorization from discovery.
- Bind short-lived run credentials to authenticated agent, originating authority and least-privilege scope.
- Enforce tool-list filtering AND per-call gateway authorization; test permitted read, denied write, direct-call bypass, revoked/expired grants and privilege escalation.
- Correlate identity, delegation, policy decision, protected tool call, external response and evidence source; redact sensitive inputs.
- Enforce revocation for subsequent protected calls; use runtime integration for actual process termination.

## P1: implement
- Task-specific MCP tool catalogs; measure token/context savings (speaker anecdote: 30 tools available, four needed, roughly 17k input tokens saved per turn; independently validate).
- Context graph adapter: before each run read spec, acceptance criteria, standards and decisions; afterward attach review status, tests, evidence and learnings.
- Human-approved task spec binding to execution authority, with risk-based approval gates.
- Verification sensors and receipts from trusted test, CI/CD, PR, deployment and telemetry sources; mark unverifiable claims distinctly.
- Capture agent retrospective separately from verified events, plus run duration, model tokens, cost and execution caps.
- Security dashboard showing agent/run inventory, delegated authority, policy decisions, revocation, missing audit evidence and policy drift.

## Reuse patterns from the slides
- AGNTCY: directory record -> publisher Cosign signature -> DID:web / Ed25519 document -> signed agent identity claim -> trust evaluation -> separate Talos policy decision.
- Agent Router: logical model routing across providers with weights/failover and retry policy; MCPRoute tool selection, JWT/CEL authorization and upstream auth. Talos should integrate as PDP/authorization layer, not duplicate model routing.
- Praxa: shared context graph (standards, intent, decisions, dependencies, provenance, history) -> task/spec -> per-run credentials -> execution -> PR/release -> machine-generated evidence and telemetry -> next run.
- Relevant Praxa MCP tools: get_task, finalize_task, create_comment, submit_for_review, event_stream. Every skill needs a sensor; every run should leave an attributable record.

## Acceptance tests
1. Verified DID or publisher signature alone never grants tool access.
2. Delegated permissions cannot exceed parent effective authority; expired, replayed and revoked grants fail closed.
3. Direct invocation of a hidden or disallowed tool is blocked by enforcement.
4. Every protected operation correlates to run, authenticated identity, delegation, policy version and enforcement outcome.
5. Receipts distinguish agent self-report, platform observation and independently verified evidence.
6. Revocation prevents subsequent protected calls; process kill requires tested runtime integration.

## Next actions
1. Build standards/OSS reuse matrix and validate maturity, API contracts, license and threat assumptions.
2. Prototype AGNTCY DID + separate publisher signature verification.
3. Prototype MCP gateway enforcement with allow/deny and bypass tests.
4. Add per-run delegation, revocation and audit-correlation vectors.
5. Integrate verified receipt and task-specific tool filtering; measure overhead.

Anti-drift: contracts-first; published boundaries only; deterministic test vectors; strict schemas and UUIDv7; deny-by-default; audit everywhere; CI gates.