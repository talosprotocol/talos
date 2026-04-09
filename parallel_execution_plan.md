# Parallelization Plan

## Goal

Resolve all pending implementation gaps identified in the March 2026 repo audit to bring the Talos project into alignment with its production-ready claims.

## Stages

### Stage 1 (parallel)

- `a2a-interop-validation`: Execute external A2A v1 live interop validation against official TCK and upstream targets. [$talos-backend-architect-agent]
- `ts-transport-completion`: Complete TypeScript Core transport implementation for TalosClient. [$talos-sdk-parity]
- `ucp-error-taxonomy`: Align UCP Connector error-taxonomy with contract specifications. [$talos-backend-architect-agent]
- `external-audit-anchoring`: Implement external audit anchoring pipeline and verification flow. [$talos-backend-architect-agent]
- `mcp-secure-tunnel`: Implement secure-session tunnel for active MCP connector transport. [$talos-backend-architect-agent]
- `security-dashboard-auth-parity`: Align security dashboard auth and runtime-mode documentation. [$talos-docs-parity]
- `demo-examples-parity`: Resolve Demo and Examples product-surface and manifest parity. [$talos-docs-parity]
- `devops-example-aiops-parity`: Align DevOps example API and AIOps backend contract parity. [$talos-backend-architect-agent]
- `marketing-catalog-content`: Audit and align Marketing Site product catalog and content ownership. [$talos-frontend-developer-agent]
- `docs-home-status-metrics`: Align Docs Home status metrics and architecture framing parity. [$talos-docs-parity]

Blocked candidates:
- `gov-ownership-consolidation` blocked by a2a-interop-validation (serial_only)
- `ai-streaming-settle` blocked by a2a-interop-validation (shared_boundary:gateway-api)
- `decentralized-did-resolution` blocked by ts-transport-completion (shared_boundary:sdk-core)
- `gateway-topology-consolidation` blocked by a2a-interop-validation (serial_only; shared_boundary:gateway-api), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only)
- `legacy-src-boundary` blocked by a2a-interop-validation (serial_only), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only; shared_writes:src)
- `service-port-consolidation` blocked by a2a-interop-validation (serial_only), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only)
- `a2a-cap-validator-bootstrap` blocked by a2a-interop-validation (shared_boundary:gateway-api)
- `phase15-reservation-cleanup` blocked by a2a-interop-validation (shared_boundary:gateway-api)
- `audit-hardening-sink` blocked by external-audit-anchoring (shared_boundary:audit-logic)
- `phase13-secrets-rotation` blocked by a2a-interop-validation (shared_boundary:gateway-api)
- `admin-auth-realism` blocked by a2a-interop-validation (shared_boundary:gateway-api)
- `audit-explorer-parity` blocked by external-audit-anchoring (shared_boundary:audit-logic)
- `dashboard-api-namespace-parity` blocked by security-dashboard-auth-parity (shared_boundary:dashboard-shell)
- `root-cli-command-parity` blocked by a2a-interop-validation (serial_only), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only), mcp-secure-tunnel (serial_only), security-dashboard-auth-parity (serial_only)
- `dashboard-secure-agent-shell` blocked by security-dashboard-auth-parity (shared_boundary:dashboard-shell)
- `deprecated-config-dash-retirement` blocked by a2a-interop-validation (serial_only), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only), mcp-secure-tunnel (serial_only), security-dashboard-auth-parity (serial_only), demo-examples-parity (serial_only), devops-example-aiops-parity (serial_only)
- `mission-control-kpi-truth` blocked by security-dashboard-auth-parity (shared_boundary:dashboard-shell)
- `marketing-benchmark-source` blocked by marketing-catalog-content (shared_boundary:marketing-content)
- `vulnerability-disclosure-parity` blocked by a2a-interop-validation (serial_only), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only), mcp-secure-tunnel (serial_only), security-dashboard-auth-parity (serial_only), demo-examples-parity (serial_only), devops-example-aiops-parity (serial_only), marketing-catalog-content (serial_only; shared_boundary:marketing-content)
- `dashboard-ws-stream-boundary` blocked by security-dashboard-auth-parity (shared_writes:site/dashboard/src/lib/config.ts; shared_boundary:dashboard-shell)
- `marketing-product-cta-parity` blocked by marketing-catalog-content (shared_writes:site/marketing/src/content/products.json; shared_boundary:marketing-content)
- `marketing-docs-discovery-parity` blocked by marketing-catalog-content (shared_writes:site/marketing/src/app/docs; shared_boundary:marketing-content)
- `marketing-availability-messaging` blocked by marketing-catalog-content (shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-catalog-content (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by security-dashboard-auth-parity (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by a2a-interop-validation (serial_only), ts-transport-completion (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only), mcp-secure-tunnel (serial_only), security-dashboard-auth-parity (serial_only; shared_boundary:dashboard-shell), demo-examples-parity (serial_only), devops-example-aiops-parity (serial_only), marketing-catalog-content (serial_only), docs-home-status-metrics (serial_only)

### Stage 2 (serial)

- `a2a-compat-retirement`: Retire legacy A2A compat migration paths and move to strict v1 default. [$talos-backend-architect-agent]

Blocked candidates:
- `gov-ownership-consolidation` blocked by a2a-compat-retirement (serial_only)
- `ai-streaming-settle` blocked by a2a-compat-retirement (serial_only; shared_boundary:gateway-api)
- `decentralized-did-resolution` blocked by a2a-compat-retirement (serial_only)
- `gateway-topology-consolidation` blocked by a2a-compat-retirement (serial_only; shared_boundary:gateway-api)
- `legacy-src-boundary` blocked by a2a-compat-retirement (serial_only)
- `service-port-consolidation` blocked by a2a-compat-retirement (serial_only)
- `a2a-cap-validator-bootstrap` blocked by a2a-compat-retirement (serial_only; shared_writes:services/ai-gateway/app/settings.py; shared_boundary:gateway-api)
- `phase15-reservation-cleanup` blocked by a2a-compat-retirement (serial_only; shared_boundary:gateway-api)
- `audit-hardening-sink` blocked by a2a-compat-retirement (serial_only)
- `phase13-secrets-rotation` blocked by a2a-compat-retirement (serial_only; shared_boundary:gateway-api)
- `admin-auth-realism` blocked by a2a-compat-retirement (serial_only; shared_boundary:gateway-api)
- `audit-explorer-parity` blocked by a2a-compat-retirement (serial_only)
- `dashboard-api-namespace-parity` blocked by a2a-compat-retirement (serial_only)
- `root-cli-command-parity` blocked by a2a-compat-retirement (serial_only)
- `secure-chat-crypto-audit` blocked by a2a-compat-retirement (serial_only)
- `dashboard-secure-agent-shell` blocked by a2a-compat-retirement (serial_only)
- `deprecated-config-dash-retirement` blocked by a2a-compat-retirement (serial_only)
- `mission-control-kpi-truth` blocked by a2a-compat-retirement (serial_only)
- `marketing-benchmark-source` blocked by a2a-compat-retirement (serial_only)
- `vulnerability-disclosure-parity` blocked by a2a-compat-retirement (serial_only)
- `marketing-dev-sdk-example` blocked by a2a-compat-retirement (serial_only)
- `public-ucp-commerce-parity` blocked by a2a-compat-retirement (serial_only)
- `dashboard-ws-stream-boundary` blocked by a2a-compat-retirement (serial_only)
- `marketing-product-cta-parity` blocked by a2a-compat-retirement (serial_only)
- `marketing-docs-discovery-parity` blocked by a2a-compat-retirement (serial_only)
- `marketing-availability-messaging` blocked by a2a-compat-retirement (serial_only)
- `marketing-verification-drift-gate` blocked by a2a-compat-retirement (serial_only)
- `dashboard-verification-route-gate` blocked by a2a-compat-retirement (serial_only)
- `dashboard-shell-ownership` blocked by a2a-compat-retirement (serial_only)

### Stage 3 (serial)

- `gov-ownership-consolidation`: Consolidate Governance-Agent ownership between standalone and gateway-embedded versions. [$talos-backend-architect-agent]

Blocked candidates:
- `ai-streaming-settle` blocked by gov-ownership-consolidation (serial_only)
- `decentralized-did-resolution` blocked by gov-ownership-consolidation (serial_only)
- `gateway-topology-consolidation` blocked by gov-ownership-consolidation (serial_only)
- `legacy-src-boundary` blocked by gov-ownership-consolidation (serial_only)
- `service-port-consolidation` blocked by gov-ownership-consolidation (serial_only)
- `a2a-cap-validator-bootstrap` blocked by gov-ownership-consolidation (serial_only)
- `phase15-reservation-cleanup` blocked by gov-ownership-consolidation (serial_only)
- `audit-hardening-sink` blocked by gov-ownership-consolidation (serial_only)
- `phase13-secrets-rotation` blocked by gov-ownership-consolidation (serial_only)
- `admin-auth-realism` blocked by gov-ownership-consolidation (serial_only)
- `audit-explorer-parity` blocked by gov-ownership-consolidation (serial_only)
- `dashboard-api-namespace-parity` blocked by gov-ownership-consolidation (serial_only)
- `root-cli-command-parity` blocked by gov-ownership-consolidation (serial_only)
- `secure-chat-crypto-audit` blocked by gov-ownership-consolidation (serial_only)
- `dashboard-secure-agent-shell` blocked by gov-ownership-consolidation (serial_only)
- `deprecated-config-dash-retirement` blocked by gov-ownership-consolidation (serial_only)
- `mission-control-kpi-truth` blocked by gov-ownership-consolidation (serial_only)
- `marketing-benchmark-source` blocked by gov-ownership-consolidation (serial_only)
- `vulnerability-disclosure-parity` blocked by gov-ownership-consolidation (serial_only)
- `marketing-dev-sdk-example` blocked by gov-ownership-consolidation (serial_only)
- `public-ucp-commerce-parity` blocked by gov-ownership-consolidation (serial_only)
- `dashboard-ws-stream-boundary` blocked by gov-ownership-consolidation (serial_only)
- `marketing-product-cta-parity` blocked by gov-ownership-consolidation (serial_only)
- `marketing-docs-discovery-parity` blocked by gov-ownership-consolidation (serial_only)
- `marketing-availability-messaging` blocked by gov-ownership-consolidation (serial_only)
- `marketing-verification-drift-gate` blocked by gov-ownership-consolidation (serial_only)
- `dashboard-verification-route-gate` blocked by gov-ownership-consolidation (serial_only)
- `dashboard-shell-ownership` blocked by gov-ownership-consolidation (serial_only)

### Stage 4 (parallel)

- `gov-auth-log-completeness`: Complete Governance-Agent deterministic authz and log artifact persistence. [$talos-backend-architect-agent]
- `ai-streaming-settle`: Implement public AI streaming with settle-on-end semantics and accounting. [$talos-backend-architect-agent]
- `decentralized-did-resolution`: Implement decentralized DID resolution via DHT lookup. [$talos-sdk-parity]
- `audit-hardening-sink`: Hardening audit sink bootstrap and HMAC key fail-closed behavior. [$talos-backend-architect-agent]
- `dashboard-api-namespace-parity`: Resolve Dashboard control-plane API namespace parity and proxy routes. [$talos-frontend-developer-agent]
- `secure-chat-crypto-audit`: Achieve cryptographic and audit reality for Secure Chat demo. [$talos-backend-architect-agent]
- `marketing-benchmark-source`: Align Marketing benchmark claim source-of-truth with repo artifacts. [$talos-frontend-developer-agent]
- `public-ucp-commerce-parity`: Align public UCP commerce positioning with connector reality. [$talos-frontend-developer-agent]

Blocked candidates:
- `gateway-topology-consolidation` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only; shared_boundary:gateway-api), decentralized-did-resolution (serial_only)
- `legacy-src-boundary` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only), decentralized-did-resolution (serial_only; shared_writes:src)
- `service-port-consolidation` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only), decentralized-did-resolution (serial_only)
- `a2a-cap-validator-bootstrap` blocked by ai-streaming-settle (shared_boundary:gateway-api)
- `phase15-reservation-cleanup` blocked by ai-streaming-settle (shared_boundary:gateway-api)
- `phase13-secrets-rotation` blocked by ai-streaming-settle (shared_boundary:gateway-api)
- `admin-auth-realism` blocked by ai-streaming-settle (shared_boundary:gateway-api)
- `audit-explorer-parity` blocked by audit-hardening-sink (shared_boundary:audit-logic)
- `root-cli-command-parity` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only), decentralized-did-resolution (serial_only), audit-hardening-sink (serial_only), dashboard-api-namespace-parity (serial_only)
- `dashboard-secure-agent-shell` blocked by dashboard-api-namespace-parity (shared_boundary:dashboard-shell)
- `deprecated-config-dash-retirement` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only), decentralized-did-resolution (serial_only), audit-hardening-sink (serial_only), dashboard-api-namespace-parity (serial_only), secure-chat-crypto-audit (serial_only)
- `mission-control-kpi-truth` blocked by dashboard-api-namespace-parity (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell)
- `vulnerability-disclosure-parity` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only), decentralized-did-resolution (serial_only), audit-hardening-sink (serial_only), dashboard-api-namespace-parity (serial_only), secure-chat-crypto-audit (serial_only), marketing-benchmark-source (serial_only; shared_boundary:marketing-content)
- `marketing-dev-sdk-example` blocked by marketing-benchmark-source (shared_boundary:marketing-content)
- `dashboard-ws-stream-boundary` blocked by dashboard-api-namespace-parity (shared_boundary:dashboard-shell)
- `marketing-product-cta-parity` blocked by marketing-benchmark-source (shared_boundary:marketing-content)
- `marketing-docs-discovery-parity` blocked by marketing-benchmark-source (shared_boundary:marketing-content)
- `marketing-availability-messaging` blocked by marketing-benchmark-source (shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-benchmark-source (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by dashboard-api-namespace-parity (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by gov-auth-log-completeness (serial_only), ai-streaming-settle (serial_only), decentralized-did-resolution (serial_only), audit-hardening-sink (serial_only), dashboard-api-namespace-parity (serial_only; shared_boundary:dashboard-shell), secure-chat-crypto-audit (serial_only), marketing-benchmark-source (serial_only), public-ucp-commerce-parity (serial_only)

### Stage 5 (parallel)

- `terminal-trust-enforcement`: Implement real Ed25519 signature verification and TGA-backed trust for terminal-adapter. [$talos-backend-architect-agent]
- `a2a-cap-validator-bootstrap`: Unify A2A capability validator bootstrap and configuration keys. [$talos-backend-architect-agent]
- `audit-explorer-parity`: Align Audit Explorer product surface with documented proof workflows. [$talos-frontend-developer-agent]
- `dashboard-secure-agent-shell`: Align Dashboard Secure-Agent shell with active chat-agent contract. [$talos-frontend-developer-agent]
- `marketing-security-guarantee`: Align Marketing security page guarantees and metric parity. [$talos-frontend-developer-agent]
- `did-dht-api-parity`: Align DID/DHT user-facing API and high-level example parity. [$talos-sdk-parity]

Blocked candidates:
- `gateway-topology-consolidation` blocked by terminal-trust-enforcement (serial_only)
- `legacy-src-boundary` blocked by terminal-trust-enforcement (serial_only)
- `service-port-consolidation` blocked by terminal-trust-enforcement (serial_only)
- `phase15-reservation-cleanup` blocked by a2a-cap-validator-bootstrap (shared_boundary:gateway-api)
- `phase13-secrets-rotation` blocked by a2a-cap-validator-bootstrap (shared_boundary:gateway-api)
- `admin-auth-realism` blocked by a2a-cap-validator-bootstrap (shared_boundary:gateway-api)
- `root-cli-command-parity` blocked by terminal-trust-enforcement (serial_only), a2a-cap-validator-bootstrap (serial_only), audit-explorer-parity (serial_only)
- `deprecated-config-dash-retirement` blocked by terminal-trust-enforcement (serial_only), a2a-cap-validator-bootstrap (serial_only), audit-explorer-parity (serial_only), dashboard-secure-agent-shell (serial_only)
- `dashboard-playground-gateway` blocked by dashboard-secure-agent-shell (shared_boundary:dashboard-shell)
- `mission-control-kpi-truth` blocked by dashboard-secure-agent-shell (shared_boundary:dashboard-shell)
- `vulnerability-disclosure-parity` blocked by terminal-trust-enforcement (serial_only), a2a-cap-validator-bootstrap (serial_only), audit-explorer-parity (serial_only), dashboard-secure-agent-shell (serial_only), marketing-security-guarantee (serial_only; shared_boundary:marketing-content)
- `marketing-dev-sdk-example` blocked by marketing-security-guarantee (shared_boundary:marketing-content)
- `marketing-roadmap-live-status` blocked by marketing-security-guarantee (shared_boundary:marketing-content)
- `dashboard-ws-stream-boundary` blocked by dashboard-secure-agent-shell (shared_boundary:dashboard-shell)
- `marketing-product-cta-parity` blocked by marketing-security-guarantee (shared_boundary:marketing-content)
- `marketing-docs-discovery-parity` blocked by marketing-security-guarantee (shared_boundary:marketing-content)
- `marketing-availability-messaging` blocked by marketing-security-guarantee (shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-security-guarantee (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by dashboard-secure-agent-shell (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by terminal-trust-enforcement (serial_only), a2a-cap-validator-bootstrap (serial_only), audit-explorer-parity (serial_only), dashboard-secure-agent-shell (serial_only; shared_boundary:dashboard-shell), marketing-security-guarantee (serial_only), did-dht-api-parity (serial_only)

### Stage 6 (serial)

- `gateway-topology-consolidation`: Consolidate gateway topology and align scripts/dashboard around ai-gateway. [$talos-infra-maintainer-agent]

Blocked candidates:
- `legacy-src-boundary` blocked by gateway-topology-consolidation (serial_only)
- `service-port-consolidation` blocked by gateway-topology-consolidation (serial_only; shared_writes:README.md)
- `phase15-reservation-cleanup` blocked by gateway-topology-consolidation (serial_only; shared_boundary:gateway-api)
- `phase13-secrets-rotation` blocked by gateway-topology-consolidation (serial_only; shared_boundary:gateway-api)
- `admin-auth-realism` blocked by gateway-topology-consolidation (serial_only; shared_boundary:gateway-api)
- `root-cli-command-parity` blocked by gateway-topology-consolidation (serial_only)
- `deprecated-config-dash-retirement` blocked by gateway-topology-consolidation (serial_only; shared_writes:deploy/scripts/common.sh)
- `dashboard-playground-gateway` blocked by gateway-topology-consolidation (serial_only)
- `mission-control-kpi-truth` blocked by gateway-topology-consolidation (serial_only)
- `vulnerability-disclosure-parity` blocked by gateway-topology-consolidation (serial_only)
- `marketing-dev-sdk-example` blocked by gateway-topology-consolidation (serial_only)
- `marketing-roadmap-live-status` blocked by gateway-topology-consolidation (serial_only)
- `dashboard-ws-stream-boundary` blocked by gateway-topology-consolidation (serial_only)
- `marketing-product-cta-parity` blocked by gateway-topology-consolidation (serial_only)
- `marketing-docs-discovery-parity` blocked by gateway-topology-consolidation (serial_only)
- `marketing-availability-messaging` blocked by gateway-topology-consolidation (serial_only)
- `marketing-verification-drift-gate` blocked by gateway-topology-consolidation (serial_only)
- `dashboard-verification-route-gate` blocked by gateway-topology-consolidation (serial_only)
- `dashboard-shell-ownership` blocked by gateway-topology-consolidation (serial_only)

### Stage 7 (serial)

- `legacy-src-boundary`: Define legacy src/ boundary and separate it from active service narrative. [$talos-docs-parity]

Blocked candidates:
- `service-port-consolidation` blocked by legacy-src-boundary (serial_only)
- `phase15-reservation-cleanup` blocked by legacy-src-boundary (serial_only)
- `phase13-secrets-rotation` blocked by legacy-src-boundary (serial_only)
- `admin-auth-realism` blocked by legacy-src-boundary (serial_only)
- `root-cli-command-parity` blocked by legacy-src-boundary (serial_only; shared_writes:src)
- `deprecated-config-dash-retirement` blocked by legacy-src-boundary (serial_only)
- `dashboard-playground-gateway` blocked by legacy-src-boundary (serial_only)
- `mission-control-kpi-truth` blocked by legacy-src-boundary (serial_only)
- `vulnerability-disclosure-parity` blocked by legacy-src-boundary (serial_only)
- `marketing-dev-sdk-example` blocked by legacy-src-boundary (serial_only)
- `marketing-roadmap-live-status` blocked by legacy-src-boundary (serial_only)
- `dashboard-ws-stream-boundary` blocked by legacy-src-boundary (serial_only)
- `marketing-product-cta-parity` blocked by legacy-src-boundary (serial_only)
- `marketing-docs-discovery-parity` blocked by legacy-src-boundary (serial_only)
- `marketing-availability-messaging` blocked by legacy-src-boundary (serial_only)
- `marketing-verification-drift-gate` blocked by legacy-src-boundary (serial_only)
- `dashboard-verification-route-gate` blocked by legacy-src-boundary (serial_only)
- `dashboard-shell-ownership` blocked by legacy-src-boundary (serial_only)

### Stage 8 (serial)

- `service-port-consolidation`: Establish and align canonical service port map across all services and docs. [$talos-backend-architect-agent]

Blocked candidates:
- `phase15-reservation-cleanup` blocked by service-port-consolidation (serial_only)
- `phase13-secrets-rotation` blocked by service-port-consolidation (serial_only)
- `admin-auth-realism` blocked by service-port-consolidation (serial_only)
- `root-cli-command-parity` blocked by service-port-consolidation (serial_only)
- `deprecated-config-dash-retirement` blocked by service-port-consolidation (serial_only)
- `dashboard-playground-gateway` blocked by service-port-consolidation (serial_only)
- `mission-control-kpi-truth` blocked by service-port-consolidation (serial_only)
- `vulnerability-disclosure-parity` blocked by service-port-consolidation (serial_only)
- `marketing-dev-sdk-example` blocked by service-port-consolidation (serial_only)
- `marketing-roadmap-live-status` blocked by service-port-consolidation (serial_only)
- `dashboard-ws-stream-boundary` blocked by service-port-consolidation (serial_only; shared_writes:site/dashboard/src/lib/config.ts)
- `marketing-product-cta-parity` blocked by service-port-consolidation (serial_only)
- `marketing-docs-discovery-parity` blocked by service-port-consolidation (serial_only)
- `marketing-availability-messaging` blocked by service-port-consolidation (serial_only)
- `marketing-verification-drift-gate` blocked by service-port-consolidation (serial_only)
- `dashboard-verification-route-gate` blocked by service-port-consolidation (serial_only)
- `dashboard-shell-ownership` blocked by service-port-consolidation (serial_only)

### Stage 9 (parallel)

- `phase15-reservation-cleanup`: Implement Phase 15 budget reservation cleanup and drift reconcile. [$talos-backend-architect-agent]
- `dashboard-playground-gateway`: Align AI Playground with real gateway and response shape parity. [$talos-frontend-developer-agent]
- `talos-tui-parity`: Align Talos TUI with active-stack parity and fix runtime bugs. [$talos-parallel-orchestrator-agent]
- `marketing-dev-sdk-example`: Align Marketing developers page SDK examples and onboarding parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `phase13-secrets-rotation` blocked by phase15-reservation-cleanup (shared_boundary:gateway-api)
- `admin-auth-realism` blocked by phase15-reservation-cleanup (shared_boundary:gateway-api)
- `deployment-manifest-parity` blocked by phase15-reservation-cleanup (serial_only)
- `root-cli-command-parity` blocked by phase15-reservation-cleanup (serial_only)
- `deprecated-config-dash-retirement` blocked by phase15-reservation-cleanup (serial_only)
- `mission-control-kpi-truth` blocked by dashboard-playground-gateway (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell)
- `vulnerability-disclosure-parity` blocked by phase15-reservation-cleanup (serial_only), dashboard-playground-gateway (serial_only), talos-tui-parity (serial_only)
- `marketing-roadmap-live-status` blocked by marketing-dev-sdk-example (shared_boundary:marketing-content)
- `dashboard-ws-stream-boundary` blocked by dashboard-playground-gateway (shared_boundary:dashboard-shell)
- `marketing-product-cta-parity` blocked by marketing-dev-sdk-example (shared_boundary:marketing-content)
- `marketing-docs-discovery-parity` blocked by marketing-dev-sdk-example (shared_boundary:marketing-content)
- `marketing-availability-messaging` blocked by marketing-dev-sdk-example (shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-dev-sdk-example (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by dashboard-playground-gateway (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by phase15-reservation-cleanup (serial_only), dashboard-playground-gateway (serial_only; shared_boundary:dashboard-shell), talos-tui-parity (serial_only), marketing-dev-sdk-example (serial_only)

### Stage 10 (parallel)

- `phase13-secrets-rotation`: Consolidate Phase 13 secrets rotation ownership and provider contract. [$talos-backend-architect-agent]
- `mission-control-kpi-truth`: Ensure Mission Control KPI and analytics truthfulness in Dashboard. [$talos-frontend-developer-agent]
- `marketing-roadmap-live-status`: Align Marketing roadmap versioning and 'LIVE' status parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `admin-auth-realism` blocked by phase13-secrets-rotation (shared_boundary:gateway-api)
- `deployment-manifest-parity` blocked by phase13-secrets-rotation (serial_only)
- `root-cli-command-parity` blocked by phase13-secrets-rotation (serial_only)
- `deprecated-config-dash-retirement` blocked by phase13-secrets-rotation (serial_only)
- `vulnerability-disclosure-parity` blocked by phase13-secrets-rotation (serial_only), mission-control-kpi-truth (serial_only)
- `dashboard-ws-stream-boundary` blocked by mission-control-kpi-truth (shared_boundary:dashboard-shell)
- `marketing-product-cta-parity` blocked by marketing-roadmap-live-status (shared_boundary:marketing-content)
- `marketing-docs-discovery-parity` blocked by marketing-roadmap-live-status (shared_boundary:marketing-content)
- `marketing-availability-messaging` blocked by marketing-roadmap-live-status (shared_writes:site/marketing/src/app/roadmap/page.tsx; shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-roadmap-live-status (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by mission-control-kpi-truth (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by phase13-secrets-rotation (serial_only), mission-control-kpi-truth (serial_only; shared_boundary:dashboard-shell), marketing-roadmap-live-status (serial_only)

### Stage 11 (parallel)

- `admin-auth-realism`: Enforce real admin control-plane auth and contain dev-bypass fallback. [$talos-backend-architect-agent]
- `dashboard-ws-stream-boundary`: Contain Dashboard legacy WebSocket stream boundary and auth. [$talos-frontend-developer-agent]
- `marketing-product-cta-parity`: Resolve Marketing product CTA, source link, and ownership parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `deployment-manifest-parity` blocked by admin-auth-realism (serial_only)
- `root-cli-command-parity` blocked by admin-auth-realism (serial_only)
- `deprecated-config-dash-retirement` blocked by admin-auth-realism (serial_only)
- `vulnerability-disclosure-parity` blocked by admin-auth-realism (serial_only)
- `marketing-docs-discovery-parity` blocked by marketing-product-cta-parity (shared_boundary:marketing-content)
- `marketing-availability-messaging` blocked by marketing-product-cta-parity (shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-product-cta-parity (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by dashboard-ws-stream-boundary (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by admin-auth-realism (serial_only), dashboard-ws-stream-boundary (serial_only; shared_boundary:dashboard-shell), marketing-product-cta-parity (serial_only)

### Stage 12 (serial)

- `deployment-manifest-parity`: Update deployment manifests (K8s/Helm) to match modern service topology. [$talos-infra-maintainer-agent]

Blocked candidates:
- `dashboard-onboarding-hardening` blocked by deployment-manifest-parity (serial_only)
- `dashboard-identity-propagation` blocked by deployment-manifest-parity (serial_only)
- `root-cli-command-parity` blocked by deployment-manifest-parity (serial_only)
- `deprecated-config-dash-retirement` blocked by deployment-manifest-parity (serial_only)
- `vulnerability-disclosure-parity` blocked by deployment-manifest-parity (serial_only)
- `marketing-docs-discovery-parity` blocked by deployment-manifest-parity (serial_only)
- `marketing-availability-messaging` blocked by deployment-manifest-parity (serial_only)
- `marketing-verification-drift-gate` blocked by deployment-manifest-parity (serial_only)
- `dashboard-verification-route-gate` blocked by deployment-manifest-parity (serial_only)
- `dashboard-shell-ownership` blocked by deployment-manifest-parity (serial_only)

### Stage 13 (parallel)

- `config-service-deployment`: Promote configuration service to first-class deployment status. [$talos-infra-maintainer-agent]
- `dashboard-onboarding-hardening`: Harden dashboard setup and agent-onboarding flows with real auth. [$talos-frontend-developer-agent]
- `marketing-docs-discovery-parity`: Resolve Marketing docs and whitepaper discovery surface parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `dashboard-identity-propagation` blocked by dashboard-onboarding-hardening (shared_boundary:dashboard-shell)
- `root-cli-command-parity` blocked by config-service-deployment (serial_only), dashboard-onboarding-hardening (serial_only)
- `deprecated-config-dash-retirement` blocked by config-service-deployment (serial_only), dashboard-onboarding-hardening (serial_only)
- `vulnerability-disclosure-parity` blocked by config-service-deployment (serial_only), dashboard-onboarding-hardening (serial_only)
- `marketing-availability-messaging` blocked by marketing-docs-discovery-parity (shared_boundary:marketing-content)
- `marketing-verification-drift-gate` blocked by marketing-docs-discovery-parity (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by dashboard-onboarding-hardening (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by config-service-deployment (serial_only), dashboard-onboarding-hardening (serial_only; shared_boundary:dashboard-shell), marketing-docs-discovery-parity (serial_only)

### Stage 14 (parallel)

- `dashboard-identity-propagation`: Implement consistent identity propagation from dashboard to gateway admin API. [$talos-frontend-developer-agent]
- `setup-helper-execution-realism`: Implement real setup-helper agent execution and credential handling. [$talos-parallel-orchestrator-agent]
- `marketing-availability-messaging`: Unify Marketing availability and lifecycle messaging consistency. [$talos-frontend-developer-agent]

Blocked candidates:
- `root-cli-command-parity` blocked by dashboard-identity-propagation (serial_only)
- `deprecated-config-dash-retirement` blocked by dashboard-identity-propagation (serial_only)
- `vulnerability-disclosure-parity` blocked by dashboard-identity-propagation (serial_only), setup-helper-execution-realism (serial_only)
- `marketing-verification-drift-gate` blocked by marketing-availability-messaging (shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by dashboard-identity-propagation (shared_boundary:dashboard-shell)
- `dashboard-shell-ownership` blocked by dashboard-identity-propagation (serial_only; shared_boundary:dashboard-shell), setup-helper-execution-realism (serial_only), marketing-availability-messaging (serial_only)
- `dashboard-auth-onboarding-parity` blocked by dashboard-identity-propagation (shared_boundary:dashboard-shell)

### Stage 15 (serial)

- `root-cli-command-parity`: Align root CLI command surface with documented operator vocabulary. [$talos-backend-architect-agent]

Blocked candidates:
- `deprecated-config-dash-retirement` blocked by root-cli-command-parity (serial_only)
- `vulnerability-disclosure-parity` blocked by root-cli-command-parity (serial_only)
- `marketing-verification-drift-gate` blocked by root-cli-command-parity (serial_only)
- `dashboard-verification-route-gate` blocked by root-cli-command-parity (serial_only)
- `dashboard-shell-ownership` blocked by root-cli-command-parity (serial_only)
- `dashboard-auth-onboarding-parity` blocked by root-cli-command-parity (serial_only)

### Stage 16 (serial)

- `deprecated-config-dash-retirement`: Retire deprecated configuration dashboard from active stack. [$talos-infra-maintainer-agent]

Blocked candidates:
- `vulnerability-disclosure-parity` blocked by deprecated-config-dash-retirement (serial_only)
- `examples-onboarding-api-parity` blocked by deprecated-config-dash-retirement (serial_only)
- `marketing-verification-drift-gate` blocked by deprecated-config-dash-retirement (serial_only)
- `dashboard-verification-route-gate` blocked by deprecated-config-dash-retirement (serial_only)
- `dashboard-shell-ownership` blocked by deprecated-config-dash-retirement (serial_only)
- `dashboard-auth-onboarding-parity` blocked by deprecated-config-dash-retirement (serial_only)

### Stage 17 (serial)

- `vulnerability-disclosure-parity`: Unify vulnerability disclosure channel and security policy parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `examples-onboarding-api-parity` blocked by vulnerability-disclosure-parity (serial_only)
- `marketing-verification-drift-gate` blocked by vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content)
- `dashboard-verification-route-gate` blocked by vulnerability-disclosure-parity (serial_only)
- `dashboard-shell-ownership` blocked by vulnerability-disclosure-parity (serial_only)
- `dashboard-auth-onboarding-parity` blocked by vulnerability-disclosure-parity (serial_only)

### Stage 18 (parallel)

- `examples-onboarding-api-parity`: Align examples, demo command, and Python onboarding API parity. [$talos-docs-parity]
- `marketing-verification-drift-gate`: Expand Marketing verification coverage and drift-gate parity. [$talos-frontend-developer-agent]
- `dashboard-verification-route-gate`: Add Dashboard verification coverage and route-integrity gate parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `dashboard-shell-ownership` blocked by examples-onboarding-api-parity (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only; shared_boundary:dashboard-shell)
- `dashboard-auth-onboarding-parity` blocked by dashboard-verification-route-gate (shared_boundary:dashboard-shell)

### Stage 19 (serial)

- `dashboard-shell-ownership`: Consolidate Dashboard shell ownership and version-surface parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `dashboard-auth-onboarding-parity` blocked by dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell)

### Stage 20 (serial)

- `dashboard-shell-nav-parity`: Resolve Dashboard shell navigation and stranded configuration UI parity. [$talos-frontend-developer-agent]

Blocked candidates:
- `dashboard-auth-onboarding-parity` blocked by dashboard-shell-nav-parity (shared_boundary:dashboard-shell)

### Stage 21 (serial)

- `dashboard-auth-onboarding-parity`: Align Dashboard auth onboarding surface and repo-local docs parity. [$talos-frontend-developer-agent]

## Task Details

### `a2a-interop-validation`

- Summary: Execute external A2A v1 live interop validation against official TCK and upstream targets.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/domain/a2a
- Runtime Resources: a2a-tck
- Verify: python3 scripts/python/run_a2a_upstream_interop.py --official-a2a-tck
- Done: Official TCK passes with zero mandatory failures.
- Conflicts: a2a-compat-retirement (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), ai-streaming-settle (shared_boundary:gateway-api), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), a2a-cap-validator-bootstrap (shared_boundary:gateway-api), phase15-reservation-cleanup (shared_boundary:gateway-api), phase13-secrets-rotation (shared_boundary:gateway-api), admin-auth-realism (shared_boundary:gateway-api), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `a2a-compat-retirement`

- Summary: Retire legacy A2A compat migration paths and move to strict v1 default.
- Suggested Skill: $talos-backend-architect-agent
- Depends On: a2a-interop-validation
- Writes: services/ai-gateway/app/settings.py, services/ai-gateway/app/api/a2a_v1/service.py
- Verify: pytest services/ai-gateway/tests/unit/api/test_a2a_v1_strict.py
- Done: Legacy aliases are removed and a2a_protocol_mode defaults to strict v1.
- Conflicts: a2a-interop-validation (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only; shared_boundary:gateway-api), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only; shared_writes:services/ai-gateway/app/settings.py; shared_boundary:gateway-api), phase15-reservation-cleanup (serial_only; shared_boundary:gateway-api), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only; shared_boundary:gateway-api), admin-auth-realism (serial_only; shared_boundary:gateway-api), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `gov-ownership-consolidation`

- Summary: Consolidate Governance-Agent ownership between standalone and gateway-embedded versions.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/governance-agent, services/ai-gateway/app/domain/tga
- Verify: pytest tests/test_tga_ownership.py
- Done: Single source of truth for TGA logic and storage exists.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-auth-log-completeness (serial_only; shared_writes:services/governance-agent; shared_boundary:governance-logic), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `gov-auth-log-completeness`

- Summary: Complete Governance-Agent deterministic authz and log artifact persistence.
- Suggested Skill: $talos-backend-architect-agent
- Depends On: gov-ownership-consolidation
- Writes: services/governance-agent/src/talos_governance_agent/domain
- Verify: pytest services/governance-agent/tests/test_audit_chain.py
- Done: Deterministic constraint validation and full log coverage are implemented.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only; shared_writes:services/governance-agent; shared_boundary:governance-logic), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `terminal-trust-enforcement`

- Summary: Implement real Ed25519 signature verification and TGA-backed trust for terminal-adapter.
- Suggested Skill: $talos-backend-architect-agent
- Depends On: gov-auth-log-completeness
- Writes: services/terminal-adapter/src/terminal_adapter/domain
- Verify: pytest services/terminal-adapter/tests/test_trust_enforcement.py
- Done: Ed25519 verification is active and placeholder decisions are replaced.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `ai-streaming-settle`

- Summary: Implement public AI streaming with settle-on-end semantics and accounting.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/api/public_ai
- Verify: pytest services/ai-gateway/tests/integration/test_public_ai_streaming.py
- Done: Streaming responses are supported with full rate-limit and audit parity.
- Conflicts: a2a-interop-validation (shared_boundary:gateway-api), a2a-compat-retirement (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), a2a-cap-validator-bootstrap (shared_boundary:gateway-api), phase15-reservation-cleanup (shared_boundary:gateway-api), phase13-secrets-rotation (shared_boundary:gateway-api), admin-auth-realism (shared_boundary:gateway-api), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `ts-transport-completion`

- Summary: Complete TypeScript Core transport implementation for TalosClient.
- Suggested Skill: $talos-sdk-parity
- Writes: sdks/typescript/packages/sdk/src/core
- Verify: cd sdks/typescript && npm test
- Done: TalosClient performs real wire-protocol send/receive.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), decentralized-did-resolution (shared_boundary:sdk-core), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), did-dht-api-parity (shared_boundary:sdk-core), dashboard-shell-ownership (serial_only)

### `decentralized-did-resolution`

- Summary: Implement decentralized DID resolution via DHT lookup.
- Suggested Skill: $talos-sdk-parity
- Writes: src/core/did.py
- Verify: pytest tests/test_did_resolution.py
- Done: resolve_did() returns DHT results instead of placeholders.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), ts-transport-completion (shared_boundary:sdk-core), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only; shared_writes:src), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), did-dht-api-parity (shared_writes:src/core/did.py; shared_boundary:sdk-core), dashboard-shell-ownership (serial_only)

### `ucp-error-taxonomy`

- Summary: Align UCP Connector error-taxonomy with contract specifications.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ucp-connector/src/talos_ucp_connector/domain
- Verify: pytest services/ucp-connector/tests/test_error_taxonomy.py
- Done: Callers receive stable contract-level errors instead of raw exceptions.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), public-ucp-commerce-parity (shared_boundary:ucp-logic), dashboard-shell-ownership (serial_only)

### `gateway-topology-consolidation`

- Summary: Consolidate gateway topology and align scripts/dashboard around ai-gateway.
- Suggested Skill: $talos-infra-maintainer-agent
- Writes: README.md, start.sh, deploy/scripts/common.sh, site/dashboard/.env.example
- Verify: ./start.sh --check-topology
- Done: Root scripts and dashboard point to the canonical ai-gateway topology.
- Conflicts: a2a-interop-validation (serial_only; shared_boundary:gateway-api), a2a-compat-retirement (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only; shared_boundary:gateway-api), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only; shared_writes:README.md), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only; shared_boundary:gateway-api), phase15-reservation-cleanup (serial_only; shared_boundary:gateway-api), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only; shared_boundary:gateway-api), admin-auth-realism (serial_only; shared_boundary:gateway-api), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only; shared_writes:deploy/scripts/common.sh), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `external-audit-anchoring`

- Summary: Implement external audit anchoring pipeline and verification flow.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/audit/src/domain, src/core/validation/layers.py
- Verify: pytest services/audit/tests/test_anchoring.py
- Done: Merkle proofs can be verified against an external anchor signal.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only; shared_writes:src), service-port-consolidation (serial_only), audit-hardening-sink (shared_boundary:audit-logic), deployment-manifest-parity (serial_only), audit-explorer-parity (shared_boundary:audit-logic), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `legacy-src-boundary`

- Summary: Define legacy src/ boundary and separate it from active service narrative.
- Suggested Skill: $talos-docs-parity
- Writes: src, docs/api/api-reference.md
- Verify: rg "LEGACY" src/
- Done: Legacy P2P stack is clearly marked and isolated from modern stack docs.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only; shared_writes:src), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (serial_only; shared_writes:src), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only; shared_writes:src), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only; shared_writes:src), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `service-port-consolidation`

- Summary: Establish and align canonical service port map across all services and docs.
- Suggested Skill: $talos-backend-architect-agent
- Writes: README.md, services/audit/src/main.py, services/configuration/main.py, site/dashboard/src/lib/config.ts
- Verify: grep -r "8001" services/audit
- Done: All services, dashboard, and docs use the same consistent port map.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only; shared_writes:README.md), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only; shared_writes:site/dashboard/src/lib/config.ts), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only; shared_writes:site/dashboard/src/lib/config.ts), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `mcp-secure-tunnel`

- Summary: Implement secure-session tunnel for active MCP connector transport.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/mcp-connector/src/talos_mcp/transport
- Verify: pytest services/mcp-connector/tests/test_secure_tunnel.py
- Done: Double Ratchet tunnel is active for tool invocations.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `a2a-cap-validator-bootstrap`

- Summary: Unify A2A capability validator bootstrap and configuration keys.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/dependencies.py, services/ai-gateway/app/settings.py
- Verify: pytest services/ai-gateway/tests/unit/test_validator_bootstrap.py
- Done: TGA_SUPERVISOR_PUBLIC_KEY is used consistently for capability validation.
- Conflicts: a2a-interop-validation (shared_boundary:gateway-api), a2a-compat-retirement (serial_only; shared_writes:services/ai-gateway/app/settings.py; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), ai-streaming-settle (shared_boundary:gateway-api), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), phase15-reservation-cleanup (shared_boundary:gateway-api), audit-hardening-sink (shared_writes:services/ai-gateway/app/dependencies.py), phase13-secrets-rotation (shared_boundary:gateway-api), admin-auth-realism (shared_boundary:gateway-api), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `phase15-reservation-cleanup`

- Summary: Implement Phase 15 budget reservation cleanup and drift reconcile.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/jobs/budget_cleanup.py, services/ai-gateway/app/domain/budgets/service.py
- Verify: pytest services/ai-gateway/tests/unit/test_budget_cleanup.py
- Done: Expired reservations are released and drift is reconciled.
- Conflicts: a2a-interop-validation (shared_boundary:gateway-api), a2a-compat-retirement (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), ai-streaming-settle (shared_boundary:gateway-api), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), a2a-cap-validator-bootstrap (shared_boundary:gateway-api), phase13-secrets-rotation (shared_boundary:gateway-api), admin-auth-realism (shared_boundary:gateway-api), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `audit-hardening-sink`

- Summary: Hardening audit sink bootstrap and HMAC key fail-closed behavior.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/domain/audit.py, services/ai-gateway/app/dependencies.py
- Verify: pytest services/ai-gateway/tests/unit/test_audit_hardening.py
- Done: Fail-closed production mode is enforced for audit logs and sinks.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (shared_boundary:audit-logic), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), a2a-cap-validator-bootstrap (shared_writes:services/ai-gateway/app/dependencies.py), deployment-manifest-parity (serial_only), audit-explorer-parity (shared_boundary:audit-logic), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `phase13-secrets-rotation`

- Summary: Consolidate Phase 13 secrets rotation ownership and provider contract.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/adapters/secrets/multi_provider.py, docs/features/operations/secrets-rotation.md
- Verify: pytest services/ai-gateway/tests/unit/test_secrets_rotation.py
- Done: Single KEK-provider exists and admin endpoints match documentation.
- Conflicts: a2a-interop-validation (shared_boundary:gateway-api), a2a-compat-retirement (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), ai-streaming-settle (shared_boundary:gateway-api), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), a2a-cap-validator-bootstrap (shared_boundary:gateway-api), phase15-reservation-cleanup (shared_boundary:gateway-api), admin-auth-realism (shared_boundary:gateway-api), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `admin-auth-realism`

- Summary: Enforce real admin control-plane auth and contain dev-bypass fallback.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/ai-gateway/app/middleware/auth_admin.py, services/ai-gateway/app/dashboard/router.py
- Verify: pytest services/ai-gateway/tests/unit/test_admin_auth.py
- Done: JWT/RBAC is enforced for admin plane without implicit fallbacks.
- Conflicts: a2a-interop-validation (shared_boundary:gateway-api), a2a-compat-retirement (serial_only; shared_boundary:gateway-api), gov-ownership-consolidation (serial_only), ai-streaming-settle (shared_boundary:gateway-api), gateway-topology-consolidation (serial_only; shared_boundary:gateway-api), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), a2a-cap-validator-bootstrap (shared_boundary:gateway-api), phase15-reservation-cleanup (shared_boundary:gateway-api), phase13-secrets-rotation (shared_boundary:gateway-api), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `deployment-manifest-parity`

- Summary: Update deployment manifests (K8s/Helm) to match modern service topology.
- Suggested Skill: $talos-infra-maintainer-agent
- Depends On: gateway-topology-consolidation, service-port-consolidation
- Writes: deploy/k8s/base, deploy/helm/talos
- Verify: helm lint deploy/helm/talos
- Done: Helm and Kustomize manifests include ai-gateway and other core services.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), config-service-deployment (serial_only; shared_writes:deploy/k8s/base), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `config-service-deployment`

- Summary: Promote configuration service to first-class deployment status.
- Suggested Skill: $talos-infra-maintainer-agent
- Depends On: deployment-manifest-parity
- Writes: deploy/k8s/base/configuration, deploy/k8s/base/kustomization.yaml
- Verify: kubectl kustomize deploy/k8s/base | grep configuration
- Done: Configuration service has its own deployment manifest and ingress wiring.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only; shared_writes:deploy/k8s/base), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `audit-explorer-parity`

- Summary: Align Audit Explorer product surface with documented proof workflows.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/src/app/api/audit, docs/features/observability/audit-explorer.md
- Verify: cd site/dashboard && npm test
- Done: Proof-verification flows are available in the dashboard and CLI.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (shared_boundary:audit-logic), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), audit-hardening-sink (shared_boundary:audit-logic), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `dashboard-onboarding-hardening`

- Summary: Harden dashboard setup and agent-onboarding flows with real auth.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: admin-auth-realism
- Writes: site/dashboard/src/app/api/setup, site/dashboard/src/lib/setup-gate.ts
- Verify: cd site/dashboard && npm test
- Done: Setup token and job APIs require admin session verification.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `security-dashboard-auth-parity`

- Summary: Align security dashboard auth and runtime-mode documentation.
- Suggested Skill: $talos-docs-parity
- Writes: docs/security/security-dashboard.md, site/dashboard/src/lib/config.ts
- Verify: cd site/dashboard && npm run typecheck
- Done: Docs describe real WebAuthn flow and supported runtime modes.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only; shared_writes:site/dashboard/src/lib/config.ts), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_writes:site/dashboard/src/lib/config.ts; shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `dashboard-identity-propagation`

- Summary: Implement consistent identity propagation from dashboard to gateway admin API.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: admin-auth-realism
- Writes: site/dashboard/src/app/api/admin
- Verify: cd site/dashboard && npm test
- Done: Principal/bearer tokens are propagated across all admin proxies.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_writes:site/dashboard/src/app/api/admin; shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `dashboard-api-namespace-parity`

- Summary: Resolve Dashboard control-plane API namespace parity and proxy routes.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/src/app/api/admin/v1, site/dashboard/src/lib/data/HttpDataSource.ts
- Verify: cd site/dashboard && npm run build
- Done: All management UI pages have matching implemented proxy routes.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_writes:site/dashboard/src/app/api/admin; shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `root-cli-command-parity`

- Summary: Align root CLI command surface with documented operator vocabulary.
- Suggested Skill: $talos-backend-architect-agent
- Writes: src/client/cli.py, pyproject.toml
- Verify: talos audit --help
- Done: Root CLI exposes documented audit and operator subcommands.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only; shared_writes:src), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `demo-examples-parity`

- Summary: Resolve Demo and Examples product-surface and manifest parity.
- Suggested Skill: $talos-docs-parity
- Writes: examples/examples_manifest.json, site/dashboard/src/app/api/examples/manifest/route.ts
- Verify: pytest tests/test_examples_manifest.py
- Done: Dashboard reads canonical manifest and demo commands work.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `secure-chat-crypto-audit`

- Summary: Achieve cryptographic and audit reality for Secure Chat demo.
- Suggested Skill: $talos-backend-architect-agent
- Depends On: mcp-secure-tunnel
- Writes: services/ai-chat-agent/api/src/main.py, site/dashboard/src/app/api/examples/chat
- Verify: pytest services/ai-chat-agent/tests/test_crypto_audit.py
- Done: Demo chat is genuinely encrypted and reports real audit proofs.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `dashboard-secure-agent-shell`

- Summary: Align Dashboard Secure-Agent shell with active chat-agent contract.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/src/app/(shell)/agent, site/dashboard/src/app/api/agent
- Verify: cd site/dashboard && npm test
- Done: Agent shell uses stable backend contracts and real capability discovery.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `devops-example-aiops-parity`

- Summary: Align DevOps example API and AIOps backend contract parity.
- Suggested Skill: $talos-backend-architect-agent
- Writes: services/aiops/api/src/main.py, site/dashboard/src/app/api/examples/devops
- Verify: pytest services/aiops/tests/test_api_parity.py
- Done: DevOps dashboard uses the real job-control and log contract from AIOps.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `deprecated-config-dash-retirement`

- Summary: Retire deprecated configuration dashboard from active stack.
- Suggested Skill: $talos-infra-maintainer-agent
- Writes: deploy/scripts/common.sh, deploy/submodules.json
- Verify: grep -v "configuration-dashboard" deploy/scripts/common.sh
- Done: Legacy dashboard is removed from deployment and operator docs.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only; shared_writes:deploy/scripts/common.sh), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `dashboard-playground-gateway`

- Summary: Align AI Playground with real gateway and response shape parity.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: ai-streaming-settle
- Writes: site/dashboard/src/app/(shell)/llm/playground, site/dashboard/src/lib/data/HttpDataSource.ts
- Verify: cd site/dashboard && npm test
- Done: Playground exercises real gateway model-group routing and audit.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), mission-control-kpi-truth (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `mission-control-kpi-truth`

- Summary: Ensure Mission Control KPI and analytics truthfulness in Dashboard.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/src/lib/data/HttpDataSource.ts, site/dashboard/src/components/dashboard/KPIGrid.tsx
- Verify: cd site/dashboard && npm test
- Done: Visible KPIs are derived from real backend-reported aggregates.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_writes:site/dashboard/src/lib/data/HttpDataSource.ts; shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `marketing-catalog-content`

- Summary: Audit and align Marketing Site product catalog and content ownership.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/marketing/src/content/products.json, site/marketing/src/app/docs
- Verify: cd site/marketing && npm run validate:claims
- Done: Product catalog maturity labels and content match verified repo state.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-product-cta-parity (shared_writes:site/marketing/src/content/products.json; shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_writes:site/marketing/src/app/docs; shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `setup-helper-execution-realism`

- Summary: Implement real setup-helper agent execution and credential handling.
- Suggested Skill: $talos-parallel-orchestrator-agent
- Depends On: dashboard-onboarding-hardening
- Writes: tools/setup-helper/talos_setup_helper/agent.py, tools/setup-helper/talos_setup_helper/auth.py
- Verify: pytest tools/setup-helper/tests/test_agent_realism.py
- Done: Setup agent executes real recipes and uses secure credential rotation.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `talos-tui-parity`

- Summary: Align Talos TUI with active-stack parity and fix runtime bugs.
- Suggested Skill: $talos-parallel-orchestrator-agent
- Depends On: service-port-consolidation
- Writes: tools/talos-tui/python/src/talos_tui/adapters, tools/talos-tui/python/src/talos_tui/domain/models.py
- Verify: cd tools/talos-tui && make test
- Done: TUI uses owned gateway APIs and metrics; Health.ok bug is fixed.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `marketing-benchmark-source`

- Summary: Align Marketing benchmark claim source-of-truth with repo artifacts.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/marketing/src/content/claims.json, site/marketing/src/lib/validate-claims.ts
- Verify: cd site/marketing && npm run validate:claims
- Done: Public benchmarks are generated from repo-owned output files.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_boundary:marketing-content), marketing-security-guarantee (shared_writes:site/marketing/src/content/claims.json; shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `marketing-security-guarantee`

- Summary: Align Marketing security page guarantees and metric parity.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: mcp-secure-tunnel, marketing-benchmark-source
- Writes: site/marketing/src/app/security/page.tsx, site/marketing/src/content/claims.json
- Verify: cd site/marketing && npm run build
- Done: Security page numbers are source-backed and claims are verified.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_boundary:marketing-content), marketing-benchmark-source (shared_writes:site/marketing/src/content/claims.json; shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `vulnerability-disclosure-parity`

- Summary: Unify vulnerability disclosure channel and security policy parity.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: SECURITY.md, site/marketing/public/.well-known/security.txt
- Verify: grep "security@talosprotocol.com" SECURITY.md
- Done: Authoritative disclosure contact is consistent across all surfaces.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only), security-dashboard-auth-parity (serial_only), dashboard-identity-propagation (serial_only), dashboard-api-namespace-parity (serial_only), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only), mission-control-kpi-truth (serial_only), marketing-catalog-content (serial_only; shared_boundary:marketing-content), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only; shared_boundary:marketing-content), marketing-security-guarantee (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (serial_only; shared_boundary:marketing-content), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only; shared_boundary:marketing-content), dashboard-ws-stream-boundary (serial_only), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only; shared_boundary:marketing-content), marketing-docs-discovery-parity (serial_only; shared_boundary:marketing-content), marketing-availability-messaging (serial_only; shared_boundary:marketing-content), dashboard-shell-nav-parity (serial_only), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only; shared_boundary:marketing-content), dashboard-verification-route-gate (serial_only), dashboard-shell-ownership (serial_only), dashboard-auth-onboarding-parity (serial_only)

### `marketing-dev-sdk-example`

- Summary: Align Marketing developers page SDK examples and onboarding parity.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: ts-transport-completion
- Writes: site/marketing/src/app/developers/page.tsx
- Verify: cd site/marketing && npm run build
- Done: Developers page shows current exported APIs and method names.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_boundary:marketing-content), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `public-ucp-commerce-parity`

- Summary: Align public UCP commerce positioning with connector reality.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: ucp-error-taxonomy
- Writes: site/marketing/src/components/UCPFeature.tsx, services/ucp-connector/README.md
- Verify: cd site/marketing && npm run build
- Done: UCP commerce claims match the allowlist-driven checkout scope.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), ucp-error-taxonomy (shared_boundary:ucp-logic), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `marketing-roadmap-live-status`

- Summary: Align Marketing roadmap versioning and 'LIVE' status parity.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: decentralized-did-resolution
- Writes: site/marketing/src/app/roadmap/page.tsx, docs/research/roadmap.md
- Verify: cd site/marketing && npm run build
- Done: Marketing roadmap matches repo-owned roadmap and verified features.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_boundary:marketing-content), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_writes:site/marketing/src/app/roadmap/page.tsx; shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `dashboard-ws-stream-boundary`

- Summary: Contain Dashboard legacy WebSocket stream boundary and auth.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/src/lib/data/WsDataSource.ts, site/dashboard/src/lib/config.ts
- Verify: cd site/dashboard && npm test
- Done: Direct browser WebSocket path is removed or properly hardened.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only; shared_writes:site/dashboard/src/lib/config.ts), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_writes:site/dashboard/src/lib/config.ts; shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `did-dht-api-parity`

- Summary: Align DID/DHT user-facing API and high-level example parity.
- Suggested Skill: $talos-sdk-parity
- Depends On: decentralized-did-resolution
- Writes: src/core/did.py, examples/06_dht.py
- Verify: pytest examples/06_dht.py
- Done: Core DID API uses DHT resolver for high-level resolution flow.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), ts-transport-completion (shared_boundary:sdk-core), decentralized-did-resolution (shared_writes:src/core/did.py; shared_boundary:sdk-core), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only; shared_writes:src), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `examples-onboarding-api-parity`

- Summary: Align examples, demo command, and Python onboarding API parity.
- Suggested Skill: $talos-docs-parity
- Depends On: root-cli-command-parity
- Writes: examples/README.md, docs/getting-started/quickstart.md
- Verify: bash examples/scripts/test.sh
- Done: Quickstart docs match the currently shipped CLI and SDK client.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `marketing-product-cta-parity`

- Summary: Resolve Marketing product CTA, source link, and ownership parity.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/marketing/src/content/products.json, site/marketing/src/components/products/ProductCard.tsx
- Verify: cd site/marketing && npm run build
- Done: Product CTAs link to owned onboarding flows or monorepo paths.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_writes:site/marketing/src/content/products.json; shared_boundary:marketing-content), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `marketing-docs-discovery-parity`

- Summary: Resolve Marketing docs and whitepaper discovery surface parity.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/marketing/src/components/Navbar.tsx, site/marketing/src/app/docs
- Verify: cd site/marketing && npm run build
- Done: One canonical docs entry path exists across navbar and homepage.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_writes:site/marketing/src/app/docs; shared_boundary:marketing-content), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `marketing-availability-messaging`

- Summary: Unify Marketing availability and lifecycle messaging consistency.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/marketing/src/app/contact/page.tsx, site/marketing/src/app/roadmap/page.tsx
- Verify: cd site/marketing && npm run build
- Done: Availability story (GA vs Beta) is consistent across all pages.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_boundary:marketing-content), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_writes:site/marketing/src/app/roadmap/page.tsx; shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-verification-drift-gate (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `dashboard-shell-nav-parity`

- Summary: Resolve Dashboard shell navigation and stranded configuration UI parity.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: dashboard-shell-ownership
- Writes: site/dashboard/src/components/layout/DashboardSidebar.tsx, site/dashboard/src/app/(shell)/configuration
- Verify: cd site/dashboard && npm run build
- Done: Navigation links point at real pages and stranded mock UI is retired.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `docs-home-status-metrics`

- Summary: Align Docs Home status metrics and architecture framing parity.
- Suggested Skill: $talos-docs-parity
- Writes: docs/README-Home.md
- Verify: grep "Verified Tests" docs/README-Home.md
- Done: Project Health metrics are derived from real repo-owned sources.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), vulnerability-disclosure-parity (serial_only), dashboard-shell-ownership (serial_only)

### `marketing-verification-drift-gate`

- Summary: Expand Marketing verification coverage and drift-gate parity.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/marketing/scripts/ci-verify.sh, site/marketing/scripts/smoke-test-routes.js
- Verify: bash site/marketing/scripts/ci-verify.sh
- Done: CI gate validates products.json and all reachable public routes.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), root-cli-command-parity (serial_only), deprecated-config-dash-retirement (serial_only), marketing-catalog-content (shared_boundary:marketing-content), marketing-benchmark-source (shared_boundary:marketing-content), marketing-security-guarantee (shared_boundary:marketing-content), vulnerability-disclosure-parity (serial_only; shared_boundary:marketing-content), marketing-dev-sdk-example (shared_boundary:marketing-content), marketing-roadmap-live-status (shared_boundary:marketing-content), marketing-product-cta-parity (shared_boundary:marketing-content), marketing-docs-discovery-parity (shared_boundary:marketing-content), marketing-availability-messaging (shared_boundary:marketing-content), dashboard-shell-ownership (serial_only)

### `dashboard-verification-route-gate`

- Summary: Add Dashboard verification coverage and route-integrity gate parity.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/package.json, site/dashboard/src/__tests__/integrity
- Verify: cd site/dashboard && npm run test
- Done: CI gate fails when dashboard links point to missing routes.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (shared_boundary:dashboard-shell)

### `dashboard-shell-ownership`

- Summary: Consolidate Dashboard shell ownership and version-surface parity.
- Suggested Skill: $talos-frontend-developer-agent
- Writes: site/dashboard/src/components/layout/AppShell.tsx, site/dashboard/src/lib/navRegistry.ts
- Verify: cd site/dashboard && npm test
- Done: Single shell implementation owns navigation, version, and docs links.
- Conflicts: a2a-interop-validation (serial_only), a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gov-auth-log-completeness (serial_only), terminal-trust-enforcement (serial_only), ai-streaming-settle (serial_only), ts-transport-completion (serial_only), decentralized-did-resolution (serial_only), ucp-error-taxonomy (serial_only), gateway-topology-consolidation (serial_only), external-audit-anchoring (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), mcp-secure-tunnel (serial_only), a2a-cap-validator-bootstrap (serial_only), phase15-reservation-cleanup (serial_only), audit-hardening-sink (serial_only), phase13-secrets-rotation (serial_only), admin-auth-realism (serial_only), deployment-manifest-parity (serial_only), config-service-deployment (serial_only), audit-explorer-parity (serial_only), dashboard-onboarding-hardening (serial_only; shared_boundary:dashboard-shell), security-dashboard-auth-parity (serial_only; shared_boundary:dashboard-shell), dashboard-identity-propagation (serial_only; shared_boundary:dashboard-shell), dashboard-api-namespace-parity (serial_only; shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), demo-examples-parity (serial_only), secure-chat-crypto-audit (serial_only), dashboard-secure-agent-shell (serial_only; shared_boundary:dashboard-shell), devops-example-aiops-parity (serial_only), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (serial_only; shared_boundary:dashboard-shell), mission-control-kpi-truth (serial_only; shared_boundary:dashboard-shell), marketing-catalog-content (serial_only), setup-helper-execution-realism (serial_only), talos-tui-parity (serial_only), marketing-benchmark-source (serial_only), marketing-security-guarantee (serial_only), vulnerability-disclosure-parity (serial_only), marketing-dev-sdk-example (serial_only), public-ucp-commerce-parity (serial_only), marketing-roadmap-live-status (serial_only), dashboard-ws-stream-boundary (serial_only; shared_boundary:dashboard-shell), did-dht-api-parity (serial_only), examples-onboarding-api-parity (serial_only), marketing-product-cta-parity (serial_only), marketing-docs-discovery-parity (serial_only), marketing-availability-messaging (serial_only), dashboard-shell-nav-parity (serial_only; shared_boundary:dashboard-shell), docs-home-status-metrics (serial_only), marketing-verification-drift-gate (serial_only), dashboard-verification-route-gate (serial_only; shared_boundary:dashboard-shell), dashboard-auth-onboarding-parity (serial_only; shared_boundary:dashboard-shell)

### `dashboard-auth-onboarding-parity`

- Summary: Align Dashboard auth onboarding surface and repo-local docs parity.
- Suggested Skill: $talos-frontend-developer-agent
- Depends On: dashboard-onboarding-hardening
- Writes: site/dashboard/README.md, site/dashboard/src/app/signup/page.tsx
- Verify: cd site/dashboard && npm test
- Done: Local docs match the passkey auth model and DB requirements.
- Conflicts: a2a-compat-retirement (serial_only), gov-ownership-consolidation (serial_only), gateway-topology-consolidation (serial_only), legacy-src-boundary (serial_only), service-port-consolidation (serial_only), deployment-manifest-parity (serial_only), dashboard-onboarding-hardening (shared_boundary:dashboard-shell), security-dashboard-auth-parity (shared_boundary:dashboard-shell), dashboard-identity-propagation (shared_boundary:dashboard-shell), dashboard-api-namespace-parity (shared_boundary:dashboard-shell), root-cli-command-parity (serial_only), dashboard-secure-agent-shell (shared_boundary:dashboard-shell), deprecated-config-dash-retirement (serial_only), dashboard-playground-gateway (shared_boundary:dashboard-shell), mission-control-kpi-truth (shared_boundary:dashboard-shell), vulnerability-disclosure-parity (serial_only), dashboard-ws-stream-boundary (shared_boundary:dashboard-shell), dashboard-shell-nav-parity (shared_boundary:dashboard-shell), dashboard-verification-route-gate (shared_boundary:dashboard-shell), dashboard-shell-ownership (serial_only; shared_boundary:dashboard-shell)

## Monitoring

- Poll active lanes for new overlap in writes, generated outputs, and runtime resources.
- Collapse back to serial execution if a later prerequisite mutates an active lane's inputs.
- Run one merged verification pass after the final stage completes.

