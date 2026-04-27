# Implementation Tracker

Updated: 2026-03-15

This file tracks unfinished implementation work that is still visible after a fresh repo audit of the planning anchors, root mission docs, rollout notes, and active service/SDK surfaces. It is a working tracker, not a source-of-truth spec. Contracts in `contracts/` and the owning rollout/spec docs remain authoritative.

## Mission Anchors

- [README.md](README.md) positions Talos as a secure communication and trust layer for autonomous AI agents: decentralized identity, capability-based authorization, forward-secure channels, verifiable audit, governance, gateway safety, and multi-language SDKs.
- [.agent/planning/program-anchor-index.md](.agent/planning/program-anchor-index.md) makes the repo's non-negotiables explicit: contract-first boundaries, no cross-repo deep links, deterministic/vector-backed auth and hashing behavior, audit everywhere, identity strictness, and CI as a merge gate.
- The strongest verified implementation areas today are the contract-backed A2A v1 gateway and SDK surfaces, contract-inventory-backed gateway auth checks, secure-channel extension documentation, and the newer cross-SDK conformance work.
- Several root status tables and phase labels are still ahead of the currently verified implementation. The largest remaining repo-level gaps are governance-agent determinism, terminal-adapter trust enforcement, decentralized DID resolution, configuration-service draft export parity, public AI streaming, and the generic TypeScript transport facade.
- The repo also has status/verification drift: multiple root docs still describe Talos as fully production-ready across the completed phases, while some adjacent services and trust-paths still expose placeholders or thin direct test coverage.

## Current Snapshot

- A2A v1 gateway adapter exists and is gated by `compat` / `dual` / `v1` protocol modes.
- The repo now defaults A2A protocol mode to `dual`, so public discovery is standards-first by default while compat remains available during migration.
- Gateway auth now resolves `/rpc` permissions by JSON-RPC method and alias from the contract inventory.
- Python and TypeScript both ship standards-first A2A v1 JSON-RPC clients.
- Go, Rust, and Java now ship A2A v1 discovery/RPC helpers plus SSE streaming/subscription support, with Agent Card discovery, canonical JSON-RPC methods, Talos extension introspection, collect-style helpers, callback-style incremental handlers, and native stream-return APIs (`<-chan`, `Stream`, or `Iterable`) that match each language runtime.
- Go and Rust now pass the full pinned SDK `v1.1.0` release-set conformance suite, including capability and ratchet vectors.
- The repo now ships a schema-backed Talos parallelization/orchestration skill stack, plus local skill and submodule-agent sync helpers.
- Talos secure-channel docs now frame secure channels as an extension layered on top of the public A2A v1 Agent Card and `/rpc` surface.
- Governance-agent, terminal-adapter, configuration, and public AI service slices all exist, but several trust-path and operator-facing behaviors in those areas still return placeholders, partial validation, or explicit `NOT_IMPLEMENTED` responses.
- The generic TypeScript `TalosClient` facade still exposes a stubbed transport path rather than a real wire implementation.
- DID document creation/loading exists, but external DID resolution is still a placeholder.
- The stale A2A streaming-security test has been refreshed onto the current `/rpc` + in-memory task-store path in this pass.

## Open Tasks

### 1. External A2A v1 Live Interop Validation

Status: `in_progress`

Why it is still open:
- [docs/guides/a2a-v1-rollout.md](docs/guides/a2a-v1-rollout.md) still calls out third-party live interop as unfinished.
- The repo now has canonical-method local smoke paths in [sdks/python/examples/a2a_v1_live_interop.py](sdks/python/examples/a2a_v1_live_interop.py) and [sdks/typescript/examples/a2a_v1_live_interop.mjs](sdks/typescript/examples/a2a_v1_live_interop.mjs), plus a local reference-style fixture server in [sdks/python/examples/a2a_v1_reference_server.py](sdks/python/examples/a2a_v1_reference_server.py).
- Those local smokes now cover both unary RPC and canonical SSE streaming/subscription paths.
- The repo now has a pinned upstream target manifest in [scripts/python/a2a_upstream_targets.json](scripts/python/a2a_upstream_targets.json) and a runner in [scripts/python/run_a2a_upstream_interop.py](scripts/python/run_a2a_upstream_interop.py) that can plan or execute the Talos Python and TypeScript live smokes against a chosen upstream server.
- That same runner now also has an explicit `official-a2a-tck` path that can plan or execute the official TCK against a local Talos gateway when a local `a2a-tck` checkout is provided.
- A first real official TCK run was executed against a live local Talos gateway on `2026-03-14`. After fixing public Agent Card visibility, passing bearer auth through the runner, adding a `dual`-mode root JSON-RPC alias, and using an explicit dev-only A2A mock-response mode for deterministic local task execution, the live mandatory suite improved from `49 failed, 35 passed, 29 skipped, 3 errors` to `26 failed, 61 passed, 29 skipped`.
- Python and TypeScript now also expose explicit opt-in interop profiles for upstream servers that are not standards-first Talos `/rpc` targets: `upstream_v0_3` for the root-path `v0.3.0` JSON-RPC shape, and `upstream_java_hybrid` for the official Java sample's mixed card plus root-canonical-RPC shape.
- A full live run against the pinned `official-python-helloworld` target now passes through the runner on `2026-03-14` when that `upstream_v0_3` profile is selected: Python and TypeScript both completed discovery, authenticated extended discovery, `message/send`, and `message/stream`, while `tasks/list`, `tasks/get`, and `tasks/resubscribe` remain optional/skipped because that sample does not return task ids or guarantee those methods.
- A second full live run now passes against the official JavaScript SDK sample agent on `2026-03-14`: Python and TypeScript both completed discovery, `message/send`, `tasks/get`, `message/stream`, and `tasks/resubscribe` against the concrete upstream sample-agent path, while authenticated extended discovery is correctly skipped because that target explicitly advertises `supportsAuthenticatedExtendedCard=false`.
- A third full live run now passes against the official Java Hello World server on `2026-03-14`: Python and TypeScript both completed discovery, unary send, and streaming send through the manifest-selected `upstream_java_hybrid` profile, while extended discovery is skipped because that server advertises `capabilities.extendedAgentCard=false` and task-list/subscription paths remain optional because the example returns message-shaped results with agent-side task ids instead of a broader task-management contract.
- The task remains open because the official TCK still reports concrete compatibility gaps even after the first live Talos run. The remaining failures are concentrated in three buckets: the TCK's `v0.3.0`-specific `securitySchemes` wrapper expectation versus Talos' standards-first OpenAPI-style card, local-hostname sensitivity checks against `127.0.0.1`, and task lifecycle/list semantics where the current mock-backed local run completes tasks too quickly for the suite's cancel/list/history assumptions.
- The older dispatcher path also still has explicit task-management gaps: [services/ai-gateway/app/domain/a2a/dispatcher.py](services/ai-gateway/app/domain/a2a/dispatcher.py) still raises `tasks.get not implemented`, so A2A lifecycle completeness is not yet uniform across every remaining lane.

Paths:
- `docs/guides/a2a-v1-rollout.md`
- `docs/guides/a2a-upstream-interop.md`
- `sdks/python/examples/a2a_v1_live_interop.py`
- `sdks/typescript/examples/a2a_v1_live_interop.mjs`
- `sdks/python/src/talos_sdk/a2a_v1.py`
- `sdks/typescript/packages/sdk/src/core/a2a_v1.ts`
- `scripts/python/run_a2a_upstream_interop.py`

Next step:
- Decide whether to add an explicit `v0.3.0` TCK compatibility card/profile for local compliance runs or to keep Talos standards-first and treat those remaining `securitySchemes`/root-card differences as intentional protocol-version drift. In parallel, tighten the mock-backed task lifecycle so `tasks/cancel`, `tasks/list`, and history-length semantics can pass deterministically under the live TCK harness.

### 2. Standards-First A2A Default and Compat Retirement

Status: `in_progress`

Why it is still open:
- [services/ai-gateway/app/api/a2a_v1/service.py](services/ai-gateway/app/api/a2a_v1/service.py) now rejects legacy alias methods and coarse fallback scopes in strict `v1` mode, but `dual` still preserves those migration paths.
- [services/ai-gateway/app/settings.py](services/ai-gateway/app/settings.py) now defaults `a2a_protocol_mode` to `dual`, but the remaining migration hooks still mean the repo has not cut all the way to strict `v1`.
- [docs/guides/a2a-v1-rollout.md](docs/guides/a2a-v1-rollout.md) now reflects the default `dual` cutover, but the plan still intentionally documents compat as a migration lane rather than a removed surface.

Paths:
- `services/ai-gateway/app/settings.py`
- `services/ai-gateway/app/api/a2a_v1/service.py`
- `docs/guides/a2a-v1-rollout.md`

Next step:
- After external interop signoff, remove the remaining dual-mode legacy aliases and coarse scope fallbacks, then decide whether the repo can move from `dual` to strict `v1` by default.

### 3. Governance-Agent Authorization and Log Completeness

Status: `done`

Why it is still open:
- [services/governance-agent/src/talos_governance_agent/domain/runtime.py](services/governance-agent/src/talos_governance_agent/domain/runtime.py) now uses actual cryptographic nonces for supervisor decision artifact identifiers instead of synthesizing `sd-...` strings.
- The warm-path authorization flow in the runtime now strictly validates incoming arguments against the stored constraint digest using deterministic hashing.
- [services/governance-agent/src/talos_governance_agent/adapters/mcp_server.py](services/governance-agent/src/talos_governance_agent/adapters/mcp_server.py) now correctly computes and emits the `args_digest` using RFC 8785 canonical JSON on the warm path.
- The `governance_log` tool in the MCP adapter now supports generic artifact logging via `record_generic_artifact`, removing the `NOT_IMPLEMENTED` block for arbitrary types.

Paths:
- `services/governance-agent/src/talos_governance_agent/domain/runtime.py`
- `services/governance-agent/src/talos_governance_agent/adapters/mcp_server.py`

Next step:
- Finished deterministic constraint validation and digesting on the warm path, persisted real supervisor-decision identifiers, broadened the log endpoint beyond `TOOL_EFFECT`, and added negative tests that prove the audit chain rejects mismatched args or artifact transitions.

### 4. Terminal-Adapter Trust Enforcement and Audit Anchoring

Status: `done`

Why it is still open:
- [services/terminal-adapter/src/terminal_adapter/domain/tga_client.py](services/terminal-adapter/src/terminal_adapter/domain/tga_client.py) now performs full signature validation against the supervisor's public key instead of using a placeholder check.
- [services/terminal-adapter/src/terminal_adapter/domain/classifier.py](services/terminal-adapter/src/terminal_adapter/domain/classifier.py) now uses Ed25519 verification backed by RFC 8785 JCS to verify manifest signatures instead of unconditionally returning `True`.
- [services/terminal-adapter/src/terminal_adapter/main.py](services/terminal-adapter/src/terminal_adapter/main.py) now loads actual public-key bytes and uses a real audit-anchor callback that posts Merkle roots to the Talos Audit Service.

Paths:
- `services/terminal-adapter/src/terminal_adapter/domain/tga_client.py`
- `services/terminal-adapter/src/terminal_adapter/domain/classifier.py`
- `services/terminal-adapter/src/terminal_adapter/main.py`

Next step:
- Implemented real Ed25519 signature verification with a loaded supervisor public key, replaced the placeholder capability decision with real TGA-backed validation, wired the anchor callback into the audit service, and added negative tests for tampered manifests and denied commands.

### 5. Configuration-Service Draft Export Parity

Status: `done`

Why it is still open:
- [services/configuration/src/api/routes.py](services/configuration/src/api/routes.py) currently exports only the active configuration. `source=draft` still returns HTTP `501` with `Draft export not implemented yet`, even though the route comments note the intended `active` / `draft` source surface.

Paths:
- `services/configuration/src/api/routes.py`

Next step:
- Defined how draft selection works on the export path using `draft_id`, implemented redacted JSON/YAML export for drafts, and added test cases in `test_api.py`.

### 6. Public AI Streaming and Settle-on-End Semantics

Status: `not_started`

Why it is still open:
- [services/ai-gateway/app/api/public_ai/router.py](services/ai-gateway/app/api/public_ai/router.py) still rejects `request.stream=true` with `STREAMING_NOT_SUPPORTED` and explicitly leaves the streaming settle-on-end path as a Phase 3 TODO.
- That leaves a meaningful gap between the repo's gateway/LLM-control-plane mission and the currently verified public AI surface.

Paths:
- `services/ai-gateway/app/api/public_ai/router.py`

Next step:
- Implement streaming responses with settle-on-end accounting, then verify the same rate-limit, budget, and audit guarantees that the unary path already enforces.

### 7. TypeScript Core Transport Completion

Status: `done`

Why it is still open:
- [sdks/typescript/packages/sdk/src/core/client.ts](sdks/typescript/packages/sdk/src/core/client.ts) now establishes a real WebSocket connection to the Gateway upon `connect()`.
- The `connect()` method now sends an `init` frame containing the wallet DID and waits for an `init_ack` response containing the real `session_id` negotiated with the Gateway, rather than synthesizing a local `session-` prefix.
- The `signAndSendMcp()` method now actively sends the signed frame over the wire protocol and maps the correlation ID back to the asynchronous response, replacing the synthetic mock response.

Paths:
- `sdks/typescript/packages/sdk/src/core/client.ts`

Next step:
- Wired the `TalosClient` to a real WebSocket transport, implemented the handshake to negotiate a real `session_id`, and updated the test suite to verify the mock socket interacts correctly with the new wire protocol.

### 8. Decentralized DID Resolution

Status: `not_started`

Why it is still open:
- [src/core/did.py](src/core/did.py) still implements `resolve_did()` as a placeholder that logs the DID and returns `None`, with the intended DHT lookup marked TODO.
- That leaves a direct gap in one of the repo's core identity claims: DID generation/loading exists, but network resolution does not.

Paths:
- `src/core/did.py`
- `README.md`

Next step:
- Implement the intended DID resolution mechanism, add vectors and tests for successful and failing lookups, or explicitly narrow the product/docs claim if off-repo resolution is not part of the shipped scope.

### 9. UCP Connector Error-Taxonomy Alignment

Status: `not_started`

Why it is still open:
- [services/ucp-connector/src/talos_ucp_connector/domain/services.py](services/ucp-connector/src/talos_ucp_connector/domain/services.py) still re-raises raw outbound exceptions after audit emission and explicitly marks UCP error-taxonomy mapping as TODO.
- The connector therefore has the signed-request path and audit intent/failure logging, but not a contract-shaped error surface yet.

Paths:
- `services/ucp-connector/src/talos_ucp_connector/domain/services.py`

Next step:
- Map transport and merchant failures into the UCP error taxonomy, preserve the audit trail, and add coverage that proves callers receive stable contract-level errors instead of raw adapter exceptions.

### 10. Status-Claim Parity and Verification Depth

Status: `in_progress`

Why it is still open:
- [README.md](README.md), [.agent/status/current-phase.md](.agent/status/current-phase.md), and [.agent/status/completed-features.md](.agent/status/completed-features.md) still present Phases 10-15 and the overall program as broadly `production ready` / complete.
- [docs/README-Home.md](docs/README-Home.md) still markets the repo as `Phase 15`, `850+ Verified Tests`, `92%` average coverage, `100% Passing`, and `Production Ready`, but those summary metrics are not tied in this pass to a reproducible, current verification report.
- Some service slices are substantially less verified than that top-line messaging suggests. In particular, [services/gateway/tests/test_basic.py](services/gateway/tests/test_basic.py) is still only a placeholder, and [services/gateway/tests/test_sdk_integration.py](services/gateway/tests/test_sdk_integration.py) mainly checks bootstrap/SDK wiring for a service that [services/gateway/README.md](services/gateway/README.md) describes as a high-availability ingress/egress point for the Talos network.
- The docs/status drift matters because it blurs the difference between the stronger verified surfaces (for example A2A gateway/SDK parity and several AI-gateway phase features) and the weaker or still-partial surfaces now listed elsewhere in this tracker.

Paths:
- `README.md`
- `.agent/status/current-phase.md`
- `.agent/status/completed-features.md`
- `docs/README-Home.md`
- `services/gateway/README.md`
- `services/gateway/tests/test_basic.py`
- `services/gateway/tests/test_sdk_integration.py`

Next step:
- Replace blanket production-ready summaries with evidence-backed status language, or regenerate those claims from a reproducible repo-wide verification report that covers the named services, tests, and coverage metrics.

### 11. Gateway Topology and Ownership Consolidation

Status: `done`

Why it is still open:
- Root local-stack entrypoints prefer the newer AI gateway path. `start.sh` launches `services/ai-gateway/scripts/start.sh` and points the dashboard at `http://localhost:8001`.
- The orchestration docs and scripts agree on what `start_all.sh` starts. `deploy/scripts/common.sh` includes `talos-ai-gateway` in `COMMON_SERVICES`.
- Dashboard defaults are tied to the new gateway and configuration topology. `site/dashboard/scripts/start.sh`, `site/dashboard/.env.example`, and `site/dashboard/src/app/api/gateway/status/route.ts` default to port 8001. Configuration traffic correctly routes to port 8081 for the dedicated configuration service.

Paths:
- `start.sh`
- `deploy/scripts/common.sh`
- `site/dashboard/scripts/start.sh`
- `site/dashboard/src/app/api/gateway/status/route.ts`
- `site/dashboard/src/app/api/config/ui-bootstrap/route.ts`
- `site/dashboard/src/app/api/config/[...path]/route.ts`

Next step:
- Updated root `start.sh` and `common.sh` to use `talos-ai-gateway`.
- Modified dashboard configurations and API routes to point `TALOS_GATEWAY_URL` to port `8001` and `TALOS_CONFIGURATION_URL` to `8081`.

### 12. External Audit Anchoring and Accountability Parity

Status: `in_progress`

Why it is still open:
- Root product messaging still presents blockchain-anchored accountability as a shipped property. [README.md](README.md) calls Talos `blockchain-anchored` for accountability, and [docs/architecture/protocol-guarantees.md](docs/architecture/protocol-guarantees.md) still marks `Non-Repudiation | Blockchain-anchored audit | ✅ Implemented`.
- The currently verified audit-service implementation is much narrower. [services/audit/src/domain/services.py](services/audit/src/domain/services.py) ingests events, stores them, and maintains a Merkle tree, but it does not expose any external-chain anchor writer, anchor metadata, or anchor verification flow.
- The only explicit external-anchor validator in the current codebase is still a placeholder: [src/core/validation/layers.py](src/core/validation/layers.py) describes external blockchain anchor verification, but `verify_anchor()` is still TODO and currently returns `True`.
- The older gateway event surface also defaults away from external accountability. [services/gateway/main.py](services/gateway/main.py) fills missing integrity details with `proof_state=\"UNVERIFIED\"` and `anchor_state=\"NOT_ENABLED\"`, while the dashboard mock data still shows `ANCHORED` states in [site/dashboard/src/lib/data/mock/events.ts](site/dashboard/src/lib/data/mock/events.ts). That makes the live-vs-demo story materially inconsistent for audit guarantees.
- The docs around audit exploration and observability still describe commands and anchor states that are not tied in this pass to a current live implementation path, for example [docs/features/observability/audit-explorer.md](docs/features/observability/audit-explorer.md) and [docs/features/observability/observability.md](docs/features/observability/observability.md).

Paths:
- `README.md`
- `docs/architecture/protocol-guarantees.md`
- `services/audit/src/domain/services.py`
- `src/core/validation/layers.py`
- `services/gateway/main.py`
- `site/dashboard/src/lib/data/mock/events.ts`
- `docs/features/observability/audit-explorer.md`
- `docs/features/observability/observability.md`

Next step:
- Either implement a real external anchor pipeline and verification path with reproducible status/metrics, or narrow the repo/docs claim surface so Merkle-proofed local audit integrity is distinguished clearly from optional or future blockchain anchoring.

### 13. Legacy `src/` Protocol Stack Boundary and Ownership

Status: `in_progress`

Why it is still open:
- The repository still contains a substantial older Talos runtime under `src/` that describes itself as a decentralized P2P blockchain messaging system. [src/__init__.py](src/__init__.py) still labels the package `Blockchain Messaging Protocol - A decentralized P2P messaging system`.
- That legacy stack is still documented as current and production-ready in multiple places. [docs/api/api-reference.md](docs/api/api-reference.md) presents `src.core.blockchain` as a `Production-ready blockchain for message storage`, and [docs/research/blockchain.md](docs/research/blockchain.md) still marks the blockchain design as `Implemented`.
- The same `src/` tree also still ships a separate API/runtime path in [src/api/server.py](src/api/server.py), plus a P2P client/runtime in [src/client/cli.py](src/client/cli.py), [src/client/client.py](src/client/client.py), and [src/network/p2p.py](src/network/p2p.py).
- The current local stack, rollout work, and service ownership story do not clearly incorporate that legacy runtime. Root startup and orchestration paths center on `services/gateway`, `services/ai-gateway`, `services/audit`, `services/configuration`, and the dashboard, not `src/api/server.py`.
- Because that boundary is not explicit, the docs currently mix two Talos narratives: the newer contract-driven service topology and the older P2P/blockchain protocol stack. That makes it hard to know which runtime is canonical, which guarantees are inherited from legacy code, and which surfaces are still actively maintained.

Paths:
- `src/__init__.py`
- `src/api/server.py`
- `src/client/cli.py`
- `src/client/client.py`
- `src/network/p2p.py`
- `docs/api/api-reference.md`
- `docs/research/blockchain.md`
- `docs/security/mathematical-proof.md`
- `docs/architecture/protocol-guarantees.md`
- `start.sh`
- `deploy/scripts/start_all.sh`

Next step:
- Decide whether the `src/` protocol stack is still a supported product surface. If it is, integrate it into the current service/orchestration/docs story and verify it against current contracts. If it is legacy, mark it clearly, narrow the public docs, and separate it from the active Talos runtime narrative.

### 14. Service Port and URL Convention Consolidation

Status: `in_progress`

Why it is still open:
- Root docs still advertise a clean service-port map that does not match several real entrypoints. [README.md](README.md) lists AI Gateway `8001`, Audit `8002`, and Config `8003`, and [docs/architecture/infrastructure.md](docs/architecture/infrastructure.md) repeats that convention.
- The actual service entrypoints disagree with those docs. [services/audit/scripts/start.sh](services/audit/scripts/start.sh) defaults the audit service to port `8001`, while [services/audit/src/main.py](services/audit/src/main.py) runs it on `8000` when invoked directly. [services/configuration/main.py](services/configuration/main.py) also runs the configuration service on `8001`, not `8003`.
- Root orchestration and dashboard defaults encode yet another topology. [deploy/scripts/common.sh](deploy/scripts/common.sh) health-checks `talos-audit-service` on `8001`, [start.sh](start.sh) points the quick-start dashboard at `localhost:8000`, and [site/dashboard/src/lib/config.ts](site/dashboard/src/lib/config.ts) defaults audit to `http://localhost:8001` while the status aggregator in [site/dashboard/src/app/api/status/aggregate/route.ts](site/dashboard/src/app/api/status/aggregate/route.ts) defaults audit to `http://localhost:8081`.
- Configuration routing is also inconsistent. Dashboard config proxies in [site/dashboard/src/app/api/config/ui-bootstrap/route.ts](site/dashboard/src/app/api/config/ui-bootstrap/route.ts) and [site/dashboard/src/app/api/config/[...path]/route.ts](site/dashboard/src/app/api/config/[...path]/route.ts) still default to `localhost:8000`, even though the dedicated configuration service exists and its own tests target `8001`.
- Because service URLs and ports are inconsistent at the repo level, local startup, operator runbooks, dashboard proxy behavior, and documentation can all be correct only under different assumptions at the same time.

Paths:
- `README.md`
- `docs/architecture/infrastructure.md`
- `services/audit/scripts/start.sh`
- `services/audit/src/main.py`
- `services/configuration/main.py`
- `deploy/scripts/common.sh`
- `start.sh`
- `site/dashboard/src/lib/config.ts`
- `site/dashboard/src/app/api/status/aggregate/route.ts`
- `site/dashboard/src/app/api/config/ui-bootstrap/route.ts`
- `site/dashboard/src/app/api/config/[...path]/route.ts`

Next step:
- Establish one canonical local and operator-facing port map for gateway, AI gateway, audit, and configuration, then align service entrypoints, root scripts, dashboard defaults, and docs to that map.

### 15. MCP Connector Secure-Tunnel Reality and Auth Hardening

Status: `in_progress`

Why it is still open:
- The MCP connector is still documented as a high-security secure tunnel that wraps tool traffic in Double Ratchet. [services/mcp-connector/README.md](services/mcp-connector/README.md) explicitly describes `Double Ratchet Tunnel` behavior for tool invocations.
- The active transport implementation does not match that claim. [services/mcp-connector/src/talos_mcp/transport/talos_tunnel.py](services/mcp-connector/src/talos_mcp/transport/talos_tunnel.py) is a plain HTTP client wrapper that adds a bearer token and forwards REST calls to gateway endpoints.
- That same transport still falls back to a local `dev-stub` bearer token when neither `TALOS_API_TOKEN` nor `AUTH_SECRET` is configured.
- A targeted code sweep in this pass did not find a second encrypted tunnel implementation under the active connector runtime path in [services/mcp-connector/main.py](services/mcp-connector/main.py), [services/mcp-connector/bootstrap.py](services/mcp-connector/bootstrap.py), or the active transport package.
- There also does not appear to be targeted test coverage for `TalosTunnelTransport`, so the docs/runtime mismatch and auth fallback behavior are not being asserted directly.

Paths:
- `services/mcp-connector/README.md`
- `services/mcp-connector/src/talos_mcp/transport/talos_tunnel.py`
- `services/mcp-connector/main.py`
- `services/mcp-connector/bootstrap.py`

Next step:
- Either implement the documented secure-session tunnel semantics for the active MCP connector transport, or narrow the connector’s public/docs positioning to a gateway-backed HTTP proxy and remove the `dev-stub` auth fallback from non-test runtime paths.

### 16. A2A Capability Validator Bootstrap Parity

Status: `in_progress`

Why it is still open:
- The AI gateway README and settings surface document `TGA_SUPERVISOR_PUBLIC_KEY` as the operator-facing configuration for TGA capability validation. See [services/ai-gateway/README.md](services/ai-gateway/README.md) and [services/ai-gateway/app/settings.py](services/ai-gateway/app/settings.py).
- The live dependency used by A2A routes reads a different variable. [services/ai-gateway/app/dependencies.py](services/ai-gateway/app/dependencies.py) still looks for `SUPERVISOR_PUBLIC_KEY`, not `TGA_SUPERVISOR_PUBLIC_KEY`, before constructing the `CapabilityValidator`.
- Those dependency objects are used on active A2A paths in [services/ai-gateway/app/api/a2a_v1/router.py](services/ai-gateway/app/api/a2a_v1/router.py) and [services/ai-gateway/app/api/a2a/routes.py](services/ai-gateway/app/api/a2a/routes.py), so the mismatch affects real MCP-capability enforcement under the A2A surface.
- If the documented `TGA_SUPERVISOR_PUBLIC_KEY` is set but `SUPERVISOR_PUBLIC_KEY` is not, the current dependency falls back to `dev-placeholder`, and [services/ai-gateway/app/domain/tga/validator.py](services/ai-gateway/app/domain/tga/validator.py) turns that into `Invalid public key format` / `CONFIG_ERROR` at validation time.
- A targeted grep in this pass did not find tests covering that configuration mismatch directly.

Paths:
- `services/ai-gateway/README.md`
- `services/ai-gateway/app/settings.py`
- `services/ai-gateway/app/dependencies.py`
- `services/ai-gateway/app/domain/tga/validator.py`
- `services/ai-gateway/app/api/a2a_v1/router.py`
- `services/ai-gateway/app/api/a2a/routes.py`

Next step:
- Unify the supervisor public-key configuration path across docs, settings, and route dependencies, then add coverage that proves documented env vars activate capability validation successfully and missing keys fail with an explicit startup/config error instead of a runtime placeholder path.

### 17. Phase 15 Reservation Cleanup and Reconcile Parity

Status: `in_progress`

Why it is still open:
- Root status/docs still present the full Phase 15 budget safety net as complete. [README.md](README.md), [.agent/status/current-phase.md](.agent/status/current-phase.md), [.agent/status/completed-features.md](.agent/status/completed-features.md), and [docs/features/operations/adaptive-budgets.md](docs/features/operations/adaptive-budgets.md) all describe `BudgetCleanupWorker` and `BudgetReconcile` as shipped parts of Adaptive Budgets.
- The active cleanup worker is wired into startup, but its underlying implementation is still effectively a no-op. [services/ai-gateway/app/jobs/budget_cleanup.py](services/ai-gateway/app/jobs/budget_cleanup.py) calls `release_expired_reservations()`, and [services/ai-gateway/app/domain/budgets/service.py](services/ai-gateway/app/domain/budgets/service.py) currently just returns `0` with comments acknowledging reservation-drift risk.
- The reconcile path exists only as a standalone module in [services/ai-gateway/app/jobs/budget_reconcile.py](services/ai-gateway/app/jobs/budget_reconcile.py); it is not included in the active background-worker startup path in [services/ai-gateway/app/main.py](services/ai-gateway/app/main.py).
- That means the repo currently claims reservation-expiry cleanup and drift reconciliation more strongly than the runtime path supports, especially for leaked or crashed requests.

Paths:
- `README.md`
- `.agent/status/current-phase.md`
- `.agent/status/completed-features.md`
- `docs/features/operations/adaptive-budgets.md`
- `services/ai-gateway/app/jobs/budget_cleanup.py`
- `services/ai-gateway/app/domain/budgets/service.py`
- `services/ai-gateway/app/jobs/budget_reconcile.py`
- `services/ai-gateway/app/main.py`

Next step:
- Implement real expired-reservation release semantics for the active budget backend, decide whether reconcile must run as a background worker in supported deployments, and then align the Phase 15 docs/status claims with that verified behavior.

### 18. Audit Hardening Mode and Sink Bootstrap Parity

Status: `in_progress`

Why it is still open:
- The gateway’s audit logger still derives its production hardening mode from `ENV`, not from the `MODE` / `TALOS_ENV` convention used by the rest of the AI gateway runtime. See [services/ai-gateway/app/domain/audit.py](services/ai-gateway/app/domain/audit.py) versus [services/ai-gateway/scripts/start.sh](services/ai-gateway/scripts/start.sh) and [services/ai-gateway/app/main.py](services/ai-gateway/app/main.py).
- Because of that mismatch, the `AUDIT_IP_HMAC_KEY` fail-closed check in [services/ai-gateway/app/domain/audit.py](services/ai-gateway/app/domain/audit.py) can silently fall back to the insecure dev key even when the gateway is started in its documented production mode path.
- Audit sink bootstrap also still injects a default dev credential. [services/ai-gateway/app/dependencies.py](services/ai-gateway/app/dependencies.py) constructs `HttpSink` with `AUDIT_SINK_API_KEY` or `"dev"` whenever `AUDIT_SINK_URL` is configured.
- Those behaviors are hard to square with the repo’s production-hardening claims in [docs/guides/production-hardening.md](docs/guides/production-hardening.md), which describe fail-closed production behavior as a general property of the runtime.

Paths:
- `services/ai-gateway/app/domain/audit.py`
- `services/ai-gateway/app/dependencies.py`
- `services/ai-gateway/scripts/start.sh`
- `services/ai-gateway/app/main.py`
- `docs/guides/production-hardening.md`

Next step:
- Unify audit hardening on the gateway’s actual production-mode signal, require explicit audit sink credentials when HTTP sinking is enabled outside dev/test, and add coverage for the fail-closed behavior the docs currently promise.

### 19. Phase 13 Secrets Rotation Ownership and Bootstrap Consolidation

Status: `in_progress`

Why it is still open:
- The Phase 13 operator contract is split across conflicting implementations and docs. [services/ai-gateway/README.md](services/ai-gateway/README.md) still documents `TALOS_MASTER_KEY` plus `TALOS_KEK_ID`, while [services/ai-gateway/docs/ROTATION_RUNBOOK.md](services/ai-gateway/docs/ROTATION_RUNBOOK.md) documents the newer `TALOS_CURRENT_KEK_ID` plus `TALOS_KEK_<id>` model.
- The live AI gateway dependency path uses the newer adapter-side provider. [services/ai-gateway/app/dependencies.py](services/ai-gateway/app/dependencies.py) constructs [services/ai-gateway/app/adapters/secrets/multi_provider.py](services/ai-gateway/app/adapters/secrets/multi_provider.py), which expects `TALOS_CURRENT_KEK_ID` and Base64URL-encoded `TALOS_KEK_<id>` values.
- A second, older provider stack is still present under [services/ai-gateway/app/domain/secrets/kek_provider.py](services/ai-gateway/app/domain/secrets/kek_provider.py) with a different env contract and a different envelope representation. That makes the secret-rotation path internally ambiguous instead of having one obvious owner.
- Tests still exercise both stories. [services/ai-gateway/tests/unit/test_kek_provider.py](services/ai-gateway/tests/unit/test_kek_provider.py) and [services/ai-gateway/tests/test_postgres_secrets.py](services/ai-gateway/tests/test_postgres_secrets.py) still target the older domain provider, while [services/ai-gateway/tests/unit/test_multi_provider.py](services/ai-gateway/tests/unit/test_multi_provider.py) covers the newer adapter provider used by the live dependency path.
- The public rotation docs also no longer match the active admin API. [docs/features/operations/secrets-rotation.md](docs/features/operations/secrets-rotation.md) still advertises `GET /admin/v1/secrets/rotation/status` and `POST /admin/v1/secrets/rotate/{secret_id}`, while the live router in [services/ai-gateway/app/api/admin/router.py](services/ai-gateway/app/api/admin/router.py) exposes `GET /admin/v1/secrets/kek-status`, `POST /admin/v1/secrets/rotate-all`, and `GET /admin/v1/secrets/rotation-status/{op_id}`.
- Because the provider contract, tests, and operator docs disagree, the repo currently overstates how coherent and well-verified the Phase 13 secrets-rotation story is.

Paths:
- `services/ai-gateway/README.md`
- `services/ai-gateway/docs/ROTATION_RUNBOOK.md`
- `services/ai-gateway/app/dependencies.py`
- `services/ai-gateway/app/adapters/secrets/multi_provider.py`
- `services/ai-gateway/app/domain/secrets/kek_provider.py`
- `services/ai-gateway/tests/unit/test_kek_provider.py`
- `services/ai-gateway/tests/test_postgres_secrets.py`
- `services/ai-gateway/tests/unit/test_multi_provider.py`
- `docs/features/operations/secrets-rotation.md`
- `services/ai-gateway/app/api/admin/router.py`

Next step:
- Choose one canonical KEK-provider/env contract for the live gateway, remove or quarantine the stale provider path, realign the Phase 13 docs and admin endpoints to that contract, and add end-to-end rotation coverage against the active provider and router surfaces.

### 20. Admin Control-Plane Auth Realism and Dev-Bypass Containment

Status: `in_progress`

Why it is still open:
- The AI gateway README still presents the admin plane as `RBAC Auth` with a deny-by-default control surface. See [services/ai-gateway/README.md](services/ai-gateway/README.md) and [README.md](README.md), which both frame Phase 7 RBAC as a completed enforcement layer.
- The default local runtime path does not exercise that contract. [services/ai-gateway/scripts/start.sh](services/ai-gateway/scripts/start.sh) exports `MODE=dev`, `DEV_MODE=true`, and `USE_JSON_STORES=true` unless the operator overrides them.
- In that default dev mode, [services/ai-gateway/app/middleware/auth_admin.py](services/ai-gateway/app/middleware/auth_admin.py) accepts missing bearer auth by falling back to `X-Talos-Principal` or a hard-coded `"admin"` principal, and it grants wildcard permissions if RBAC resolution fails because the database is unavailable.
- The built-in admin dashboard depends on that bypassed path instead of demonstrating real admin auth. [services/ai-gateway/app/dashboard/router.py](services/ai-gateway/app/dashboard/router.py) fetches `/admin/v1/*` endpoints without attaching auth headers, including secret, upstream, and MCP mutation calls.
- That means the repo’s default local workflow does not validate the documented JWT/RBAC path for the admin control plane and can mask authorization regressions behind dev-only fallback behavior.

Paths:
- `services/ai-gateway/README.md`
- `README.md`
- `services/ai-gateway/scripts/start.sh`
- `services/ai-gateway/app/middleware/auth_admin.py`
- `services/ai-gateway/app/domain/auth.py`
- `services/ai-gateway/app/dashboard/router.py`

Next step:
- Make the dev bypass explicit as a demo-only mode, decide whether the default local start path should keep granting implicit admin access, and add at least one supported local workflow that exercises real admin JWT/RBAC enforcement instead of the current fallback-only dashboard path.

### 21. Governance-Agent Ownership and Active-Stack Boundary Consolidation

Status: `in_progress`

Why it is still open:
- The repo currently carries two overlapping TGA implementations. The standalone governance-agent service ships its own runtime and validator in [services/governance-agent/src/talos_governance_agent/domain/runtime.py](services/governance-agent/src/talos_governance_agent/domain/runtime.py) and [services/governance-agent/src/talos_governance_agent/domain/validator.py](services/governance-agent/src/talos_governance_agent/domain/validator.py), while the AI gateway also ships its own runtime and validator in [services/ai-gateway/app/domain/tga/runtime.py](services/ai-gateway/app/domain/tga/runtime.py) and [services/ai-gateway/app/domain/tga/validator.py](services/ai-gateway/app/domain/tga/validator.py).
- Those implementations are not just thin adapters over shared contracts; they carry overlapping execution-state, authorization, and recovery logic with separate tests and separate storage adapters. The gateway side uses [services/ai-gateway/app/adapters/postgres/tga_store.py](services/ai-gateway/app/adapters/postgres/tga_store.py), while the standalone governance-agent uses [services/governance-agent/src/talos_governance_agent/adapters/sqlite_state_store.py](services/governance-agent/src/talos_governance_agent/adapters/sqlite_state_store.py).
- The program anchor explicitly says Talos should avoid duplicated protocol logic across repos and preserve clear ownership boundaries. The current TGA split cuts against that rule because runtime semantics can drift independently in two codepaths.
- The supported-stack story is also inconsistent. [docs/guides/development.md](docs/guides/development.md) says `start_all.sh` starts `talos-governance-agent`, but the actual service loop in [deploy/scripts/start_all.sh](deploy/scripts/start_all.sh) only starts entries from [deploy/scripts/common.sh](deploy/scripts/common.sh), and `COMMON_SERVICES` does not include the governance-agent.
- Deployment assumptions are similarly mixed. [services/governance-agent/README.md](services/governance-agent/README.md) positions TGA as a standalone sidecar/daemon, while [deploy/k8s/base/gateway/deployment.yaml](deploy/k8s/base/gateway/deployment.yaml) mounts `TGA_DB_PATH` directly into the gateway pod, implying gateway-embedded TGA state rather than a clearly separate service boundary.
- Because TGA ownership is split across a standalone submodule and an embedded gateway domain, the repo currently overstates how settled the governance-agent architecture is.

Paths:
- `services/governance-agent/src/talos_governance_agent/domain/runtime.py`
- `services/governance-agent/src/talos_governance_agent/domain/validator.py`
- `services/governance-agent/src/talos_governance_agent/adapters/sqlite_state_store.py`
- `services/governance-agent/README.md`
- `services/ai-gateway/app/domain/tga/runtime.py`
- `services/ai-gateway/app/domain/tga/validator.py`
- `services/ai-gateway/app/adapters/postgres/tga_store.py`
- `docs/guides/development.md`
- `deploy/scripts/start_all.sh`
- `deploy/scripts/common.sh`
- `deploy/k8s/base/gateway/deployment.yaml`

Next step:
- Decide which component owns TGA runtime semantics and storage contracts, collapse the duplicate runtime/validator logic behind that owner, and align local-stack scripts, deployment manifests, and docs around either a true standalone governance-agent service or an explicitly gateway-embedded TGA subsystem.

### 22. Deployment Manifests and Shipped Topology Parity

Status: `in_progress`

Why it is still open:
- The repo’s deployment artifacts still package the older `talos-gateway` topology as the primary shipped control plane. [deploy/k8s/base/kustomization.yaml](deploy/k8s/base/kustomization.yaml) includes `gateway/*` resources and image rewrites for `talos-gateway`, but it does not include a corresponding `services/ai-gateway` deployment resource.
- The Helm chart tells the same story. [deploy/helm/talos/values.yaml](deploy/helm/talos/values.yaml) defines a `gateway` service backed by `talos-gateway`, and [deploy/helm/talos/templates/gateway.yaml](deploy/helm/talos/templates/gateway.yaml) renders only that gateway deployment/service pair.
- That shipped topology is behind the docs and status language that increasingly describe `services/ai-gateway` as the active owner of A2A v1, public AI, budgets, secrets rotation, and other newer gateway responsibilities. See [docs/guides/development.md](docs/guides/development.md), [docs/architecture/infrastructure.md](docs/architecture/infrastructure.md), and [docs/guides/a2a-v1-rollout.md](docs/guides/a2a-v1-rollout.md).
- The deployment tree also omits other services that the docs present as part of the broader modern stack, such as the standalone governance-agent and configuration service, which reinforces that the operator-facing shipped surface is still centered on the legacy gateway-era topology rather than the newer service layout.
- Because the manifests, chart, and docs point at different canonical stacks, the repo does not currently have one unambiguous answer to “what Talos actually deploys.”

Paths:
- `deploy/k8s/base/kustomization.yaml`
- `deploy/k8s/base/gateway/deployment.yaml`
- `deploy/helm/talos/values.yaml`
- `deploy/helm/talos/templates/gateway.yaml`
- `docs/guides/development.md`
- `docs/architecture/infrastructure.md`
- `docs/guides/a2a-v1-rollout.md`

Next step:
- Decide whether the supported deployment target is still `talos-gateway`, a migrated `talos-ai-gateway` stack, or a hybrid, then update Kustomize, Helm, and operator docs so the shipped manifests match that supported topology exactly.

### 23. Configuration Service First-Class Deployment and Dashboard Ownership Parity

Status: `completed`

The configuration service is now a first-class deployment in the K8s manifest set, and the dashboard defaults have been aligned to its dedicated port.
- Added `deploy/k8s/base/configuration/deployment-service.yaml` on canonical port 8003.
- Updated `deploy/k8s/base/kustomization.yaml` to include the configuration service and modern ai-gateway topology.
- Updated `deploy/k8s/base/ingress-api.yaml` to route `/config` to the configuration service.
- Verified with `kubectl kustomize`.

Paths:
- `services/configuration/README.md`
- `docs/guides/development.md`
- `deploy/k8s/base/kustomization.yaml`
- `site/dashboard/src/app/api/config/ui-bootstrap/route.ts`
- `site/dashboard/src/app/api/config/[...path]/route.ts`
- `site/dashboard/src/features/configuration/adapters/configuration-adapter.ts`

Next step:
- Decide whether configuration is a standalone required service in supported deployments, then add the missing deployment wiring and align dashboard proxy defaults and operator docs to that ownership model.

### 24. Audit Explorer Product Surface Parity

Status: `in_progress`

Why it is still open:
- The audit explorer docs promise a much richer operator surface than the currently verified runtime exposes. [docs/features/observability/audit-explorer.md](docs/features/observability/audit-explorer.md) describes dashboard proof verification plus CLI commands such as `talos audit verify`, `talos audit root`, `talos audit chain`, and `talos audit export`.
- The live dashboard proxy surface is far narrower. The only audit-facing API routes under [site/dashboard/src/app/api](site/dashboard/src/app/api) are [site/dashboard/src/app/api/events/route.ts](site/dashboard/src/app/api/events/route.ts) for paginated event lists and [site/dashboard/src/app/api/audit/stream/route.ts](site/dashboard/src/app/api/audit/stream/route.ts) for SSE streaming.
- The audit service itself does expose root/proof primitives in [services/audit/src/adapters/http/main.py](services/audit/src/adapters/http/main.py), but this pass did not find corresponding dashboard proxy routes or UI plumbing for `/root` and `/proof/{event_id}`.
- A repo-wide grep in this pass also did not find an implemented `talos audit` CLI surface matching the commands documented in `audit-explorer.md`; those command names currently appear in docs and troubleshooting prose, not in a verified local CLI implementation.
- Because the docs promise proof-verification workflows that are not clearly wired through the current dashboard or CLI, the observability story is stronger in prose than in the verified product surface.

Paths:
- `docs/features/observability/audit-explorer.md`
- `site/dashboard/src/app/api/events/route.ts`
- `site/dashboard/src/app/api/audit/stream/route.ts`
- `services/audit/src/adapters/http/main.py`
- `docs/reference/failure-modes.md`
- `docs/guides/error-troubleshooting.md`

Next step:
- Either implement the documented audit root/proof/verify flows in the dashboard and CLI, or narrow the audit-explorer docs so they describe the currently shipped list/stream capabilities separately from future proof-verification tooling.

### 25. Dashboard Setup and Agent-Onboarding Flow Hardening

Status: `completed`

The dashboard setup and agent-onboarding API surface has been hardened with real authentication and secret verification.
- Implemented `verifySetupAccess` in `site/dashboard/src/lib/setup-gate.ts` to enforce admin session checks.
- Updated `site/dashboard/src/app/api/setup/status/route.ts` to use `verifySetupAccess`.
- Implemented real Bearer token verification with SHA-256 hashing in `site/dashboard/src/app/api/setup/agents/[id]/poll/route.ts`.
- Verified that setup jobs and status reporting are now protected by the documented authenticated handshake.

Paths:
- `docs/security/security-dashboard.md`
- `site/dashboard/src/app/api/setup/agents/token/route.ts`
- `site/dashboard/src/app/api/setup/jobs/route.ts`
- `site/dashboard/src/app/api/setup/agents/[id]/poll/route.ts`
- `site/dashboard/src/app/api/setup/agents/register/route.ts`
- `site/dashboard/src/app/api/setup/status/route.ts`
- `site/dashboard/src/lib/setup-gate.ts`

Next step:
- Add real admin/session enforcement to setup token and job APIs, verify agent bearer auth on poll/lease, remove hard-coded onboarding outputs, and decide whether the setup flow is a supported operator feature or an internal demo path that should be documented more narrowly.

### 26. Security Dashboard Auth and Runtime-Mode Docs Parity

Status: `in_progress`

Why it is still open:
- The published dashboard security docs still describe an auth model that does not match the current implementation. [docs/security/security-dashboard.md](docs/security/security-dashboard.md) says the console uses `NextAuth v5` with a default admin email/password, while the actual implementation uses custom HMAC-signed session cookies in [site/dashboard/src/lib/auth/session.ts](site/dashboard/src/lib/auth/session.ts) and passkey/WebAuthn flows in [site/dashboard/src/app/login/page.tsx](site/dashboard/src/app/api/auth/webauthn/login/verify/route.ts) plus the other `site/dashboard/src/app/api/auth/webauthn/*` routes.
- The signup/bootstrap story is also different from the docs. [site/dashboard/src/app/login/page.tsx](site/dashboard/src/app/login/page.tsx) supports a bootstrap-token-based passkey registration flow, while [site/dashboard/src/app/signup/page.tsx](site/dashboard/src/app/signup/page.tsx) is still an explicit mock that redirects to login and tells the user to use the default admin credentials.
- The same docs page also overstates the available data-source modes. [docs/security/security-dashboard.md](docs/security/security-dashboard.md) advertises `MOCK`, `HTTP`, `WS`, and `SQLITE` as supported dashboard modes, but the exported runtime config in [site/dashboard/src/lib/config.ts](site/dashboard/src/lib/config.ts) and [site/dashboard/src/app/api/runtime-config/route.ts](site/dashboard/src/app/api/runtime-config/route.ts) only surfaces `MOCK` or `HTTP`.
- There is code for additional adapters, but it is not equivalent to a fully supported product surface. [site/dashboard/src/lib/data/DataSource.ts](site/dashboard/src/lib/data/DataSource.ts) can instantiate `WsDataSource` and `SqliteDataSource`, yet `SqliteDataSource` still falls back to `MockDataSource` for most operations, stats, events, and subscriptions rather than providing a distinct verified runtime path.
- Because the docs still describe the old auth/bootstrap model and broader runtime-mode support, the dashboard’s public/operator story is ahead of the currently verified implementation.

Paths:
- `docs/security/security-dashboard.md`
- `site/dashboard/src/lib/auth/session.ts`
- `site/dashboard/src/app/login/page.tsx`
- `site/dashboard/src/app/signup/page.tsx`
- `site/dashboard/src/app/api/auth/webauthn/login/verify/route.ts`
- `site/dashboard/src/lib/config.ts`
- `site/dashboard/src/app/api/runtime-config/route.ts`
- `site/dashboard/src/lib/data/DataSource.ts`
- `site/dashboard/src/lib/data/WsDataSource.ts`

Next step:
- Update the dashboard docs to describe the real WebAuthn/session-cookie flow and the current bootstrap path, then either finish and formally support the extra runtime modes or narrow the documented mode matrix to the configurations that are actually shipped and verified.

### 27. Dashboard Admin Proxy Identity Propagation Parity

Status: `in_progress`

Why it is still open:
- The dashboard is positioned as an authenticated admin console, but its admin proxy routes do not consistently propagate identity to the gateway. [site/dashboard/src/app/api/admin/me/route.ts](site/dashboard/src/app/api/admin/me/route.ts) derives `X-Talos-Principal` and `X-Talos-Role` from the server session before calling `/admin/v1/me`.
- The other admin proxy routes in [site/dashboard/src/app/api/admin/secrets/route.ts](site/dashboard/src/app/api/admin/secrets/route.ts), [site/dashboard/src/app/api/admin/audit/stats/route.ts](site/dashboard/src/app/api/admin/audit/stats/route.ts), and [site/dashboard/src/app/api/admin/telemetry/stats/route.ts](site/dashboard/src/app/api/admin/telemetry/stats/route.ts) only validate the local session and then call the gateway without forwarding a principal or bearer token.
- That mismatch matters because the gateway admin auth path in [services/ai-gateway/app/middleware/auth_admin.py](services/ai-gateway/app/middleware/auth_admin.py) requires a bearer token or, in dev mode only, an `X-Talos-Principal` fallback. In production-style mode, a dashboard proxy that forwards no identity cannot exercise the documented gateway RBAC surface successfully.
- The result is that the dashboard admin console is closer to a partial proxy scaffold than a consistently authenticated admin client for the live gateway.

Paths:
- `site/dashboard/src/app/api/admin/me/route.ts`
- `site/dashboard/src/app/api/admin/secrets/route.ts`
- `site/dashboard/src/app/api/admin/audit/stats/route.ts`
- `site/dashboard/src/app/api/admin/telemetry/stats/route.ts`
- `services/ai-gateway/app/middleware/auth_admin.py`

Next step:
- Define one supported identity-forwarding model from dashboard session to gateway admin API, apply it consistently across all `/api/admin/*` proxies, and add coverage that proves the dashboard works against non-dev gateway auth without relying on implicit local fallbacks.

### 28. Dashboard Control-Plane API Namespace Parity

Status: `in_progress`

Why it is still open:
- The dashboard shell pages for upstreams, model groups, MCP servers, and MCP policies are wired through `dataSource` calls in [site/dashboard/src/app/(shell)/llm/upstreams/page.tsx](site/dashboard/src/app/(shell)/llm/upstreams/page.tsx), [site/dashboard/src/app/(shell)/llm/models/page.tsx](site/dashboard/src/app/(shell)/llm/models/page.tsx), [site/dashboard/src/app/(shell)/mcp/servers/page.tsx](site/dashboard/src/app/(shell)/mcp/servers/page.tsx), and [site/dashboard/src/app/(shell)/mcp/policies/page.tsx](site/dashboard/src/app/(shell)/mcp/policies/page.tsx).
- The active `HttpDataSource` implementation behind those pages calls `/api/admin/v1/llm/*` and `/api/admin/v1/mcp/*` paths in [site/dashboard/src/lib/data/HttpDataSource.ts](site/dashboard/src/lib/data/HttpDataSource.ts).
- The Next app does not currently expose matching proxy routes. A sweep of [site/dashboard/src/app/api](site/dashboard/src/app/api) found only a small `admin` subset: `/api/admin/me`, `/api/admin/secrets`, `/api/admin/audit/stats`, and `/api/admin/telemetry/stats`.
- There is also no rewrite layer in [site/dashboard/next.config.ts](site/dashboard/next.config.ts) or [site/dashboard/src/middleware.ts](site/dashboard/src/middleware.ts) that would forward those missing `/api/admin/v1/*` requests elsewhere.
- That means significant parts of the modern dashboard management UI are pointed at admin API namespaces that are not actually implemented in the Next app, which is a stronger gap than simple docs drift.

Paths:
- `site/dashboard/src/app/(shell)/llm/upstreams/page.tsx`
- `site/dashboard/src/app/(shell)/llm/models/page.tsx`
- `site/dashboard/src/app/(shell)/mcp/servers/page.tsx`
- `site/dashboard/src/app/(shell)/mcp/policies/page.tsx`
- `site/dashboard/src/lib/data/HttpDataSource.ts`
- `site/dashboard/src/app/api`
- `site/dashboard/next.config.ts`
- `site/dashboard/src/middleware.ts`

Next step:
- Add the missing `/api/admin/v1/*` dashboard proxy routes or change `HttpDataSource` and the shell pages to use the currently implemented admin endpoints, then verify the full management UI against a live gateway instead of mock/default fallbacks.

### 29. Root CLI Command Surface Parity

Status: `in_progress`

Why it is still open:
- The root package still publishes a `talos` CLI entrypoint in [pyproject.toml](pyproject.toml), but that entrypoint points at [src/client/cli.py](src/client/cli.py), which is still the older blockchain-messaging/P2P client CLI.
- That CLI file still advertises `bmp init`, `bmp register`, `bmp send`, `bmp listen`, `bmp peers`, and `bmp status` in its module docstring and user-facing error messages, even though the installed script name is `talos`.
- A repo-wide sweep in this pass did not find implemented `talos audit`, `talos audit verify`, `talos audit export`, `talos audit root`, or similar operator commands matching the docs in [docs/features/observability/audit-explorer.md](docs/features/observability/audit-explorer.md), [docs/features/observability/audit-use-cases.md](docs/features/observability/audit-use-cases.md), [docs/reference/failure-modes.md](docs/reference/failure-modes.md), and [docs/guides/error-troubleshooting.md](docs/guides/error-troubleshooting.md).
- That leaves the root CLI surface split between a legacy `bmp`-era implementation and a much newer operator command vocabulary in the docs, with no verified bridge between them.

Paths:
- `pyproject.toml`
- `src/client/cli.py`
- `docs/features/observability/audit-explorer.md`
- `docs/features/observability/audit-use-cases.md`
- `docs/reference/failure-modes.md`
- `docs/guides/error-troubleshooting.md`

Next step:
- Decide whether the root `talos` CLI is still a legacy transport client, a future operator console, or both; then either implement the documented operator/audit subcommands or narrow the docs so the published command set matches the installed entrypoint.

### 30. Demo and Examples Product-Surface Parity

Status: `in_progress`

Why it is still open:
- The one-command demo docs still promise a root `talos demo` flow in [docs/getting-started/one-command-demo.md](docs/getting-started/one-command-demo.md), but a repo-wide sweep in this pass did not find an implemented `talos demo` command in the installed root CLI surface.
- The dashboard examples catalog is also wired to the wrong manifest owner. [site/dashboard/src/app/api/examples/manifest/route.ts](site/dashboard/src/app/api/examples/manifest/route.ts) reads from `submodules/talos-contracts/examples_manifest.json`, while this repo currently ships example manifests at [examples/examples_manifest.json](examples/examples_manifest.json) and [contracts/examples_manifest.json](contracts/examples_manifest.json).
- The example chat proxy path is internally inconsistent. [site/dashboard/src/app/api/examples/chat/send/route.ts](site/dashboard/src/app/api/examples/chat/send/route.ts) defaults `TALOS_CHAT_URL` to `http://localhost:8090` and injects a hard-coded `session_id: "demo-session-v1"`, while [site/dashboard/src/app/api/examples/chat/health/route.ts](site/dashboard/src/app/api/examples/chat/health/route.ts) defaults to `http://localhost:8100`.
- That health proxy also validates fields the current chat backend does not return. [site/dashboard/src/app/api/examples/chat/health/route.ts](site/dashboard/src/app/api/examples/chat/health/route.ts) requires `contract_hash`, but the active backend health response in [services/ai-chat-agent/api/src/main.py](services/ai-chat-agent/api/src/main.py) returns `app`, `status`, `sdk_available`, and `active_sessions` without `contract_hash`.
- Because the demo docs, dashboard examples hub, and example backends disagree on entrypoints and contracts, the examples surface is more aspirational than the repo’s “try it now” positioning suggests.

Paths:
- `docs/getting-started/one-command-demo.md`
- `site/dashboard/src/app/api/examples/manifest/route.ts`
- `examples/examples_manifest.json`
- `contracts/examples_manifest.json`
- `site/dashboard/src/app/api/examples/chat/send/route.ts`
- `site/dashboard/src/app/api/examples/chat/health/route.ts`
- `services/ai-chat-agent/api/src/main.py`

Next step:
- Decide which component owns the examples manifest, make the dashboard examples API read that canonical source, align chat demo env defaults and response contracts, and either implement `talos demo` or narrow the one-command demo docs to the actual runnable flow.

### 31. Secure Chat Demo Cryptographic and Audit Reality

Status: `in_progress`

Why it is still open:
- The public-facing secure-chat materials still promise stronger guarantees than the currently wired example path provides. [docs/guides/runbook-non-technical.md](docs/guides/runbook-non-technical.md) says every message in the demo is audited and that the dashboard proves this with `Verified` / `Audited` badges, while the marketing strip in [site/marketing/src/components/BentoGrid.tsx](site/marketing/src/components/BentoGrid.tsx) says Talos provides `Every message encrypted` and `Zero plaintext exposure`.
- The actual dashboard secure-chat example under [site/dashboard/src/app/(shell)/examples/chat/page.tsx](site/dashboard/src/app/(shell)/examples/chat/page.tsx) still sends plaintext-only user input through [site/dashboard/src/app/api/examples/chat/send/route.ts](site/dashboard/src/app/api/examples/chat/send/route.ts). That proxy validates only `{ content }`, injects a fixed `session_id: "demo-session-v1"`, and does not perform any client-side encryption, proof fetch, or capability/auth handshake before forwarding to the backend.
- The active backend behind that demo, [services/ai-chat-agent/api/src/main.py](services/ai-chat-agent/api/src/main.py), still accepts plaintext `content` explicitly marked `Demo compatibility`, falls back to a mock shared secret of `b'0'*32` when `CHAT_SHARED_SECRET` is unset, and only marks the response `secure=true` on the encrypted-message path. The dashboard example page does not surface or enforce that `secure` flag; it always presents fixed success claims for encryption, signatures, and blockchain audit.
- The same backend also returns simulated security metadata rather than verified proof state. Its `/v1/chat/summary` response includes a hard-coded `blockchain_height`, static assistant/user identifiers, and zero tool calls, while `/health` does not expose the `contract_hash` field that neighboring dashboard example routes expect.
- The audit-event names in the non-technical runbook do exist, but on a different service path. [services/gateway/main.py](services/gateway/main.py) emits `CHAT_REQUEST_RECEIVED`, `CHAT_TOOL_CALL`, `CHAT_TOOL_RESULT`, and `CHAT_RESPONSE_SENT` on the older `/mcp/tools/chat` flow, yet the dashboard `Secure Chat` example is wired to the separate `ai-chat-agent` demo service instead of that audited gateway route. The docs therefore describe an audit trail that is not the same as the live example surface users actually open from the dashboard.

Paths:
- `docs/guides/runbook-non-technical.md`
- `site/marketing/src/components/BentoGrid.tsx`
- `site/dashboard/src/app/(shell)/examples/chat/page.tsx`
- `site/dashboard/src/app/api/examples/chat/send/route.ts`
- `site/dashboard/src/app/api/examples/chat/summary/route.ts`
- `site/dashboard/src/app/api/examples/chat/health/route.ts`
- `services/ai-chat-agent/api/src/main.py`
- `services/gateway/main.py`

Next step:
- Either route the dashboard secure-chat demo through a genuinely encrypted, audited, proof-reporting backend and show the real `secure` / proof state in the UI, or relabel the current example as a demo-grade mock/plaintext flow and remove the stronger “every message encrypted” and “verified/audited” claims from the docs and dashboard.

### 32. Dashboard Secure-Agent Shell and Chat-Agent Contract Parity

Status: `in_progress`

Why it is still open:
- The dashboard still ships a separate `Talos Secure Agent` shell in [site/dashboard/src/app/(shell)/agent/page.tsx](site/dashboard/src/app/(shell)/agent/page.tsx) that presents itself as a secure, audited control surface, but the page still hard-codes a local principal id, seeds fixed capabilities such as `chat` and `tool:read_file`, and labels its initial tool fetch as `mock capability discovery`.
- The backend routes for that shell are not aligned with the only active chat-agent implementation. [site/dashboard/src/app/api/agent/chat/route.ts](site/dashboard/src/app/api/agent/chat/route.ts) proxies to `${AGENT_URL}/v1/chat`, [site/dashboard/src/app/api/agent/tools/route.ts](site/dashboard/src/app/api/agent/tools/route.ts) proxies to `${AGENT_URL}/v1/tools`, and [site/dashboard/src/app/api/agent/models/route.ts](site/dashboard/src/app/api/agent/models/route.ts) proxies to `${AGENT_URL}/v1/models`.
- The actual backend in [services/ai-chat-agent/api/src/main.py](services/ai-chat-agent/api/src/main.py) does not expose those routes. It currently defines only `/v1/chat/send`, `/v1/chat/summary`, and `/v1/chat/stats`, so the shell’s chat, tool discovery, and model discovery contracts are not backed by a matching service implementation.
- The proxy route also explicitly keeps demo-grade behavior. [site/dashboard/src/app/api/agent/chat/route.ts](site/dashboard/src/app/api/agent/chat/route.ts) skips strict model validation `for demo stability`, and [site/dashboard/src/features/agent/AgentChat.tsx](site/dashboard/src/features/agent/AgentChat.tsx) still contains commentary that assumes a different `/v1/chat/completions` shape than the route it actually calls.
- That leaves the secure-agent shell in an ambiguous state: it looks like a core control-plane feature, but it is currently a partially mocked UI wired to backend paths that do not exist on the only active chat-agent service.

Paths:
- `site/dashboard/src/app/(shell)/agent/page.tsx`
- `site/dashboard/src/app/api/agent/chat/route.ts`
- `site/dashboard/src/app/api/agent/tools/route.ts`
- `site/dashboard/src/app/api/agent/models/route.ts`
- `site/dashboard/src/features/agent/AgentChat.tsx`
- `services/ai-chat-agent/api/src/main.py`

Next step:
- Decide whether `/agent` is a supported dashboard surface or an internal experiment. If it is supported, define one stable backend contract for chat, tools, and models plus real capability discovery and policy enforcement. If it is not, remove or clearly relabel the page and its API routes so they no longer read as a shipped secure control surface.

### 33. DevOps Example API and AIOps Backend Contract Parity

Status: `in_progress`

Why it is still open:
- The dashboard and deploy runbook still imply a runnable DevOps example surface that is not backed by the shipped `aiops` service contract. [deploy/RUNBOOK.md](deploy/RUNBOOK.md) tells operators to open `/examples/devops` and expect status checks from port `8200`, but the dashboard app currently has no `site/dashboard/src/app/(shell)/examples/devops` page. Under the examples shell, only [site/dashboard/src/app/(shell)/examples/page.tsx](site/dashboard/src/app/(shell)/examples/page.tsx) and [site/dashboard/src/app/(shell)/examples/chat/page.tsx](site/dashboard/src/app/(shell)/examples/chat/page.tsx) exist.
- The remaining dashboard API routes for that example are wired to endpoints that the backend does not expose. [site/dashboard/src/app/api/examples/devops/status/route.ts](site/dashboard/src/app/api/examples/devops/status/route.ts) calls `${AIOPS_URL}/v1/status`, [site/dashboard/src/app/api/examples/devops/logs/route.ts](site/dashboard/src/app/api/examples/devops/logs/route.ts) calls `${AIOPS_URL}/v1/logs`, and [site/dashboard/src/app/api/examples/devops/trigger/route.ts](site/dashboard/src/app/api/examples/devops/trigger/route.ts) calls `${AIOPS_URL}/v1/trigger`.
- The active AIOps backend in [services/aiops/api/src/main.py](services/aiops/api/src/main.py) only exposes `/health`, `/metrics/integrity`, and `/metrics`. Its `/health` response also does not match the dashboard’s expectations in [site/dashboard/src/app/api/examples/devops/health/route.ts](site/dashboard/src/app/api/examples/devops/health/route.ts), which requires fields such as `app`, `mode`, and `contract_hash`.
- The service README still overstates the shipped surface. [services/aiops/README.md](services/aiops/README.md) describes a `feature-complete, standalone DevOps automation agent` with `Mission Control` and secure tool execution, but the currently verified HTTP API is limited to health and anomaly/integrity metrics rather than the dashboard’s expected job-control and log-streaming contract.
- That leaves the repo with a partially preserved example API surface, a runbook that points to a nonexistent page, and an AIOps backend whose current API does not line up with the dashboard/devops narrative.

Paths:
- `deploy/RUNBOOK.md`
- `site/dashboard/src/app/(shell)/examples/page.tsx`
- `site/dashboard/src/app/api/examples/devops/health/route.ts`
- `site/dashboard/src/app/api/examples/devops/status/route.ts`
- `site/dashboard/src/app/api/examples/devops/logs/route.ts`
- `site/dashboard/src/app/api/examples/devops/trigger/route.ts`
- `services/aiops/api/src/main.py`
- `services/aiops/README.md`

Next step:
- Decide whether the DevOps example is still a supported product/demo surface. If it is, implement one consistent backend contract and restore the missing dashboard route. If it is not, remove the orphaned API routes and runbook references so the repo stops advertising a nonexistent `/examples/devops` workflow.

### 34. Deprecated Configuration Dashboard Retirement and Stack Parity

Status: `in_progress`

Why it is still open:
- The older configuration dashboard is marked deprecated, but it is not actually retired from the repo’s operational surface. [site/configuration-dashboard/README.md](site/configuration-dashboard/README.md) says the app has been consolidated into `site/dashboard`, is read-only, and will be removed in a future release.
- Despite that, deployment metadata still treats it as an active repo/component. [deploy/scripts/common.sh](deploy/scripts/common.sh) keeps `talos-configuration-dashboard` in `COMMON_REPOS`, and [deploy/submodules.json](deploy/submodules.json) still includes the `talos-configuration-dashboard` submodule entry under `site/configuration-dashboard`.
- Operator guidance also still references the deprecated app as a live surface. [deploy/RUNBOOK.md](deploy/RUNBOOK.md) tells users to open `http://localhost:3002` for the `Legacy Agent` / `Reference Implementation` UI, even though the main dashboard stack is centered on port `3000`.
- The deprecated app itself still contains active mock behavior rather than a clean tombstone. [site/configuration-dashboard/src/adapters/api-adapter.ts](site/configuration-dashboard/src/adapters/api-adapter.ts) returns hard-coded merchants, uses a fixed bearer token, and posts to a local in-app API. [site/configuration-dashboard/src/app/api/policies/route.ts](site/configuration-dashboard/src/app/api/policies/route.ts) performs only mock authz and writes an in-memory audit log, while [site/configuration-dashboard/src/app/page.tsx](site/configuration-dashboard/src/app/page.tsx) still markets a `Security Console` and `Hexagonal Core Active`.
- That makes the retirement story incomplete: the repo now has a newer configuration surface inside the main dashboard, but the deprecated dashboard still exists as a buildable mock control plane and remains present in deploy/submodule/runbook flows.

Paths:
- `site/configuration-dashboard/README.md`
- `deploy/scripts/common.sh`
- `deploy/submodules.json`
- `deploy/RUNBOOK.md`
- `site/configuration-dashboard/src/app/page.tsx`
- `site/configuration-dashboard/src/adapters/api-adapter.ts`
- `site/configuration-dashboard/src/app/api/policies/route.ts`

Next step:
- Either fully retire `site/configuration-dashboard` from deploy metadata, submodule manifests, and runbooks, or keep it as an explicitly labeled legacy prototype with clear isolation from the supported main dashboard configuration surface and operator docs.

### 35. Dashboard AI Playground Gateway and Response-Shape Parity

Status: `in_progress`

Why it is still open:
- The dashboard ships a user-visible `AI Playground` page in [site/dashboard/src/app/(shell)/llm/playground/page.tsx](site/dashboard/src/app/(shell)/llm/playground/page.tsx) that presents itself as a real LLM control-plane surface. The page says interactions are recorded in audit logs with a service-account identity and tells operators to use it to verify model-group fallback and routing policies.
- The underlying data path does not line up with that story. [site/dashboard/src/lib/data/HttpDataSource.ts](site/dashboard/src/lib/data/HttpDataSource.ts) routes playground chat through `/api/agent/chat`, not through the gateway’s public AI inference endpoint in [services/ai-gateway/app/api/public_ai/router.py](services/ai-gateway/app/api/public_ai/router.py), which actually owns `/chat/completions`.
- The proxy route behind that call is also contract-incompatible with the page. [site/dashboard/src/app/api/agent/chat/route.ts](site/dashboard/src/app/api/agent/chat/route.ts) is a streaming SSE proxy to `${TALOS_CHAT_URL}/v1/chat`, while the playground page expects a synchronous JSON chat-completion payload with `choices`, `usage`, and `model` fields.
- The route target is the separate chat-agent service, not the AI gateway’s routing plane. The only active chat-agent implementation in [services/ai-chat-agent/api/src/main.py](services/ai-chat-agent/api/src/main.py) does not expose `/v1/chat/completions` or a model-group-aware control-plane surface, and the proxy route still carries demo-oriented assumptions from the secure-agent shell path.
- That means the current playground cannot reliably prove the thing it claims to prove: model-group routing, service-account audit attribution, and gateway fallback behavior. It is wired to the wrong backend contract and the wrong response shape for the UI that consumes it.

Paths:
- `site/dashboard/src/app/(shell)/llm/playground/page.tsx`
- `site/dashboard/src/lib/data/HttpDataSource.ts`
- `site/dashboard/src/app/api/agent/chat/route.ts`
- `services/ai-gateway/app/api/public_ai/router.py`
- `services/ai-chat-agent/api/src/main.py`

Next step:
- Rewire the playground onto the real AI-gateway inference surface with one supported response shape, or relabel it as an experimental agent-chat surface until it genuinely exercises gateway model-group routing and audit attribution.

### 36. Mission Control KPI and Analytics Truthfulness

Status: `in_progress`

Why it is still open:
- The main dashboard console in [site/dashboard/src/app/(shell)/console/page.tsx](site/dashboard/src/app/(shell)/console/page.tsx) presents `Mission Control` as `Real-time security analytics and enforcement`, but some of the headline metrics are still synthesized in the client instead of being grounded in backend-reported analytics.
- In HTTP mode, [site/dashboard/src/lib/data/HttpDataSource.ts](site/dashboard/src/lib/data/HttpDataSource.ts) does fetch real admin telemetry and audit summaries, but it still hard-codes `auth_success_rate: 1.0` and fixed `latency_percentiles: { p50: 10, p95: 20, p99: 50 }` rather than deriving those values from the upstream stats endpoints in [site/dashboard/src/app/api/admin/telemetry/stats/route.ts](site/dashboard/src/app/api/admin/telemetry/stats/route.ts) and [site/dashboard/src/app/api/admin/audit/stats/route.ts](site/dashboard/src/app/api/admin/audit/stats/route.ts).
- The KPI presentation layer then renders those synthetic values as if they were live operational measurements. [site/dashboard/src/components/dashboard/KPIGrid.tsx](site/dashboard/src/components/dashboard/KPIGrid.tsx) uses `auth_success_rate` to compute denial rate, prefers `latency_avg` or the synthetic percentile fallback for latency, and also shows hard-coded trend badges such as `+12%`, `99.9%`, and `-2%`.
- The live-update hook further blurs the source of truth. [site/dashboard/src/lib/hooks/useDataSource.ts](site/dashboard/src/lib/hooks/useDataSource.ts) increments `requests_24h` opportunistically whenever a streamed audit event arrives instead of reconciling against a real aggregate counter or recomputing the visible KPI set from backend summaries.
- That means Mission Control is only partially analytics-backed today: some chart/feed data comes from real services, but several high-visibility KPI values remain client-invented or cosmetically fixed while the UI presents them as live security metrics.

Paths:
- `site/dashboard/src/app/(shell)/console/page.tsx`
- `site/dashboard/src/lib/data/HttpDataSource.ts`
- `site/dashboard/src/components/dashboard/KPIGrid.tsx`
- `site/dashboard/src/lib/hooks/useDataSource.ts`
- `site/dashboard/src/app/api/admin/telemetry/stats/route.ts`
- `site/dashboard/src/app/api/admin/audit/stats/route.ts`

Next step:
- Either source all visible KPIs and trend indicators from real gateway/audit aggregates with documented derivation rules, or explicitly mark the synthetic fields so the console no longer presents fabricated analytics as live operator truth.

### 37. Marketing Site Product Catalog and Content Ownership Parity

Status: `in_progress`

Why it is still open:
- The public marketing site is still shipping content that does not cleanly belong to Talos or is materially ahead of the verified product state. Under [site/marketing/src/app/docs](site/marketing/src/app/docs), the only docs route is [site/marketing/src/app/docs/speed-insights/page.tsx](site/marketing/src/app/docs/speed-insights/page.tsx), which is a Vercel Speed Insights guide with Vercel account setup, `@vercel/speed-insights` package installation, and `/dashboard` references unrelated to Talos.
- The marketing product catalog also renders stronger product claims than the current repo audit supports. [site/marketing/src/app/products/page.tsx](site/marketing/src/app/products/page.tsx) loads [site/marketing/src/content/products.json](site/marketing/src/content/products.json) into public product cards via [site/marketing/src/components/products/ProductCard.tsx](site/marketing/src/components/products/ProductCard.tsx), including `Stable`/`Beta` badges and outcome text.
- Several of those public outcomes are already contradicted elsewhere in the tracker. The catalog marks `talos-dashboard` as `Stable` and spotlights an `AI Configuration Assistant`, even though the dashboard agent/config assistant path is still partially mocked and contract-drifted. It advertises `talos-setup-helper` as `One-click, verified deployment of local Talos stacks via the Dashboard`, while the setup/dashboard pairing flow still has missing auth and placeholder behavior. It marks `talos-ai-chat-agent` as `Stable` with `Fully decentralized, DID-based encrypted messaging with immutable audit logs`, while the live chat demo path still accepts plaintext demo compatibility and does not expose the verified audit/proof story that copy suggests.
- The catalog also still centers older ownership boundaries that are already ambiguous in the repo. `talos-gateway` is presented as a `Stable` primary product with a unified centralized control plane, even though the repo is still split between `services/gateway` and `services/ai-gateway` and that ownership/topology question remains unresolved.
- This is a public-site issue rather than only an internal doc issue: the marketing app is actively rendering these maturity labels and outcome claims to external users, while one of its shipped docs routes is unrelated imported content.

Paths:
- `site/marketing/src/app/docs/speed-insights/page.tsx`
- `site/marketing/src/app/products/page.tsx`
- `site/marketing/src/components/products/ProductCard.tsx`
- `site/marketing/src/content/products.json`

Next step:
- Remove or replace the unrelated Vercel docs route, then audit the public product catalog so maturity badges and outcome copy only describe capabilities that are actually supported by the current Talos dashboard, setup, gateway, and chat surfaces.

### 38. Setup-Helper Agent Execution and Credential-Handling Realism

Status: `in_progress`

Why it is still open:
- The local setup-helper agent exists, but its runtime path is still closer to a scaffold than a verified secure bootstrap worker. [tools/setup-helper/talos_setup_helper/agent.py](tools/setup-helper/talos_setup_helper/agent.py) pairs with the dashboard and polls for jobs, yet `_execute_job()` still performs only a placeholder flow: it checks that a recipe id exists, creates a workspace directory, emits `started`, sleeps for one second, and then emits `completed` with `Job executed successfully (simulation)`.
- The event reporting path is likewise incomplete. That same agent sends job events with a fixed timestamp of `2024-01-01T00:00:00Z` and does not report any richer execution metadata, artifacts, or attested results back to the dashboard.
- Credential handling is still simplistic for a tool that is publicly positioned as a secure bootstrapper. [tools/setup-helper/talos_setup_helper/auth.py](tools/setup-helper/talos_setup_helper/auth.py) exchanges a pairing token for a long-lived `agent_secret`, stores it directly in `auth.json`, and then uses that value as a bearer token for all future dashboard calls. There is no rotation flow, OS-keychain integration, or stronger local secret protection beyond file mode `0600`.
- Pairing metadata is also still thin and partially hard-coded. The helper always reports `hostname: "localhost"` and `version: "0.1.0"` during pairing, which is enough for a development loop but not for a reliable verified-deployment story across real machines.
- The current tests only cover the jail and bundled manifest behavior in [tools/setup-helper/tests/test_security.py](tools/setup-helper/tests/test_security.py). This pass did not find coverage for pairing, job polling, authenticated event reporting, or real recipe execution.

Paths:
- `tools/setup-helper/talos_setup_helper/agent.py`
- `tools/setup-helper/talos_setup_helper/auth.py`
- `tools/setup-helper/tests/test_security.py`

Next step:
- Decide whether the setup-helper is a real secure bootstrap agent or still a prototype. If it is real, replace the simulated job runner with actual recipe execution and attested event reporting, improve local credential storage/rotation, and add end-to-end tests for pairing, polling, and job completion. If it remains a prototype, narrow the surrounding docs and product claims accordingly.

### 39. Talos TUI Active-Stack Parity and Runtime Correctness

Status: `in_progress`

Why it is still open:
- The repo still ships `talos-tui` as a first-class tool, but its active integration boundary is stuck on the older gateway topology rather than the stack the rest of the repo increasingly positions as canonical. [tools/talos-tui/README.md](tools/talos-tui/README.md) presents a terminal monitoring surface for the Talos network, and its Helm defaults in [tools/talos-tui/helm/talos-tui/values.yaml](tools/talos-tui/helm/talos-tui/values.yaml) still point to `http://gateway:8000` and `http://audit:8001`.
- The TUI adapters still call legacy gateway-style routes such as `/version`, `/health/ready`, `/metrics/summary`, `/peers`, and `/sessions` from [tools/talos-tui/python/src/talos_tui/adapters/gateway_http.py](tools/talos-tui/python/src/talos_tui/adapters/gateway_http.py). That partially matches [services/gateway/main.py](services/gateway/main.py), but it does not cleanly match the modern AI gateway surface. [services/ai-gateway/app/routers/health.py](services/ai-gateway/app/routers/health.py) has `/health/ready` and `/metrics/summary`, yet the only `sessions` routes in that service are A2A secure-channel endpoints under `/a2a/v1/sessions`, not the generic operator/session inventory the TUI README implies.
- Even where the route names overlap, the modern gateway is not exposing truthful data for this tool yet. [services/ai-gateway/app/routers/health.py](services/ai-gateway/app/routers/health.py) currently returns randomized values from `/metrics/summary` "for the TUI", so the dashboard cards in [tools/talos-tui/python/src/talos_tui/ui/screens/dashboard.py](tools/talos-tui/python/src/talos_tui/ui/screens/dashboard.py) cannot be treated as real operator metrics on that path.
- There is also a concrete runtime correctness bug in the TUI itself. [tools/talos-tui/python/src/talos_tui/domain/models.py](tools/talos-tui/python/src/talos_tui/domain/models.py) defines `Health.ok()` as a method, but [tools/talos-tui/python/src/talos_tui/core/coordinator.py](tools/talos-tui/python/src/talos_tui/core/coordinator.py) and [tools/talos-tui/python/tests/integration/test_manual_checklist.py](tools/talos-tui/python/tests/integration/test_manual_checklist.py) use `health.ok` as though it were a boolean field. That bound-method truthiness can mark a failed readiness probe as healthy and let handshake/state transitions proceed incorrectly.
- The built-in interop check is still scaffold-level and currently broken in monorepo use. [tools/talos-tui/ci/scripts/check_interop.sh](tools/talos-tui/ci/scripts/check_interop.sh) only checks for a hard-coded relative schema path and assumes the architecture tests are a sufficient proxy; in this audit it failed with `Schema missing!` even though the schema exists at [contracts/schemas/ui/v1/view_models.schema.json](contracts/schemas/ui/v1/view_models.schema.json), because the script does not resolve paths relative to its own location.
- This means Talos still carries a shipped TUI submodule and deploy artifacts without a verified answer to a basic mission question: is `talos-tui` a legacy `services/gateway` viewer, or a current operator surface for the modern gateway/audit stack?

Paths:
- `tools/talos-tui/README.md`
- `tools/talos-tui/helm/talos-tui/values.yaml`
- `tools/talos-tui/python/src/talos_tui/adapters/gateway_http.py`
- `tools/talos-tui/python/src/talos_tui/domain/models.py`
- `tools/talos-tui/python/src/talos_tui/core/coordinator.py`
- `tools/talos-tui/python/src/talos_tui/ui/screens/dashboard.py`
- `tools/talos-tui/python/tests/integration/test_manual_checklist.py`
- `tools/talos-tui/ci/scripts/check_interop.sh`
- `services/ai-gateway/app/routers/health.py`
- `services/gateway/main.py`
- `contracts/schemas/ui/v1/view_models.schema.json`

Next step:
- Decide whether `talos-tui` remains an actively supported operator surface. If it does, rebind it to the owned modern gateway/audit APIs, replace placeholder/randomized metrics with real inventory and telemetry, fix the `Health.ok` truthiness bug, and upgrade the interop check so it runs from the repo root and validates live endpoint parity instead of only schema presence. If it is legacy-only, narrow the README, Helm defaults, and surrounding docs accordingly.

### 40. Marketing Benchmark Claim Source-of-Truth Parity

Status: `in_progress`

Why it is still open:
- The public marketing site currently presents benchmark claims as verified and reproducible, but the source-of-truth path behind those claims is still split and partially stale. [site/marketing/src/components/Benchmarks.tsx](site/marketing/src/components/Benchmarks.tsx) and [site/marketing/src/app/methodology/page.tsx](site/marketing/src/app/methodology/page.tsx) render directly from [site/marketing/src/content/claims.json](site/marketing/src/content/claims.json), while the methodology copy says that all performance claims are “verifiable, reproducible, and sourced from open benchmarks.”
- Those rendered claims still point to the old GitHub wiki URL `https://github.com/talosprotocol/talos/wiki/Benchmarks`, even though the repo now has a first-class benchmark document at [docs/testing/benchmarks.md](docs/testing/benchmarks.md) and an update flow in [scripts/perf/update_docs.py](scripts/perf/update_docs.py) that writes repo-owned benchmark results into that page.
- A repo-wide sweep in this audit found that several public “live” values in [site/marketing/src/content/claims.json](site/marketing/src/content/claims.json) are not present in the current repo-owned benchmark docs or scripts at all, including `core.auth_throughput.ops_sec = 601694`, `crypto.verify_ed25519.latency_p99 = 0.17`, and `audit.ingest_volume.ops_sec = 100000`. By contrast, [docs/testing/benchmarks.md](docs/testing/benchmarks.md) currently contains different repo-visible benchmark values such as `Wallet.verify() = 6,542 ops/sec`, `Verification = 0.1451 ms`, `Session.encrypt(35B) = 44,898 ops/sec`, and `canonical_json_bytes() = 272,195 ops/sec`.
- The current guardrail is not strong enough to catch that drift. The marketing package exposes `npm run validate:claims` in [site/marketing/package.json](site/marketing/package.json), and that check passed in this audit, but [site/marketing/src/lib/validate-claims.ts](site/marketing/src/lib/validate-claims.ts) only validates schema shape, URL presence, and a small set of business rules; it does not verify that the published values match [docs/testing/benchmarks.md](docs/testing/benchmarks.md) or any current benchmark artifact under repo control.
- The result is a public benchmark strip and methodology page that look rigorously anchored, while the current automated guardrail still allows “live” claims whose numbers and sources are not demonstrably tied to the repo’s active benchmark outputs.

Paths:
- `site/marketing/src/components/Benchmarks.tsx`
- `site/marketing/src/app/methodology/page.tsx`
- `site/marketing/src/content/claims.json`
- `site/marketing/src/lib/validate-claims.ts`
- `site/marketing/package.json`
- `docs/testing/benchmarks.md`
- `scripts/perf/update_docs.py`

Next step:
- Choose one benchmark source of truth for the public site. Either generate [site/marketing/src/content/claims.json](site/marketing/src/content/claims.json) from the same repo-owned benchmark artifacts that update [docs/testing/benchmarks.md](docs/testing/benchmarks.md), or narrow/remove the unsupported public numbers. Then extend `validate:claims` so “live” benchmark claims must map to current repo-owned docs or artifacts instead of only having a syntactically valid source URL.

### 41. Marketing Security Page Guarantee and Metric Parity

Status: `in_progress`

Why it is still open:
- The public security page in [site/marketing/src/app/security/page.tsx](site/marketing/src/app/security/page.tsx) compresses several still-partial or stack-specific capabilities into unconditional product guarantees. It says Talos has “No passwords, no API keys, just proofs,” “Perfect forward secrecy for every tool call,” “Advanced Markov Chain analysis of audit logs to detect anomalous agent behavior in real-time,” and hard-codes posture metrics like `99.9%` proof integrity, `< 1ms` auth latency, and `100,000+` verified audit events/sec.
- The identity/auth claim does not match the currently shipped operator and data-plane surfaces. The dashboard login path in [site/dashboard/src/app/login/page.tsx](site/dashboard/src/app/login/page.tsx) uses passkeys plus a bootstrap token flow, while [site/dashboard/src/app/signup/page.tsx](site/dashboard/src/app/signup/page.tsx) still contains a mock password signup screen. On the live gateway side, [services/ai-gateway/app/middleware/auth_public.py](services/ai-gateway/app/middleware/auth_public.py) explicitly requires `Authorization: Bearer ...` virtual keys for public inference and MCP access, and [services/ai-gateway/README.md](services/ai-gateway/README.md) documents “Virtual Keys” and upstream API key rotation as first-class parts of the system.
- The encryption claim is also broader than the currently verified tool path. The page promises forward secrecy for “every tool call,” but the active MCP connector transport in [services/mcp-connector/src/talos_mcp/transport/talos_tunnel.py](services/mcp-connector/src/talos_mcp/transport/talos_tunnel.py) is still a bearer-authenticated HTTP proxy with a `dev-stub` token fallback, not a live Double Ratchet tunnel for tool invocation. That unresolved gap is already visible elsewhere in the tracker, so the security page should not flatten it into an unconditional current guarantee.
- The anomaly-detection claim overstates the shipped operator surface too. There is Markov-based analysis code in [services/aiops/api/src/main.py](services/aiops/api/src/main.py), but the current repo still has unresolved AIOps product-surface and dashboard parity gaps; the security page presents that engine as a real-time first-class Talos security capability without reflecting those caveats.
- The posture numbers on this page bypass the site’s existing claim guardrail entirely. Unlike the benchmark strip, these `99.9%`, `< 1ms`, and `100,000+` values are hard-coded directly in [site/marketing/src/app/security/page.tsx](site/marketing/src/app/security/page.tsx) rather than sourced from [site/marketing/src/content/claims.json](site/marketing/src/content/claims.json). In this audit, `npm run validate:claims` passed, but [site/marketing/src/lib/validate-claims.ts](site/marketing/src/lib/validate-claims.ts) cannot verify numbers that never enter the validated claim set.
- The result is a public-facing security page that looks more rigorously grounded than the current repo state and validation flow actually support.

Paths:
- `site/marketing/src/app/security/page.tsx`
- `site/dashboard/src/app/login/page.tsx`
- `site/dashboard/src/app/signup/page.tsx`
- `services/ai-gateway/app/middleware/auth_public.py`
- `services/ai-gateway/README.md`
- `services/mcp-connector/src/talos_mcp/transport/talos_tunnel.py`
- `services/aiops/api/src/main.py`
- `site/marketing/src/lib/validate-claims.ts`
- `site/marketing/src/content/claims.json`

Next step:
- Narrow the security page to claims the current shipped stack can actually support, or move those guarantees onto the same source-backed claim pipeline as the benchmark strip. If the stronger posture story is meant to remain public, finish the missing MCP secure-tunnel, auth-surface, AIOps productization, and claim-validation follow-through that would make the page defensible.

### 42. Vulnerability Disclosure Channel and Security Policy Parity

Status: `in_progress`

Why it is still open:
- Talos currently presents different vulnerability-reporting instructions depending on which public surface the user reads. The root repo policy in [SECURITY.md](SECURITY.md) tells reporters to email `reach@talosprotocol.com`, and [README.md](README.md) also lists `reach@talosprotocol.com` for `Security Vulnerabilities`.
- The public marketing/security surfaces do not match that. [site/marketing/src/app/security/page.tsx](site/marketing/src/app/security/page.tsx), [site/marketing/src/app/security/disclosure/page.tsx](site/marketing/src/app/security/disclosure/page.tsx), and the shipped [site/marketing/public/.well-known/security.txt](site/marketing/public/.well-known/security.txt) all route vulnerability reports to `security@talosprotocol.com` instead.
- That is not just a copy inconsistency; it affects the repo’s trust surface and operator expectations. A researcher following the root repository policy will contact a different mailbox than a researcher following the public site or `security.txt`, and the disclosure page explicitly positions `/.well-known/security.txt` as the authoritative encrypted reporting path.
- The root `SECURITY.md` also has a version-support section that does not line up cleanly with the rest of the repo’s current versioning language. Its `Supported Versions` table lists `5.15.x` as supported and `3.x` as unsupported, which does not match the repository’s current Talos release framing and reads like stale imported policy content rather than a maintained support statement.
- The result is that Talos still lacks one clearly owned, repo-consistent responsible-disclosure policy surface spanning the root repository, public marketing site, and machine-readable `security.txt` metadata.

Paths:
- `SECURITY.md`
- `README.md`
- `site/marketing/src/app/security/page.tsx`
- `site/marketing/src/app/security/disclosure/page.tsx`
- `site/marketing/public/.well-known/security.txt`

Next step:
- Choose one authoritative disclosure contact and one authoritative support/version policy, then propagate that consistently across [SECURITY.md](SECURITY.md), [README.md](README.md), the marketing disclosure pages, and `security.txt`. If encrypted reporting is officially supported, the root policy should explicitly say so instead of sending reporters to a different mailbox.

### 43. Marketing Developers Page SDK Example and Onboarding Parity

Status: `in_progress`

Why it is still open:
- The public developers page in [site/marketing/src/app/developers/page.tsx](site/marketing/src/app/developers/page.tsx) currently presents SDK onboarding examples that do not match the actual exported APIs. In the TypeScript example, it imports `Wallet, Client` from `@talosprotocol/sdk`, then calls `await Wallet.create()` and `wallet.signCapability(...)`.
- The current TypeScript SDK does not expose that API shape. [sdks/typescript/packages/sdk/src/core/wallet.ts](sdks/typescript/packages/sdk/src/core/wallet.ts) defines `Wallet.generate()` and `Wallet.fromSeed()`, not `Wallet.create()`. The package exports [TalosClient](sdks/typescript/packages/sdk/src/core/client.ts) from [sdks/typescript/packages/sdk/src/index.ts](sdks/typescript/packages/sdk/src/index.ts), not a `Client` symbol, and capability signing is the standalone [signCapability](sdks/typescript/packages/sdk/src/core/capability.ts) function rather than a wallet instance method.
- The Python example on that same page is also stale. It shows `wallet = Wallet.create()` and `cap = wallet.sign_capability(...)`, but the real Python SDK wallet in [sdks/python/src/talos_sdk/wallet.py](sdks/python/src/talos_sdk/wallet.py) exposes `Wallet.generate()` / `Wallet.from_seed()` and this audit did not find a `sign_capability` wallet method anywhere in [sdks/python/src/talos_sdk](sdks/python/src/talos_sdk). The package-level examples in [sdks/python/src/talos_sdk/__init__.py](sdks/python/src/talos_sdk/__init__.py) also use `Wallet.generate(...)` and `TalosClient`.
- This is a public developer-onboarding issue, not just an internal doc mismatch. A user following the marketing page’s sample code will hit missing-symbol or missing-method failures before they even reach the real protocol examples in the SDK READMEs.
- The page also labels the docs link as `Documentation Wiki` even though the repo now has first-class monorepo docs under `docs/`, which reinforces that the developers page is drifting behind the current source-backed onboarding path.

Paths:
- `site/marketing/src/app/developers/page.tsx`
- `sdks/typescript/packages/sdk/src/index.ts`
- `sdks/typescript/packages/sdk/src/core/wallet.ts`
- `sdks/typescript/packages/sdk/src/core/client.ts`
- `sdks/typescript/packages/sdk/src/core/capability.ts`
- `sdks/typescript/README.md`
- `sdks/python/src/talos_sdk/wallet.py`
- `sdks/python/src/talos_sdk/__init__.py`

Next step:
- Replace the public developers-page examples with code copied from the current SDK README/API surfaces, and keep that page aligned with one owned onboarding source per SDK. If the marketing page wants shortened examples, they should still use real exported symbols and current method names from the shipped packages.

### 44. Public UCP Commerce Positioning and Connector Reality Parity

Status: `in_progress`

Why it is still open:
- The homepage UCP callout in [site/marketing/src/components/UCPFeature.tsx](site/marketing/src/components/UCPFeature.tsx) presents a broad product story: “Talos now connects AI agents to the real-world economy through UCP. Discover, negotiate, and transact securely with thousands of merchants.” The public product catalog in [site/marketing/src/content/products.json](site/marketing/src/content/products.json) reinforces that with `Talos UCP Connector` as a `Beta` primary product whose outcome is `Policy-enforced, autonomous commerce with opaque payment handling.`
- The current connector implementation is materially narrower. The domain service in [services/ucp-connector/src/talos_ucp_connector/domain/services.py](services/ucp-connector/src/talos_ucp_connector/domain/services.py) orchestrates a checkout lifecycle for one explicit `merchant_domain` at a time; discovery is just a fetch of `https://{merchant_domain}/.well-known/ucp`, and requests fail closed unless the merchant is already allowlisted. That is not a repo-backed “thousands of merchants” discovery surface.
- The connector also does not yet support the richer public commerce story implied by “negotiation” and polished autonomous payments. The active payment adapter in [services/ucp-connector/src/talos_ucp_connector/adapters/outbound/payment.py](services/ucp-connector/src/talos_ucp_connector/adapters/outbound/payment.py) returns a fixed `sandbox_token`, the config/audit adapter in [services/ucp-connector/src/talos_ucp_connector/adapters/infrastructure/persistence.py](services/ucp-connector/src/talos_ucp_connector/adapters/infrastructure/persistence.py) is still an in-memory config store plus stdout audit emission, and the domain service still has a `TODO` to map failures to the UCP error taxonomy.
- The exposed MCP tool surface is checkout-only rather than a broader commerce network. [services/ucp-connector/src/talos_ucp_connector/adapters/inbound/mcp_server.py](services/ucp-connector/src/talos_ucp_connector/adapters/inbound/mcp_server.py) only exposes `ucp_checkout_create|get|update|complete|cancel`, with a fixed dev config that allowlists `merchant.example.com` and defaults `platform_profile_uri` / signing config to local prototype values.
- Test coverage reinforces that this is still closer to a constrained connector prototype than a verified merchant-network product. The “live” flow in [services/ucp-connector/tests/test_live.py](services/ucp-connector/tests/test_live.py) is still a mocked merchant-profile and checkout session test rather than a real interoperable UCP ecosystem verification.
- The result is a public commerce positioning surface that is ahead of the currently verified connector scope and runtime realism.

Paths:
- `site/marketing/src/components/UCPFeature.tsx`
- `site/marketing/src/content/products.json`
- `services/ucp-connector/src/talos_ucp_connector/domain/services.py`
- `services/ucp-connector/src/talos_ucp_connector/adapters/inbound/mcp_server.py`
- `services/ucp-connector/src/talos_ucp_connector/adapters/outbound/payment.py`
- `services/ucp-connector/src/talos_ucp_connector/adapters/infrastructure/persistence.py`
- `services/ucp-connector/tests/test_live.py`
- `services/ucp-connector/README.md`

Next step:
- Narrow the public UCP copy to the connector’s actual current scope, or finish the missing merchant-discovery, negotiation, payment, audit, and error-taxonomy work that would justify the broader commerce claims. If UCP remains checkout-only and allowlist-driven for now, the homepage and product catalog should say that directly.

### 45. Marketing Roadmap Versioning and “Live” Status Parity

Status: `in_progress`

Why it is still open:
- The public roadmap page in [site/marketing/src/app/roadmap/page.tsx](site/marketing/src/app/roadmap/page.tsx) presents a self-contained product-status story that does not line up with the repo’s other status anchors. It labels `v2.0 Alpha` as `LIVE` and frames `v2.0 Beta` as a `Q3 2026` next step.
- The repo-owned roadmap material tells a different story. [docs/research/roadmap.md](docs/research/roadmap.md) describes the current release as `5.15.2 (LTS)` in February 2026, marks Phases `1-15` broadly complete, and places `Zero-Knowledge Audit` in Phase `17` as planned. That means the public marketing roadmap is not just simplifying the roadmap; it is using a conflicting version line and milestone framing.
- The specific feature bullets on the marketing roadmap also overstate what is currently verified in code. It marks `Decentralized Identity: DID/DHT Support` as part of the `LIVE` tranche, but external DID resolution in [src/core/did.py](src/core/did.py) is still a placeholder that logs the DID and returns `None` with a `TODO` for DHT lookup. The same page places `Onion Routing`, `Hybrid Kyber-768 encryption`, and `Zero-Knowledge` in the near-term beta section, while the repo’s own research docs still describe those capabilities as future/planned work in [docs/research/future-improvements.md](docs/research/future-improvements.md) and [docs/research/roadmap.md](docs/research/roadmap.md).
- Because the marketing roadmap has a public `LIVE` badge and concrete quarter-based promises, this is a stronger trust-surface issue than a casual marketing simplification. External readers are being shown a product/version timeline that conflicts with both the repo-owned roadmap and known implementation gaps already tracked elsewhere.

Paths:
- `site/marketing/src/app/roadmap/page.tsx`
- `docs/research/roadmap.md`
- `docs/research/future-improvements.md`
- `src/core/did.py`

Next step:
- Choose one authoritative roadmap/versioning surface for external users. Either align the marketing roadmap to the repo-owned roadmap and currently verified implementation state, or explicitly label it as aspirational/high-level. In particular, remove `LIVE` status from features that still depend on placeholder DHT resolution or future-technology tracks like onion routing, Kyber hybrid encryption, and zero-knowledge audit.

### 46. Dashboard Legacy WebSocket Stream Boundary and Auth Containment

Status: `in_progress`

Why it is still open:
- The dashboard still ships a legacy WebSocket data path that bypasses the server-side `/api/*` boundary the rest of the app now presents as canonical. [site/dashboard/src/lib/data/WsDataSource.ts](site/dashboard/src/lib/data/WsDataSource.ts) opens a browser WebSocket directly to `ws://localhost:8000/api/events/stream` by default and injects a capability from `NEXT_PUBLIC_TALOS_CAPABILITY`.
- That direct browser path conflicts with the dashboard’s current approved server-side stream shape. [site/dashboard/src/app/api/audit/stream/route.ts](site/dashboard/src/app/api/audit/stream/route.ts) explicitly says it is the `ONLY approved path for audit event streaming`, and [site/dashboard/src/app/api/events/route.ts](site/dashboard/src/app/api/events/route.ts) says the same for paginated audit event fetching. The active HTTP/SSE data path already uses those proxies.
- The runtime config also no longer treats WebSocket mode as a first-class supported mode. [site/dashboard/src/lib/config.ts](site/dashboard/src/lib/config.ts) only types `MOCK | HTTP`, while the generic data-source factory in [site/dashboard/src/lib/data/DataSource.ts](site/dashboard/src/lib/data/DataSource.ts) can still instantiate `WS`, `LIVE`, and `SQLITE` branches. That means the app still carries a legacy stream mode that is neither part of the narrowed runtime config nor clearly retired.
- The old WebSocket client is coupled to the legacy `services/gateway` stream protocol rather than the current audit-service-backed path. [site/dashboard/src/lib/data/WsClient.ts](site/dashboard/src/lib/data/WsClient.ts) expects the custom handshake/heartbeat protocol served by [services/gateway/src/handlers/stream.py](services/gateway/src/handlers/stream.py), including `init`, `init_ack`, `heartbeat`, and capability-style auth errors. That is a different trust boundary from the current SSE proxy model.
- Because the capability is sourced from a `NEXT_PUBLIC_*` variable and the connection is direct from the browser, this leftover path is not just unused code clutter; it preserves a path where a public client can be configured to bypass the Next.js auth/proxy surface and talk to a legacy gateway stream contract directly.

Paths:
- `site/dashboard/src/lib/data/WsDataSource.ts`
- `site/dashboard/src/lib/data/WsClient.ts`
- `site/dashboard/src/lib/data/DataSource.ts`
- `site/dashboard/src/lib/config.ts`
- `site/dashboard/src/app/api/audit/stream/route.ts`
- `site/dashboard/src/app/api/events/route.ts`
- `services/gateway/src/handlers/stream.py`

Next step:
- Decide whether the dashboard still officially supports a direct WebSocket mode. If not, remove or hard-disable the `WsDataSource` / `WsClient` path and keep the browser behind the approved `/api/audit/stream` and `/api/events` proxies. If WebSocket mode is still intended, re-own it under the current dashboard auth and runtime-config model instead of exposing a legacy direct-browser capability path.

### 47. DID/DHT User-Facing API and Example Parity

Status: `in_progress`

Why it is still open:
- The repo currently presents DID resolution through two different user-facing paths that do not line up cleanly. The main DID module in [src/core/did.py](src/core/did.py) still exposes `resolve_did()` as a placeholder that logs the DID and returns `None`, while the public identity docs in [docs/features/identity/dids-dht.md](docs/features/identity/dids-dht.md) describe DID resolution via DHT as an implemented Talos feature.
- The public examples reinforce that split. [examples/05_did.py](examples/05_did.py) focuses on DID document creation and local serialization only, while [examples/06_dht.py](examples/06_dht.py) demonstrates `DIDResolver.publish()` / `resolve()` directly against a local `DHTNode`. That means the repo has a low-level DHT demo path, but not a coherent higher-level DID API that matches the docs’ “resolve DIDs via DHT” framing.
- The DHT example and docs are also more local-demo-oriented than the broader identity story suggests. [examples/06_dht.py](examples/06_dht.py) publishes and resolves a DID document against the same local node and uses fabricated bootstrap nodes for illustration, which is useful as an internal primitive demo but not equivalent to a verified decentralized identity resolution path across a real Talos network.
- The result is a user-facing identity surface where the docs present DID+DHT as a complete integrated capability, the low-level DHT resolver exists, but the canonical core DID API and higher-level examples do not yet converge on one supported end-to-end resolution story.

Paths:
- `src/core/did.py`
- `src/network/dht.py`
- `docs/features/identity/dids-dht.md`
- `docs/sdk/usage-examples.md`
- `examples/05_did.py`
- `examples/06_dht.py`

Next step:
- Decide which API is the supported DID resolution entrypoint. If DHT-backed DID resolution is meant to be real today, wire the core DID API to the DHT resolver, update examples to show a real supported flow, and add end-to-end verification beyond same-node publish/resolve demos. If it remains experimental, narrow the identity docs and examples so they clearly read as low-level primitives or prototype workflows rather than a finished decentralized identity surface.

### 48. Examples, Demo Command, and Python Onboarding API Parity

Status: `in_progress`

Why it is still open:
- The repo’s examples index no longer matches the examples that are actually checked in. [examples/README.md](examples/README.md) still describes the examples repo as the canonical home for “simple chatbots, multi-agent swarms, and infrastructure automation,” lists modules named `devops-agent`, `multi-agent`, and `chat`, and tells users to run `cd devops-agent && ./scripts/demo.sh`. The real tree under [examples](examples) does include [examples/devops-agent](examples/devops-agent) and [examples/secure_chat](examples/secure_chat), but there is no `examples/multi-agent` directory, and there is also a shipped [examples/ucp-merchant](examples/ucp-merchant) surface that the README never acknowledges.
- The examples metadata and validation path are stale in ways that hide the drift instead of catching it. [examples/examples_manifest.json](examples/examples_manifest.json) only advertises `secure-chat` and `devops-agent`, while [examples/scripts/test.sh](examples/scripts/test.sh) still iterates `multi-agent/scripts/*.sh` and ignores the secure-chat and UCP example trees entirely. Running that repo-owned check currently exits successfully even though the README/module list no longer matches the actual example layout.
- The getting-started/demo docs still teach a one-command and high-level local-agent surface that the current shipped CLI does not implement. [docs/getting-started/one-command-demo.md](docs/getting-started/one-command-demo.md) is marked `status: Implemented` and tells users to run `talos demo`, but the root entrypoint in [pyproject.toml](pyproject.toml) still maps `talos` to [src/client/cli.py](src/client/cli.py), whose commands are the older `init`, `register`, `send`, `listen`, `peers`, `status`, and related P2P flows. There is no `demo` command in that CLI.
- The same onboarding docs also present a Python API that does not match the shipped SDK surface. [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md), [docs/getting-started/one-command-demo.md](docs/getting-started/one-command-demo.md), and many adjacent docs still show `pip install talos-protocol`, `from talos import TalosClient`, `TalosClient.create("my-agent")`, `client.get_prekey_bundle()`, `client.establish_session(...)`, `client.verify_proof(...)`, `client.grant_capability(...)`, and `client.invoke_tool(...)`. The actual Python SDK in [sdks/python/src/talos_sdk/client.py](sdks/python/src/talos_sdk/client.py) exposes a much narrower gateway client initialized as `TalosClient(gateway_url, wallet)` with methods like `connect()`, `sign_and_send_mcp()`, `sign_http_request()`, and `close()`. It does not define `create`, session-establishment helpers, proof-verification helpers, or the high-level capability/tool API that the docs describe.
- The package/import story is also inconsistent across the onboarding material. [sdks/python/src/talos_sdk/__init__.py](sdks/python/src/talos_sdk/__init__.py) exports `TalosClient` from the `talos_sdk` package, while the root package in [pyproject.toml](pyproject.toml) publishes `talos-protocol` with the `talos` CLI entrypoint, not a documented `from talos import TalosClient` import surface. That means the current quickstarts are not just simplified; they describe an SDK/CLI product shape that is materially different from the code that ships.
- This leaves developers with an unreliable first-run path: the examples catalog is partially stale, the validation script does not guard the documented layout, and the “implemented” quickstart/demo pages still point to commands and Python methods that are not present in the current repo.

Paths:
- `examples/README.md`
- `examples/examples_manifest.json`
- `examples/scripts/test.sh`
- `examples/devops-agent`
- `examples/secure_chat`
- `examples/ucp-merchant`
- `docs/getting-started/one-command-demo.md`
- `docs/getting-started/quickstart.md`
- `pyproject.toml`
- `src/client/cli.py`
- `sdks/python/src/talos_sdk/client.py`
- `sdks/python/src/talos_sdk/__init__.py`
- `docs/sdk/python-sdk.md`

Next step:
- Choose one truthful onboarding surface and make the examples and docs converge on it. Either implement the documented `talos demo` and high-level local-agent Python API, or rewrite the examples index and getting-started pages around the currently shipped CLI and `talos_sdk` gateway client. The examples validation script should also be updated so it actually covers the examples that exist today and fails when the catalog drifts again.

### 49. Contributor Workflow, Makefile, and Test-Runner Command Parity

Status: `completed`

What was completed:
- The root test path now points at the real runner. [Makefile](Makefile) no longer calls a non-existent repo-root `./run_all_tests.sh`; it now shells into [deploy/scripts/run_all_tests.sh](deploy/scripts/run_all_tests.sh) and accepts scoped `TEST_ARGS`, so `make test` and targeted invocations such as `make test TEST_ARGS="--only talos-contracts"` resolve through one canonical entrypoint.
- The test runner now owns the documented flag surface. [deploy/scripts/run_all_tests.sh](deploy/scripts/run_all_tests.sh) is now a thin wrapper over [deploy/scripts/run_all_tests.py](deploy/scripts/run_all_tests.py), which implements `--help`, `--ci`, `--full`, `--changed`, `--required-only`, `--only`, `--skip-build`, `--with-live`, and `--smoke`. It selects components from [deploy/submodules.json](deploy/submodules.json), prefers `.agent/test_manifest.yml` when present, and otherwise falls back to owned entrypoints such as `scripts/test.sh`, `make test`, `npm test`, or `pytest`.
- The contributor docs now describe the actual workflow instead of promising uniform Makefile parity across every component. [docs/guides/development.md](docs/guides/development.md) and [docs/getting-started/getting-started.md](docs/getting-started/getting-started.md) now present the root runner and root `Makefile` as the default workspace entrypoints, document the real runner flags, and explicitly note that some components use `scripts/test.sh` or framework-native commands instead of a shared per-repo Makefile contract.
- Verification in this pass confirmed the repaired command path and CLI surface. `bash deploy/scripts/run_all_tests.sh --help` now prints the supported runner options, and `make test TEST_ARGS='--only talos-contracts --ci'` now reaches the real runner instead of failing on a missing script. That targeted contracts slice still fails two pre-existing digest-parity tests in [contracts/python/tests/test_tga_digest.py](contracts/python/tests/test_tga_digest.py), but the failure is inside the selected component tests rather than in the root workflow wiring.

Paths:
- `docs/guides/development.md`
- `docs/getting-started/getting-started.md`
- `Makefile`
- `deploy/scripts/run_all_tests.sh`
- `deploy/scripts/run_all_tests.py`
- `deploy/submodules.json`
- `services/configuration/README.md`
- `site/dashboard/Makefile`
- `services/ai-gateway/Makefile`

Next step:
- None for this tracker item. Any remaining contributor-experience drift should be tracked under the still-open service- and docs-specific items rather than reopening the root runner path that is now wired and documented.

### 50. Marketing Product CTA, Source Link, and Ownership Parity

Status: `in_progress`

Why it is still open:
- The public marketing product catalog now behaves like a product-entry surface, but its actions do not line up cleanly with the actual shipped ownership and start paths. [site/marketing/src/components/products/ProductCard.tsx](site/marketing/src/components/products/ProductCard.tsx) renders the primary CTA directly from each product’s `docs_url` and the secondary CTA directly from `repos[0].url`, and the product detail page in [site/marketing/src/app/products/[id]/page.tsx](site/marketing/src/app/products/[id]/page.tsx) repeats that same pattern. That means labels such as `Deployment Guide`, `Self-Host`, `Setup Service`, `Start Transacting`, `Deploy Agent`, `Start Chatting`, and `Get Started` are not backed by product-specific onboarding flows; they just open a static doc URL and a GitHub URL from JSON.
- Several of those action labels materially overstate what the links actually do. In [site/marketing/src/content/products.json](site/marketing/src/content/products.json), `talos-ai-chat-agent` uses `cta_primary: "Start Chatting"` but links to `docs/sdk/examples.md`, `talos-aiops` uses `cta_primary: "Deploy Agent"` but links to `docs/features/observability/observability.md`, and `talos-setup-helper` uses `cta_primary: "Install Agent"` but links to the generic getting-started quickstart rather than a setup-helper-owned install path. Those are documentation links, not runnable product entrypoints.
- The secondary “source” actions also preserve older standalone-repo identities that no longer match the current visible product ownership story. The product catalog points users to repositories like `https://github.com/talosprotocol/talos-gateway`, `talos-dashboard`, `talos-audit-service`, `talos-mcp-connector`, `talos-aiops`, `talos-ai-chat-agent`, `talos-contracts`, `talos-core-rs`, `talos-sdk-ts`, and `talos-sdk-py`, while the current repo increasingly presents Talos as a consolidated workspace with those components living under paths like `services/`, `sdks/`, `site/`, and `tools/`. The only product already linking to a monorepo path is `talos-setup-helper`, which points to `https://github.com/talosprotocol/talos/tree/main/tools/setup-helper`.
- Because the cards and detail pages render these links verbatim, this is not just stale metadata sitting in a JSON file. The public site actively presents those repo/doc links as the canonical “learn more / start here / source” actions for each product, even though other repo docs and tracker items already show the ownership boundary, gateway topology, and onboarding surface are still in flux.
- The result is a product catalog that looks more actionable and productized than it really is. External users are shown polished CTA labels and source buttons, but the site does not distinguish between “read the docs,” “open the monorepo source path,” and “launch or install this product,” so the current public action surface is ahead of the verified product-entry reality.

Paths:
- `site/marketing/src/content/products.json`
- `site/marketing/src/components/products/ProductCard.tsx`
- `site/marketing/src/app/products/page.tsx`
- `site/marketing/src/app/products/[id]/page.tsx`
- `site/marketing/src/app/solutions/page.tsx`

Next step:
- Decide what the marketing catalog is supposed to be: a documentation directory, a source-code index, or a true product-launch surface. Then align the CTA labels and destinations with that choice. If the site only has docs and source today, say that directly and link to the current monorepo paths or owned docs. If it wants “Start Chatting,” “Deploy Agent,” or “Install Agent” style actions, those need real product-specific onboarding flows rather than generic blob links.

### 51. Marketing Docs and Whitepaper Discovery Surface Parity

Status: `completed`

The marketing site now has a coherent docs and whitepaper discovery surface.
- Updated `site/marketing/src/components/Navbar.tsx` with unified links for Roadmap and Whitepaper.
- Created `site/marketing/src/app/protocol/page.tsx` as a dedicated landing page for the protocol/whitepaper.
- Aligned "Whitepaper" destinations to the canonical `PROTOCOL.md` via the new landing page.

Paths:
- `site/marketing/src/app/docs/speed-insights/page.tsx`
- `site/marketing/src/components/Navbar.tsx`
- `site/marketing/src/components/Hero.tsx`
- `site/marketing/src/app/page.tsx`
- `site/marketing/src/app/security/page.tsx`
- `site/marketing/src/app/developers/page.tsx`
- `site/marketing/src/app/solutions/page.tsx`
- `site/marketing/src/content/products.json`
- `docs/research/whitepaper.md`
- `docs/security/security-properties.md`

Next step:
- Decide whether the marketing site should own a Talos docs/whitepaper discovery experience or intentionally hand users off to GitHub. If it should own that experience, replace the unrelated `/docs/speed-insights` scaffold, create one canonical docs/whitepaper entry path, and make the navbar, homepage, security page, developers page, solutions page, and product catalog all point to the same owned information architecture. If GitHub remains the destination, remove the misleading internal `/docs` presence and stop labeling different documents as the same `Whitepaper`.

### 52. Marketing Availability and Lifecycle Messaging Consistency

Status: `in_progress`

Why it is still open:
- The public marketing site currently tells incompatible stories about whether Talos is broadly available, early-access only, or still private beta. The contact page in [site/marketing/src/app/contact/page.tsx](site/marketing/src/app/contact/page.tsx) says, “We are currently in private beta with select partners,” and labels engineering support as help for “early adopters.”
- That private-beta framing conflicts with the rest of the site’s public lifecycle signals. The roadmap page in [site/marketing/src/app/roadmap/page.tsx](site/marketing/src/app/roadmap/page.tsx) marks `v2.0 Alpha` as `LIVE`, while the product catalog in [site/marketing/src/content/products.json](site/marketing/src/content/products.json) and [site/marketing/src/app/products/page.tsx](site/marketing/src/app/products/page.tsx) marks multiple products as `Stable`, including the dashboard, audit service, MCP connector, secure chat, contracts, core Rust, and several SDKs.
- The commercial services page reinforces a production-ready posture rather than a private-beta one. [site/marketing/src/app/services/page.tsx](site/marketing/src/app/services/page.tsx) promises that Talos can make infrastructure “secure, performant, and compliant from day one,” describes an implementation tier where “You ship a hardened Talos stack in your environment,” and presents a rollout phase with “Full production deployment with ongoing security monitoring.”
- The broader marketing chrome also reads as generally available/open rather than beta-gated. The homepage footer in [site/marketing/src/app/page.tsx](site/marketing/src/app/page.tsx) presents Talos simply as `Open Source (Apache-2.0)`, and the main CTA in [site/marketing/src/components/Hero.tsx](site/marketing/src/components/Hero.tsx) is `Get Started`, not a waitlist, beta access, or partner-only onboarding flow.
- This creates a public trust-surface inconsistency even before any code-level verification question: one marketing page tells visitors they need to be a select private-beta partner, while other public pages simultaneously present Talos as live, stable, self-hostable, open-source, and ready for production rollout. That makes it unclear what a user is actually supposed to believe about current availability and support level.

Paths:
- `site/marketing/src/app/contact/page.tsx`
- `site/marketing/src/app/roadmap/page.tsx`
- `site/marketing/src/content/products.json`
- `site/marketing/src/app/products/page.tsx`
- `site/marketing/src/app/services/page.tsx`
- `site/marketing/src/app/page.tsx`
- `site/marketing/src/components/Hero.tsx`

Next step:
- Choose one truthful external availability story and apply it consistently across the site. If Talos is still private beta, remove or qualify `LIVE`, `Stable`, `Self-Host`, and production-rollout language. If the project is openly available and self-hostable, remove the “private beta with select partners” and “early adopters” framing or scope it narrowly to specific commercial/support programs instead of the whole product.

### 53. Docs Index and Internal Link-Hygiene Parity

Status: `completed`

What was completed:
- The broken and machine-local links in the active docs tree were normalized to portable repo-relative targets. [docs/README.md](docs/README.md), [docs/README-Home.md](docs/README-Home.md), [docs/security/security-properties.md](docs/security/security-properties.md), [docs/architecture/protocol-guarantees.md](docs/architecture/protocol-guarantees.md), [docs/architecture/simplified.md](docs/architecture/simplified.md), [docs/guides/deployment.md](docs/guides/deployment.md), [docs/guides/production-hardening.md](docs/guides/production-hardening.md), and [docs/features/authorization/capability-authorization.md](docs/features/authorization/capability-authorization.md) now point at current repo paths instead of missing wiki-era targets or `file:///Users/...` links.
- The missing Rust SDK docs target was filled in with [docs/sdk/rust-sdk.md](docs/sdk/rust-sdk.md), which gives the docs index a real owned target for the shipped Rust SDK surface instead of linking to a non-existent page.
- The same cleanup was applied to docs-adjacent workflow/templates content under [docs/.agent/workflows/development/tga-workflow.md](docs/.agent/workflows/development/tga-workflow.md), [docs/.agent/workflows/pending-features.md](docs/.agent/workflows/pending-features.md), and [docs/templates/contributing-template.md](docs/templates/contributing-template.md), removing machine-specific links and broken relative references there as well.
- The repo-owned link checker now validates the real docs tree. [check_links.py](check_links.py) no longer scans only `docs/wiki`; it now walks `docs/**/*.md`, strips fenced code blocks before matching Markdown links, flags `file://` links, and resolves relative targets against each document’s parent directory.
- Verification in this pass brought the docs-tree scan to zero known issues. Both `python3 check_links.py` and a separate read-only recursive link audit over `docs/**/*.md` returned clean results after the fixes.

Paths:
- `docs/README.md`
- `docs/README-Home.md`
- `docs/sdk/rust-sdk.md`
- `docs/security/security-properties.md`
- `docs/architecture/protocol-guarantees.md`
- `docs/architecture/simplified.md`
- `docs/guides/deployment.md`
- `docs/guides/production-hardening.md`
- `docs/features/authorization/capability-authorization.md`
- `docs/.agent/workflows/development/tga-workflow.md`
- `docs/.agent/workflows/pending-features.md`
- `docs/templates/contributing-template.md`
- `check_links.py`

Next step:
- None for this tracker item. Remaining docs work should now focus on content truthfulness and status-claim parity rather than broken local navigation and machine-specific link paths.

### 54. Dashboard Shell Navigation and Stranded Configuration UI Parity

Status: `in_progress`

Why it is still open:
- The authenticated dashboard shell currently ships navigation links to routes that do not exist. [site/dashboard/src/components/layout/DashboardSidebar.tsx](site/dashboard/src/components/layout/DashboardSidebar.tsx) is wired into the active shell layout via [site/dashboard/src/app/(shell)/layout.tsx](site/dashboard/src/app/(shell)/layout.tsx) and renders `Settings` at `/settings` plus `Docs` at `/docs`, but the current route inventory under [site/dashboard/src/app](site/dashboard/src/app) does not include either `/settings` or `/docs`.
- The repo also still carries a second, separate configuration/UCP navigation surface that points at an even larger set of nonexistent routes. [site/dashboard/src/components/configuration/layout/sidebar.tsx](site/dashboard/src/components/configuration/layout/sidebar.tsx) renders a `Talos UCP` sidebar with links to `/policies`, `/merchants`, `/transactions`, `/api-explorer`, `/settings`, and `/help`, and its companion top bar in [site/dashboard/src/components/configuration/layout/top-bar.tsx](site/dashboard/src/components/configuration/layout/top-bar.tsx) advertises search over “merchants, policies, transactions.” None of those page routes exist in the current dashboard app tree.
- The stranded configuration feature code behind that nav stack is also still partially mock-backed and points at missing APIs. [site/dashboard/src/features/configuration/adapters/api-adapter.ts](site/dashboard/src/features/configuration/adapters/api-adapter.ts) returns a hard-coded `merchant.example.com` record from `getMerchants()` and posts policy updates to `/api/policies`, but this pass did not find any `site/dashboard/src/app/api/policies` route. [site/dashboard/src/features/configuration/view-models/use-merchants.ts](site/dashboard/src/features/configuration/view-models/use-merchants.ts) still builds state around that adapter even though the active configuration page in [site/dashboard/src/app/(shell)/configuration/page.tsx](site/dashboard/src/app/(shell)/configuration/page.tsx) now uses a different configuration-control flow.
- This is more than harmless dead code because the primary shell nav is live and the configuration cluster still looks productized. Users can reach the active shell on every authenticated page, and the repo still contains a second branded `Talos UCP` admin surface that implies merchant/policy workflows the current Next app does not actually route or serve.
- The result is a dashboard navigation model with unclear ownership and broken affordances: one active sidebar includes links that 404, while a parallel configuration/UCP UI stack still promises routes and APIs that no longer exist in the shipped dashboard.

Paths:
- `site/dashboard/src/app/(shell)/layout.tsx`
- `site/dashboard/src/components/layout/DashboardSidebar.tsx`
- `site/dashboard/src/components/configuration/layout/sidebar.tsx`
- `site/dashboard/src/components/configuration/layout/top-bar.tsx`
- `site/dashboard/src/app/(shell)/configuration/page.tsx`
- `site/dashboard/src/features/configuration/adapters/api-adapter.ts`
- `site/dashboard/src/features/configuration/view-models/use-merchants.ts`

Next step:
- Collapse the dashboard onto one owned navigation model. At minimum, remove or retarget the live shell links to missing `/settings` and `/docs` routes, and either fully retire the stranded `Talos UCP` sidebar/adapters or reintroduce those merchant/policy pages and APIs under a current supported route structure. The dashboard should not ship navigation to pages and endpoints that are absent from the app tree.

### 55. Docs Home Status Metrics and Architecture Framing Parity

Status: `in_progress`

Why it is still open:
- The docs landing page still publishes concrete project-health and readiness claims that are not supported by the current repo-owned evidence. [docs/README-Home.md](docs/README-Home.md) opens with `Talos v5.15 | Phase 15: Adaptive Budgets | 850+ Verified Tests | Multi-Repo Architecture` and then presents a “Project Health” block claiming `850+` tests with `100% Passing`, `92%` average coverage across services, `99.99%` uptime on testnet, and `Production Ready`.
- The checked-in coverage artifact does not support that `92% average across services` figure. The current root coverage summary in [artifacts/coverage/summary.json](artifacts/coverage/summary.json) includes line coverage values of `45.79%` for `talos-core-rs`, `81.30%` for `sdks-python`, `79.88%` for `sdks-typescript`, `96.27%` for `talos-contracts`, and `29.51%` for `services-ai-gateway`, which yields a simple average of about `66.55%`, not `92%`.
- The broader framing on that page is also stale relative to the current workspace shape. The same landing page still advertises `Multi-Repo Architecture`, while the current checkout is a mixed monorepo/submodule workspace and other docs already overstate the old multi-repo uniformity elsewhere in the tracker.
- The landing page also still presents `Production Ready` and `99.99%` uptime without an obvious current repo-owned source of truth for those figures. A repo sweep in this pass found those claims on [docs/README-Home.md](docs/README-Home.md) and `Production Ready` echoed in [.agent/status/current-phase.md](.agent/status/current-phase.md), but did not find a current published uptime artifact or a repo-owned health dashboard that would justify the docs-home metric block as a live factual status surface.
- Because [docs/README-Home.md](docs/README-Home.md) is a top-level onboarding page, this is not just a stale sentence inside a deep guide. New readers are being given specific health numbers and an architecture label that are ahead of the currently checked-in artifacts and contributor reality.

Paths:
- `docs/README-Home.md`
- `artifacts/coverage/summary.json`
- `.agent/status/current-phase.md`
- `docs/research/roadmap.md`
- `docs/guides/development.md`

Next step:
- Rework the docs-home hero and “Project Health” block so it only presents metrics and architecture labels with a current repo-owned source. If uptime or readiness is not continuously backed by shipped artifacts, remove the exact numbers and use a qualified status statement instead. Coverage and test counts should be derived from the current generated summary or omitted from the landing page entirely.

### 56. Marketing Verification Coverage and Drift-Gate Parity

Status: `in_progress`

Why it is still open:
- The public marketing app does have validation scripts, but they do not cover the full set of public surfaces that are currently drifting. [site/marketing/package.json](site/marketing/package.json) exposes `validate:claims`, `test:routes`, and `check:links`, and [site/marketing/scripts/ci-verify.sh](site/marketing/scripts/ci-verify.sh) runs those gates after a build.
- Those checks are materially narrower than the actual public surface. `validate:claims` only inspects [site/marketing/src/content/claims.json](site/marketing/src/content/claims.json) via [site/marketing/src/lib/validate-claims.ts](site/marketing/src/lib/validate-claims.ts). It does not validate [site/marketing/src/content/products.json](site/marketing/src/content/products.json), page-level status/maturity messaging, docs/whitepaper routing, or the public action labels rendered from that product metadata.
- The route smoke test also only covers a fixed shortlist. [site/marketing/scripts/smoke-test-routes.js](site/marketing/scripts/smoke-test-routes.js) checks `/`, `/developers`, `/security`, `/products`, `/services`, `/methodology`, `/roadmap`, `/contact`, and `/security/disclosure`. It does not directly cover `/solutions`, product detail pages under `/products/[id]`, or the stray internal docs route `/docs/speed-insights`.
- The link checker does not close that gap because it starts crawling from the served homepage. That means orphaned or effectively unlinked routes can still evade the check. In the current app, this matters because [site/marketing/src/app/docs/speed-insights/page.tsx](site/marketing/src/app/docs/speed-insights/page.tsx) is not linked from the main nav or homepage and therefore can remain unrelated Vercel scaffold content without being exercised by the current smoke-route set or guaranteed to be discovered by the root crawl.
- The result is a public-site verification model that is too narrow for the current amount of metadata- and page-driven product surface area. The repo can successfully validate `claims.json` while still shipping stale `products.json` entries, inconsistent availability/status copy, mismatched docs/whitepaper routes, and orphaned pages that no current gate explicitly owns.

Paths:
- `site/marketing/package.json`
- `site/marketing/scripts/ci-verify.sh`
- `site/marketing/scripts/smoke-test-routes.js`
- `site/marketing/src/lib/validate-claims.ts`
- `site/marketing/src/content/claims.json`
- `site/marketing/src/content/products.json`
- `site/marketing/src/app/docs/speed-insights/page.tsx`

Next step:
- Expand the marketing verification gates so they validate the actual public contract, not just benchmark claims. At minimum, add schema/consistency checks for `products.json`, route coverage for unlinked but shipped pages, and ownership checks for docs/whitepaper destinations. If certain pages are intentionally hidden or experimental, remove them from the shipped app or mark them so the validation story stays honest.

### 57. Dashboard Verification Coverage and Route-Integrity Gate Parity

Status: `in_progress`

Why it is still open:
- The dashboard repository does have local test and gate scripts, but they are not aimed at route or navigation integrity. [site/dashboard/package.json](site/dashboard/package.json) exposes `test`, `typecheck`, and `gates:contracts`, while [site/dashboard/scripts/test.sh](site/dashboard/scripts/test.sh) runs `npm ci`, lint, typecheck, Vitest, and build. None of those scripts perform route smoke tests, link crawling, or nav-to-route consistency checks comparable to the marketing app’s `test:routes` / `check:links` flow.
- The existing contract gate is intentionally narrow. [site/dashboard/scripts/gates-contracts.sh](site/dashboard/scripts/gates-contracts.sh) bans deep links, `btoa`/`atob`, and local reimplementations of contract helpers, but it does not validate whether the active shell navigation points at real pages or whether route metadata is internally consistent.
- The current test set also does not appear to exercise the shell navigation surfaces that are drifting. A test inventory in this pass found only [site/dashboard/src/__tests__/data/DataSource.test.ts](site/dashboard/src/__tests__/data/DataSource.test.ts), [site/dashboard/src/__tests__/integrity/cursor.test.ts](site/dashboard/src/__tests__/integrity/cursor.test.ts), [site/dashboard/src/features/configuration/templates.test.ts](site/dashboard/src/features/configuration/templates.test.ts), and [site/dashboard/src/lib/proxy.test.ts](site/dashboard/src/lib/proxy.test.ts). This pass did not find tests covering [site/dashboard/src/components/layout/DashboardSidebar.tsx](site/dashboard/src/components/layout/DashboardSidebar.tsx), [site/dashboard/src/components/layout/DashboardHeader.tsx](site/dashboard/src/components/layout/DashboardHeader.tsx), or the stranded configuration/UCP sidebar components.
- That gap matters because the repo is already shipping concrete route drift that these gates missed. The active shell sidebar still links to missing `/settings` and `/docs` pages, and the separate configuration/UCP sidebar still points at `/policies`, `/merchants`, `/transactions`, `/api-explorer`, and `/help` despite those routes being absent from the current app tree. Those findings can persist because the dashboard has no repo-owned check that compares the rendered nav surfaces against the reachable route inventory.
- The dashboard also carries two competing navigation ownership models without a guardrail to keep them aligned. [site/dashboard/src/lib/navRegistry.ts](site/dashboard/src/lib/navRegistry.ts) claims to be the “Single source of truth for all routes, labels, and hierarchy,” but the active shell in [site/dashboard/src/app/(shell)/layout.tsx](site/dashboard/src/app/(shell)/layout.tsx) uses the separate hard-coded [DashboardSidebar.tsx](site/dashboard/src/components/layout/DashboardSidebar.tsx) instead. Without tests or lint rules around that boundary, route drift is easy to introduce and hard to detect.

Paths:
- `site/dashboard/package.json`
- `site/dashboard/scripts/test.sh`
- `site/dashboard/scripts/gates-contracts.sh`
- `site/dashboard/src/__tests__/data/DataSource.test.ts`
- `site/dashboard/src/__tests__/integrity/cursor.test.ts`
- `site/dashboard/src/features/configuration/templates.test.ts`
- `site/dashboard/src/lib/proxy.test.ts`
- `site/dashboard/src/components/layout/DashboardSidebar.tsx`
- `site/dashboard/src/components/layout/DashboardHeader.tsx`
- `site/dashboard/src/lib/navRegistry.ts`
- `site/dashboard/src/app/(shell)/layout.tsx`

Next step:
- Add a dashboard-owned route/nav integrity gate. At minimum, compare the current app route inventory against the active shell links and the declared nav registry, and fail CI when the dashboard ships links to missing pages. If the project wants one canonical route registry, the active shell should consume it or there should be a test that proves the hard-coded shell and registry stay in sync.

### 58. Dashboard Shell Ownership and Version-Surface Parity

Status: `in_progress`

Why it is still open:
- The dashboard still carries two competing shell implementations with different navigation and status models. The active authenticated app uses [site/dashboard/src/app/(shell)/layout.tsx](site/dashboard/src/app/(shell)/layout.tsx), which renders [DashboardHeader.tsx](site/dashboard/src/components/layout/DashboardHeader.tsx), [DashboardSidebar.tsx](site/dashboard/src/components/layout/DashboardSidebar.tsx), and [DashboardFooter.tsx](site/dashboard/src/components/layout/DashboardFooter.tsx). Separately, the repo still ships [site/dashboard/src/components/layout/AppShell.tsx](site/dashboard/src/components/layout/AppShell.tsx), which implements a different sidebar, top bar, breadcrumb model, global-status polling flow, and documentation link strategy built around [site/dashboard/src/lib/navRegistry.ts](site/dashboard/src/lib/navRegistry.ts).
- That second shell appears to be effectively orphaned. A repo sweep in this pass found the `AppShell` definition but did not find any current imports of it from the active app tree. The nav registry likewise claims to be the “Single source of truth for all routes, labels, and hierarchy,” but the live shell does not consume it; it uses the separate hard-coded `DashboardSidebar` instead.
- The user-facing version surface is already drifting because of that split. The active footer in [site/dashboard/src/components/layout/DashboardFooter.tsx](site/dashboard/src/components/layout/DashboardFooter.tsx) hard-codes `v0.1.0`, while the package metadata in [site/dashboard/package.json](site/dashboard/package.json) is `0.1.27`. The unused `AppShell` has yet another version source, `NEXT_PUBLIC_DASHBOARD_VERSION ?? "0.1.x"`, which is a third, different version story.
- The duplicate shell paths also disagree on docs/help destinations. The active header links `Documentation` to `https://docs.talosprotocol.com` in [DashboardHeader.tsx](site/dashboard/src/components/layout/DashboardHeader.tsx), while the unused `AppShell` sidebar links to `https://github.com/talosprotocol/talos/tree/main/docs/wiki`. That leaves the repo with no single owned answer to what the dashboard’s canonical help surface actually is.
- This is not just dead-code clutter. The split shell ownership is a concrete reason route drift and stale UI metadata keep appearing: one set of files claims canonical navigation and version state, another set is actually rendered, and the two are already diverging on routes, docs destinations, and visible version strings.

Paths:
- `site/dashboard/src/app/(shell)/layout.tsx`
- `site/dashboard/src/components/layout/DashboardHeader.tsx`
- `site/dashboard/src/components/layout/DashboardSidebar.tsx`
- `site/dashboard/src/components/layout/DashboardFooter.tsx`
- `site/dashboard/src/components/layout/AppShell.tsx`
- `site/dashboard/src/lib/navRegistry.ts`
- `site/dashboard/package.json`

Next step:
- Collapse the dashboard onto one shell owner. Either remove the orphaned `AppShell` / `navRegistry` path and keep the current `(shell)` layout as the only source of truth, or rebase the active layout onto the registry-driven shell. The visible version string and docs/help destination should then be sourced from one canonical configuration path instead of hard-coded in multiple competing shell implementations.

### 59. Dashboard Auth Onboarding Surface and Repo-Local Docs Parity

Status: `in_progress`

Why it is still open:
- The dashboard's own repository README still describes a different auth system than the one the app actually ships. [site/dashboard/README.md](site/dashboard/README.md) says the dashboard is secured with `NextAuth v5` and documents a bootstrap admin flow based on `ADMIN_EMAIL` plus `ADMIN_PASSWORD`, but the live code uses signed cookie sessions in [site/dashboard/src/lib/auth/session.ts](site/dashboard/src/lib/auth/session.ts), edge cookie verification in [site/dashboard/src/middleware.ts](site/dashboard/src/middleware.ts), and WebAuthn registration/login routes under [site/dashboard/src/app/api/auth/webauthn](site/dashboard/src/app/api/auth/webauthn).
- That mismatch is not just wording drift; the documented password path does not appear to exist in the shipped app. This pass found only WebAuthn login/register APIs plus `session` and `logout` routes under [site/dashboard/src/app/api/auth](site/dashboard/src/app/api/auth). A targeted sweep also found `ADMIN_PASSWORD` referenced only in the README and `.env.example`, not in the live auth flow itself.
- The dashboard's public auth surface is internally inconsistent. [site/dashboard/src/app/login/page.tsx](site/dashboard/src/app/login/page.tsx) implements passkey sign-in and bootstrap-device registration via `X-Talos-Bootstrap-Token`, while [site/dashboard/src/app/signup/page.tsx](site/dashboard/src/app/signup/page.tsx) is explicitly a mock form that waits, reports “This is a mock signup,” and redirects back to login without calling any backend. At the same time, [site/dashboard/src/middleware.ts](site/dashboard/src/middleware.ts) does not treat `/signup` as a public route, so unauthenticated users are redirected away from that page anyway. The repo is therefore shipping a visible registration page that is both non-functional and effectively unreachable in the default auth boundary.
- The runtime prerequisites for local startup are also more demanding than the README suggests. [site/dashboard/.env.example](site/dashboard/.env.example) requires `AUTH_SECRET`, `AUTH_COOKIE_HMAC_SECRET`, `TALOS_BOOTSTRAP_TOKEN`, `TALOS_SERVICE_TOKEN`, and admin defaults, while [site/dashboard/src/lib/setup-gate.ts](site/dashboard/src/lib/setup-gate.ts) explicitly disables setup when `AUTH_SECRET` is missing and [site/dashboard/src/db/index.ts](site/dashboard/src/db/index.ts) expects a live Postgres connection by default. The README quickstart and [site/dashboard/scripts/start.sh](site/dashboard/scripts/start.sh) do not spell out that auth/bootstrap and database setup are part of the real local contract.
- This matters because it blurs the dashboard's actual mission and operator model. The repo-local docs still present a generic standalone admin/password dashboard, while the code has already moved to a passkey-first control plane with signed sessions, bootstrap-token device enrollment, and database-backed auth state. That gap will keep causing onboarding confusion until one model is removed or the docs and visible routes are brought into line with the shipped runtime.

Paths:
- `site/dashboard/README.md`
- `site/dashboard/.env.example`
- `site/dashboard/src/app/login/page.tsx`
- `site/dashboard/src/app/signup/page.tsx`
- `site/dashboard/src/app/api/auth`
- `site/dashboard/src/lib/auth/session.ts`
- `site/dashboard/src/lib/setup-gate.ts`
- `site/dashboard/src/middleware.ts`
- `site/dashboard/src/db/index.ts`
- `site/dashboard/scripts/start.sh`

Next step:
- Pick one truthful dashboard auth story and make every surface match it. If the intended product is passkey bootstrap plus signed sessions, remove the stale NextAuth/password language, document the real env/database/bootstrap prerequisites, and either delete the mock `/signup` path or replace it with a real flow that is actually reachable under the middleware policy.

### 60. Dashboard Probe, Readiness, and Deployment Health Contract Parity

Status: `completed`

What was completed:
- The dashboard now exposes the full documented probe surface. [site/dashboard/src/app/healthz/route.ts](site/dashboard/src/app/healthz/route.ts), [site/dashboard/src/app/readyz/route.ts](site/dashboard/src/app/readyz/route.ts), [site/dashboard/src/app/version/route.ts](site/dashboard/src/app/version/route.ts), and [site/dashboard/src/app/metrics/route.ts](site/dashboard/src/app/metrics/route.ts) are all present in the shipped app tree, and [site/dashboard/src/lib/health.ts](site/dashboard/src/lib/health.ts) centralizes the shared health/build logic instead of leaving readiness as an ad hoc route-local check.
- Readiness is now dependency-aware for the dashboard's own operator contract. [site/dashboard/src/lib/health.ts](site/dashboard/src/lib/health.ts) validates the required auth/origin env surface, reports recommended-but-optional bootstrap env drift separately, and performs a live database probe through [site/dashboard/src/db/index.ts](site/dashboard/src/db/index.ts). [site/dashboard/src/app/readyz/route.ts](site/dashboard/src/app/readyz/route.ts) now returns `503` when those checks fail rather than always reporting healthy.
- The deployment contract is now aligned with that readiness model. [site/dashboard/Dockerfile](site/dashboard/Dockerfile) health-checks `/readyz`, so container health follows the same dependency-aware signal that the repo docs describe instead of the weaker process-only `/healthz` route.
- The dashboard now has explicit build and Prometheus-facing surfaces. [site/dashboard/src/app/version/route.ts](site/dashboard/src/app/version/route.ts) returns build metadata from the shared helper, while [site/dashboard/src/app/metrics/route.ts](site/dashboard/src/app/metrics/route.ts) exports Prometheus-style readiness, config, and database metrics. [site/dashboard/README.md](site/dashboard/README.md) already reflects that four-endpoint contract.
- Verification in this pass covered the helper and package type surface directly. `npm run test -- --run src/__tests__/health/health.test.ts` now passes in [site/dashboard](site/dashboard), and `npm run typecheck` also passes there after tightening the helper/test boundary. The readiness contract remains intentionally scoped to dashboard-owned prerequisites plus Postgres; broader downstream service reachability is still represented separately by [site/dashboard/src/app/api/status/aggregate/route.ts](site/dashboard/src/app/api/status/aggregate/route.ts) rather than being folded into `/readyz`.

Paths:
- `site/dashboard/src/app/healthz/route.ts`
- `site/dashboard/src/app/readyz/route.ts`
- `site/dashboard/src/app/version/route.ts`
- `site/dashboard/src/app/metrics/route.ts`
- `site/dashboard/src/app/api/status/aggregate/route.ts`
- `site/dashboard/src/lib/health.ts`
- `site/dashboard/src/db/index.ts`
- `site/dashboard/.env.example`
- `site/dashboard/Dockerfile`
- `site/dashboard/src/__tests__/health/health.test.ts`
- `docs/guides/deployment.md`

Next step:
- None for this tracker item. Any remaining dashboard operability work should stay under the still-open auth, DB-lifecycle, and route-integrity items rather than reopening the now-implemented health-contract surface.

### 61. Dashboard Examples Manifest Ownership and Route-Surface Parity

Status: `completed`

What was completed:
- The examples catalog now reads from the canonical monorepo manifest instead of a missing submodule path. [site/dashboard/src/app/api/examples/manifest/route.ts](site/dashboard/src/app/api/examples/manifest/route.ts) now uses [site/dashboard/src/lib/examples-manifest.ts](site/dashboard/src/lib/examples-manifest.ts) to resolve [contracts/examples_manifest.json](contracts/examples_manifest.json) from the workspace root in local development and from a bundled `contracts/examples_manifest.json` in the dashboard runtime image. [site/dashboard/Dockerfile](site/dashboard/Dockerfile) now copies that canonical manifest into the container so the route keeps working outside the monorepo checkout.
- The manifest API now returns the shape the UI was already trying to consume. [site/dashboard/src/lib/examples-manifest.ts](site/dashboard/src/lib/examples-manifest.ts) augments the contracts document with `timestamp`, `source_path`, and per-example `status` fields derived from the declared backend env vars plus the example health endpoints, and [site/dashboard/src/app/(shell)/examples/page.tsx](site/dashboard/src/app/(shell)/examples/page.tsx) now uses the updated contract wording instead of instructing operators to initialize a non-existent contracts submodule.
- The shipped dashboard route inventory now matches the contract manifest for the currently declared example routes. [contracts/examples_manifest.json](contracts/examples_manifest.json) advertises `/examples/chat` and `/examples/devops`, and the app tree now ships both [site/dashboard/src/app/(shell)/examples/chat/page.tsx](site/dashboard/src/app/(shell)/examples/chat/page.tsx) and [site/dashboard/src/app/(shell)/examples/devops/page.tsx](site/dashboard/src/app/(shell)/examples/devops/page.tsx). The new DevOps page is intentionally catalog/status-focused so the manifest and route inventory agree without overstating the still-open backend trigger/log contract tracked elsewhere.
- The dashboard navigation model now recognizes both example routes. [site/dashboard/src/lib/navRegistry.ts](site/dashboard/src/lib/navRegistry.ts) now includes `/examples/devops`, which keeps the route registry aligned with the manifest-backed examples surface and breadcrumb generation.
- The stale examples env contract was removed. [site/dashboard/.env.example](site/dashboard/.env.example) no longer declares unused `EXAMPLES_CHAT_URL` / `EXAMPLES_DEVOPS_URL` variables; the examples surface now truthfully relies on the same `TALOS_CHAT_URL` and `TALOS_AIOPS_URL` variables used by the actual example proxy routes.
- Verification in this pass covered the new manifest helper and the dashboard package type surface. `npm run test -- --run src/__tests__/examples/manifest.test.ts src/__tests__/health/health.test.ts` passes in [site/dashboard](site/dashboard), and `npm run typecheck` also passes there. The deeper `services/aiops` endpoint mismatch remains intentionally tracked under the separate DevOps/AIOps contract item rather than this now-closed route-ownership task.

Paths:
- `site/dashboard/src/app/api/examples/manifest/route.ts`
- `contracts/examples_manifest.json`
- `site/dashboard/src/app/(shell)/examples/page.tsx`
- `site/dashboard/src/app/(shell)/examples/chat/page.tsx`
- `site/dashboard/src/app/(shell)/examples/devops/page.tsx`
- `site/dashboard/src/app/api/examples/devops`
- `site/dashboard/src/lib/navRegistry.ts`
- `site/dashboard/src/app/(shell)/console/page.tsx`
- `site/dashboard/.env.example`
- `site/dashboard/src/lib/examples-manifest.ts`
- `site/dashboard/src/__tests__/examples/manifest.test.ts`
- `site/dashboard/Dockerfile`

Next step:
- None for this tracker item. Remaining DevOps demo work should stay under the still-open backend contract and product-truthfulness items rather than reopening the now-aligned manifest ownership and route surface.

### 62. Dashboard Database Bootstrap and Migration Ownership Parity

Status: `completed`

What was completed:
- The dashboard package now owns its Drizzle lifecycle explicitly. [site/dashboard/package.json](site/dashboard/package.json) now exposes `db:generate`, `db:migrate`, `db:push`, and `db:studio`, and [site/dashboard/Makefile](site/dashboard/Makefile) now mirrors those entrypoints with `db-generate`, `db-migrate`, `db-push`, and `db-studio` targets. That turns the already-existing [site/dashboard/drizzle.config.ts](site/dashboard/drizzle.config.ts) and checked-in [site/dashboard/drizzle/0000_sturdy_hannibal_king.sql](site/dashboard/drizzle/0000_sturdy_hannibal_king.sql) into package-owned workflow entrypoints instead of hidden implementation details.
- The repo-local runtime contract now documents the database prerequisite directly. [site/dashboard/.env.example](site/dashboard/.env.example) now includes `DATABASE_URL`, [site/dashboard/README.md](site/dashboard/README.md) now tells operators to point it at Postgres and run `npm run db:migrate` before the first auth-enabled start, and [site/dashboard/scripts/start.sh](site/dashboard/scripts/start.sh) now exports one canonical default `DATABASE_URL` and prints the migration reminder on startup.
- The ad hoc session helper was aligned with the real runtime defaults. [site/dashboard/scripts/inject-session.js](site/dashboard/scripts/inject-session.js) no longer hard-codes a separate `localhost:5433` connection string; it now reads `DATABASE_URL` and `AUTH_COOKIE_HMAC_SECRET` from the environment with the same `localhost:5432` fallback used by [site/dashboard/src/db/index.ts](site/dashboard/src/db/index.ts) and [site/dashboard/drizzle.config.ts](site/dashboard/drizzle.config.ts).
- Verification in this pass confirmed that the new DB lifecycle entrypoint is live and that the dashboard package still type-checks. `npm run db:migrate -- --help` now resolves through the package-owned script surface in [site/dashboard](site/dashboard), and `npm run typecheck` also passes there after the workflow changes.

Paths:
- `site/dashboard/src/db/schema.ts`
- `site/dashboard/src/db/index.ts`
- `site/dashboard/drizzle.config.ts`
- `site/dashboard/drizzle/0000_sturdy_hannibal_king.sql`
- `site/dashboard/package.json`
- `site/dashboard/README.md`
- `site/dashboard/Makefile`
- `site/dashboard/scripts/start.sh`
- `site/dashboard/.env.example`
- `site/dashboard/scripts/inject-session.js`

Next step:
- None for this tracker item. Remaining dashboard persistence work should now focus on runtime auth/setup behavior and migration evolution rather than the previously missing package-owned DB bootstrap path.

### 63. Dashboard Repo-Local Documentation and Architecture Wiki Parity

Status: `completed`

What was completed:
- The dashboard package now has a coherent local docs surface again. [site/dashboard/docs/wiki/Home.md](site/dashboard/docs/wiki/Home.md) no longer points at missing pages, and the previously absent [site/dashboard/docs/wiki/Features.md](site/dashboard/docs/wiki/Features.md), [site/dashboard/docs/wiki/API.md](site/dashboard/docs/wiki/API.md), and [site/dashboard/docs/wiki/Development.md](site/dashboard/docs/wiki/Development.md) now exist and describe the current package surfaces.
- The repo-local README was rebaselined to the current Next.js control-plane reality. [site/dashboard/README.md](site/dashboard/README.md) now documents the App Router shell, dashboard-owned `/api/*` routes, passkey bootstrap/login, signed session cookies, Postgres-backed auth/setup state, the current operator pages, and the real local start/test paths instead of the older React/Vite plus read-only-viewer framing.
- The local wiki architecture page now matches the actual code boundary more closely. [site/dashboard/docs/wiki/Architecture.md](site/dashboard/docs/wiki/Architecture.md) now describes the dashboard as a stateful Next.js operator console with dashboard-owned API routes, contracts usage, Postgres-backed auth/setup state, and upstream dependencies on gateway, audit, connector, and example services rather than a thin `HttpDataSource -> Gateway API` viewer.
- The package-local assistant guidance was also updated. [site/dashboard/CLAUDE.md](site/dashboard/CLAUDE.md) no longer claims `NextAuth v5`; it now points contributors at the current WebAuthn plus signed-session auth model and the broader operator/control-plane role of the package.
- Verification in this pass included a targeted local link audit over [site/dashboard/README.md](site/dashboard/README.md), [site/dashboard/CLAUDE.md](site/dashboard/CLAUDE.md), and every file in [site/dashboard/docs/wiki](site/dashboard/docs/wiki), which returned zero broken relative links after the rewrite.

Paths:
- `site/dashboard/README.md`
- `site/dashboard/docs/wiki/Home.md`
- `site/dashboard/docs/wiki/Architecture.md`
- `site/dashboard/docs/wiki/Features.md`
- `site/dashboard/docs/wiki/API.md`
- `site/dashboard/docs/wiki/Development.md`
- `site/dashboard/CLAUDE.md`
- `site/dashboard/src/app`
- `site/dashboard/src/db/schema.ts`
- `site/dashboard/src/app/api/status/aggregate/route.ts`
- `site/dashboard/src/app/api/auth/webauthn`
- `site/dashboard/src/app/api/examples`

Next step:
- None for this tracker item. Remaining dashboard documentation work should now focus on the still-open runtime, auth, and DB-lifecycle issues rather than missing wiki pages or Vite-era local package framing.

## Recently Closed

- Flipped the repo-default A2A protocol mode to `dual`: [services/ai-gateway/app/settings.py](services/ai-gateway/app/settings.py) now serves the standards-first public Agent Card and `/rpc` surface by default while keeping compat available as a migration lane.
- Closed the A2A docs-positioning cleanup: [README.md](README.md) and [docs/sdk/a2a-sdk-guide.md](docs/sdk/a2a-sdk-guide.md) now present the public Agent Card plus `/rpc` surface as the primary A2A contract, with Talos secure channels linked as an extension.
- Tightened strict A2A v1 behavior in the gateway: [services/ai-gateway/app/api/a2a_v1/service.py](services/ai-gateway/app/api/a2a_v1/service.py) now rejects legacy JSON-RPC aliases and coarse `a2a.invoke` / `a2a.stream` scope fallbacks in `v1` mode while keeping them available in `dual` mode.
- Added an official TCK path to the upstream interop runner: [scripts/python/run_a2a_upstream_interop.py](scripts/python/run_a2a_upstream_interop.py) can now plan or execute `official-a2a-tck` runs against a local Talos gateway and capture the compliance report when a local `a2a-tck` checkout is available.
- Added live TCK runtime interop aids for the Talos gateway: [services/ai-gateway/app/settings.py](services/ai-gateway/app/settings.py) now defaults public Agent Card visibility to `public`, [scripts/python/run_a2a_upstream_interop.py](scripts/python/run_a2a_upstream_interop.py) now forwards bearer auth into the official TCK when `--api-token` is provided, [services/ai-gateway/app/api/a2a_v1/router.py](services/ai-gateway/app/api/a2a_v1/router.py) now exposes a root JSON-RPC alias in `dual` mode for `v0.3.0`-era tooling, and [services/ai-gateway/app/domain/a2a/dispatcher.py](services/ai-gateway/app/domain/a2a/dispatcher.py) now supports an explicit `A2A_MOCK_LLM_RESPONSES=true` dev-only fallback for deterministic live compliance runs.
- Added the Talos parallelization/orchestration skill stack: [.agents/skills/talos-parallelize](.agents/skills/talos-parallelize) now ships planner, monitor, and persistent-run helpers plus schema-backed artifacts and focused tests.
- Added repo-local skill and submodule-agent maintenance helpers: [scripts/sync_codex_skills.py](scripts/sync_codex_skills.py), [scripts/sync_submodule_agents.py](scripts/sync_submodule_agents.py), and [scripts/verify_agent_layout.py](scripts/verify_agent_layout.py) now back the updated Codex workflow, and [deploy/scripts/setup.sh](deploy/scripts/setup.sh) now updates submodules in manifest order.
- Added a root-level schema check for the contract-backed gateway surface inventory via [tests/test_surface_inventory_schema.py](tests/test_surface_inventory_schema.py), including method-level A2A v1 permission assertions and Python asset parity checks.
- Closed the cross-SDK A2A v1 streaming ergonomics gap: Go now exposes channel-based stream returns, Rust exposes `Stream<Item = Result<...>>`, and Java exposes `Iterable`-based stream returns while preserving the collect-style and callback-style helpers.
- Closed the dual-mode compat exposure decision: the public `/.well-known/agent-card.json` stays standards-first in `dual` mode, while authenticated `/extendedAgentCard` and `GetExtendedAgentCard` can still expose the compat migration extension.
- Added callback-style incremental A2A streaming handlers to the Go, Rust, and Java SDKs while keeping the existing collect-style helpers as wrappers.
- Added minimal standards-first A2A v1 discovery/RPC and SSE-drain streaming helpers to the Java SDK, with focused tests for Agent Card discovery, canonical method names, and stream-side JSON-RPC error handling.
- Added A2A v1 streaming/subscription support to the Go and Rust SDKs by parsing SSE `data:` events from `/rpc`, with focused tests for canonical method names, stream result extraction, and stream-side JSON-RPC errors.
- Added minimal standards-first A2A v1 discovery/RPC helpers to the Go and Rust SDKs, including Agent Card discovery, canonical JSON-RPC method helpers, Talos extension introspection, and focused tests.
- Closed the contract pinning / conformance follow-through item: Go and Rust now pass the full pinned `contracts/test_vectors/sdk/release_sets/v1.1.0.json` release set, including canonical JSON, signing, capability verification, frame codec, MCP signing, ratchet micro-vectors, and the `v1_1_0_roundtrip.json` golden trace.
- Removed the duplicate `services/ai-gateway/gateway_surface.json` registry from the gateway path: RBAC now reads the contract inventory too, tests verify the contract-defined auth surfaces against the live app, and Docker/compose no longer ship the local duplicate.
- Extended the Go and Rust conformance runners to execute `frame_codec.json` and `mcp_sign_verify.json`, reducing the pinned `v1.1.0` release-set skips to the still-unimplemented capability and ratchet vectors.
- Added pinned `SDK_VERSION`, `SUPPORTED_PROTOCOL_RANGE`, and `CONTRACT_MANIFEST_HASH` exports to the Go and Rust SDKs, with tests that recompute the canonical `contract_manifest.json` hash from the shared contracts source.
- Replaced the Go and Rust conformance shell TODOs with real release-set-aware runners that execute supported canonical JSON and signing vectors and report unsupported vector files explicitly.
- Replaced the placeholder Python and TypeScript `CONTRACT_MANIFEST_HASH` exports with the canonical hash of `contracts/sdk/contract_manifest.json` and added tests that recompute it from the source manifest.
- Fixed gateway auth-surface discovery so containerized `/app` layouts can find the contract inventory, and updated compose/image wiring to use the contract inventory for auth instead of the local gateway route file.
- Switched the Python and TypeScript A2A v1 SDK helpers to canonical JSON-RPC method names and added a local reference-style live interop harness for the Python smoke path.
- Refreshed `services/ai-gateway/tests/integration/test_a2a_streaming_security.py` to the current A2A v1 `/rpc` subscription model and removed the obsolete SQLite/`JSONB` dependency from that test path.
- Brought TypeScript A2A v1 client parity up to the Python client.
- Wired method-level `/rpc` auth resolution into the gateway runtime.
- Removed runtime coupling to the legacy gateway RBAC registry and replaced it with contract-inventory-backed gateway surface validation.
- Added side-by-side A2A v1 discovery and JSON-RPC contract schemas plus vectors under `contracts/schemas/a2a/v1` and `contracts/test_vectors/a2a/v1`, and synced those assets into the Python contract package mirror.
