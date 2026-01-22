# talos-ucp-connector — implementation_plan.md

Status: DRAFT (Architect Review)
Owner: Talos Protocol
Implementor: Google Antigravity
Target UCP Version: 2026-01-11

## 1. Objective

Add first-class support for Universal Commerce Protocol (UCP) to the Talos ecosystem by building a dedicated MCP server connector that:
- Discovers UCP-enabled merchants via `/.well-known/ucp`
- Executes UCP Shopping “checkout session” flows over REST (and optionally UCP MCP binding later)
- Emits Talos-audited, policy-constrained commerce tool actions usable by Talos agents

## 2. Background and normative constraints (must-follow)

### 2.1 Discovery
- Merchant capabilities and endpoints are discovered through the UCP profile at:
  - `https://<merchant>/.well-known/ucp`
- REST base URL for Shopping service is discovered in:
  - `services["dev.ucp.shopping"].rest.endpoint`
Ref: UCP REST binding and Shopping OpenAPI.  
Citations: UCP REST binding describes base URL discovery via the profile. UCP shopping OpenAPI requires base URL from the discovery profile. :contentReference[oaicite:6]{index=6}

### 2.2 Transport security
- All UCP REST endpoints must use HTTPS with minimum TLS 1.3. :contentReference[oaicite:7]{index=7}

### 2.3 Required headers and signing
- REST requests require `Request-Signature` and `Request-Id`. Mutations require `Idempotency-Key`. :contentReference[oaicite:8]{index=8}
- Webhook payloads must be signed with a detached JWT (RFC 7797) and verified using `signing_keys` from the merchant profile. :contentReference[oaicite:9]{index=9}

### 2.4 UCP scope reality (v2026-01-11)
Initial UCP launch emphasizes Checkout, Identity Linking, and Order management. Product discovery/search is not guaranteed as a first-class API in the canonical shopping REST spec. :contentReference[oaicite:10]{index=10}

### 2.5 Negotiation and schema composition (must-follow)
- Platforms MUST advertise `UCP-Agent: profile="https://…"` on every REST request (RFC 8941 dict). :contentReference[oaicite:1]{index=1}
- Platforms MUST validate namespace authority for capability `spec` and `schema` URIs. :contentReference[oaicite:1]{index=1}
- Platforms MUST resolve and compose schemas client-side (base + extensions) and validate all requests/responses against the composed schema. :contentReference[oaicite:1]{index=1}

### 2.6 Security Defaults
- Strict network guards required: forbid IP literals/private ranges/redirects; enforce TLS 1.3.
- Key type: Standardize on **ES256**.
- Signing: Enforce `Request-Signature` (REST) and detached JWT verification (Webhooks).

## 3. Non-goals (v1)
- Building a universal product search engine across merchants
- Supporting every optional UCP extension on day 1 (AP2 mandates, discounts, fulfillment, etc.)
- Local-only deployment where merchants cannot fetch platform profile URLs or deliver webhooks

## 4. Repository and boundary strategy

### 4.1 Where the code lives
Preferred: new repo `talos-ucp-connector` (standalone, no deep links into other repos).  
Alternative: a dedicated module inside `talos-mcp-connector` if we want a single connector distribution surface.

Hard rules:
- No cross-repo source imports
- All shared schemas and test vectors MUST live in `talos-contracts` and be consumed as versioned artifacts

### 4.2 Contract-first deliverables (blocking)
Add UCP-related artifacts to `talos-contracts`:
- `schemas/ucp/2026-01-11/profile.schema.json` (business profile shape)
- `schemas/ucp/2026-01-11/platform_profile.schema.json` (Talos platform profile shape)
- Snapshot copies (vendored) of:
  - `services/shopping/rest.openapi.json`
  - `schemas/shopping/*` (checkout, payment_data, order, etc.)
- `test_vectors/ucp/2026-01-11/`:
  - Example `/.well-known/ucp` profile
  - Signed webhook examples (good signature, bad signature, rotated key)
  - Checkout create/update/complete flows with deterministic canonical JSON bytes

CI gate:
- Schema validation + vector verification must pass before connector merges.

## 5. System architecture

### 5.1 Component overview
`talos-ucp-connector` is an MCP Server that exposes commerce tools to Talos agents and maps them to UCP operations.

Core modules:
- NegotiationEngine
  - Advertises platform profile URI (`UCP-Agent` header)
  - Caches business profile using HTTP cache-control
  - Validates business response includes `ucp` metadata
  - Tracks negotiated capability set
- SchemaResolver
  - Fetches base schema(s) + active extensions
  - Composes runtime validators (JSON Schema `allOf`)
  - Validates outbound requests & inbound responses (fail closed)
- NamespaceValidator
  - Enforces authority checks (e.g. `dev.ucp.*` -> `ucp.dev`)
- OutboundNetworkGuard
  - SSRF protection: DNS resolution checks, no private IPs
  - TLS 1.3 enforcement
  - No redirects (or strict same-origin)
- DiscoveryClient
  - Fetches and validates `/.well-known/ucp`
- RequestSigner (platform-side)
  - Builds detached JWT (RFC 7797) using **ES256**
- CheckoutClient (REST)
  - Enforces idempotency and retry semantics
- WebhookServer (Phase 2+)
  - Verifies merchant signature using `signing_keys`
- PolicyEngineAdapter
  - Maps Talos capability constraints to runtime checks

### 5.2 Deployment modes
Mode A (recommended): Hosted connector in Talos infra with public HTTPS ingress.
- Required for merchant fetch of platform profile URL and for order webhooks.

Mode B (limited): Local connector for read-only experimentation.
- Allowed only if we avoid flows requiring merchant callbacks and we use a publicly reachable, static platform profile URL.

## 6. MCP tool surface (v1)

Because UCP shopping REST is checkout-centric, v1 tools align to those operations:

- ucp_discover(merchant_domain)
  - Returns normalized merchant profile summary + supported capabilities

- ucp_checkout_create(merchant_domain, line_items, currency, buyer_context?)
  - Calls POST /checkout-sessions

- ucp_checkout_get(merchant_domain, checkout_id)
  - Calls GET /checkout-sessions/{id}

- ucp_checkout_update(merchant_domain, checkout_id, checkout_patch)
  - Calls PUT /checkout-sessions/{id}

- ucp_checkout_complete(merchant_domain, checkout_id, payment_data, risk_signals?)
  - Calls POST /checkout-sessions/{id}/complete

- ucp_checkout_cancel(merchant_domain, checkout_id)
  - Calls POST /checkout-sessions/{id}/cancel

Optional (explicitly “non-normative” for UCP v1):
- ucp_search(...)
  - Only if we define a separate catalog/feed strategy and label it “best-effort”.

## 7. Talos security, auditing, and privacy

### 7.1 Talos envelope and audit
Every tool call emits:
- A Talos audit event with:
  - merchant domain
  - operation name
  - negotiated capability set + versions
  - platform profile URI (hash or exact if non-sensitive)
  - `Request-Id` and `Idempotency-Key` (safe to store)
  - deterministic hash of request payload (canonical JSON)
  - deterministic hash of response payload (canonical JSON)
  - result status mapping (success/failure/denied)

Do NOT store:
- full buyer PII
- payment instruments/tokens
- email, phone, address (hash or omit)
Store only hashes or redacted summaries.

### 7.2 Capability constraints (examples)
Constraints enforced before any network call:
- allowed_merchants: domain allowlist with safe matching (no naive suffix checks)
- max_spend_minor: integer in minor units, compare against checkout totals
- allowed_currency: ["USD"]
- allowed_payment_handlers: ["com.google.pay"]
- require_buyer_consent: true (ties into future AP2 / consent extensions)

### 7.3 Request signing keys
Platform key material:
- Stored in Talos secrets system
- Rotatable, with key ids
- Request-Signature is mandatory for REST calls. :contentReference[oaicite:11]{index=11}

Merchant webhook verification:
- Verify detached JWT signatures using merchant `signing_keys` from `/.well-known/ucp`. :contentReference[oaicite:12]{index=12}

## 8. Implementation roadmap

### Phase 0 (BLOCKING): Contracts + vectors
Deliverables:
- `talos-contracts` UCP schemas + vendored OpenAPI + test vectors
- CI: schema validation + vector verification
Exit criteria:
- Green CI gates
- Cross-language signature verification vectors pass (at least Python + TS)

### Phase 1: Discovery + Checkout REST (no webhooks)
Deliverables:
- MCP server with tools:
  - discover, checkout_create/get/update/complete/cancel
- REST client:
  - Discovers endpoint from profile
  - Adds required headers (Request-Id, Idempotency-Key, Request-Signature, UCP-Agent profile)
  - Retries with idempotency guarantees
Exit criteria:
- Integration test against a reference merchant implementation
- Audit events emitted with redaction and deterministic hashes

### Phase 2: Payment handlers via WalletProvider abstraction
Goal:
- Provide a safe interface for obtaining “opaque credentials” required by `payment_data`, consistent with the UCP payment model (credentials flow Platform → Business only). :contentReference[oaicite:13]{index=13}
Deliverables:
- WalletProvider interface
- At least one provider implementation (mock or sandbox) plus redaction rules
Exit criteria:
- No sensitive values in logs or audit
- Complete checkout flow succeeds end-to-end in sandbox

### Phase 3: Commerce-specific policy validators
Deliverables:
- Constraint schema for commerce (Talos capability constraints profile)
- Deterministic validators for limits, allowlists, handler restrictions
Exit criteria:
- Negative tests demonstrating fail-closed behavior

### Phase 4 (optional): Order lifecycle webhooks + Identity linking
Deliverables:
- Public webhook endpoint with signature verification
- Order event persistence and audit
Exit criteria:
- Verified webhooks using rotated keys and replay defense

## 9. Testing strategy

- Unit tests:
  - Discovery parsing and validation
  - Signature creation and verification
  - Constraint evaluation
- Contract tests:
  - Validate all payloads against vendored JSON schemas
- Vector tests:
  - Detached JWT signing/verification vectors
  - Canonical JSON hashing stability tests
- Integration tests:
  - Docker compose sandbox merchant + connector
  - Idempotency replay tests

## 10. Operational requirements

- Observability:
  - Trace propagation using Request-Id
  - Metrics: calls, latency, failures by merchant and operation
- Rate limiting:
  - Per principal and per merchant
- Safe defaults:
  - Fail closed if policy evaluation or signing fails
  - Explicit allowlist required for merchants in prod

## 11. Open decisions (must be resolved before Phase 1 coding)

1. Hosting:
   - Where will the platform profile URL live so merchants can fetch it?
2. Key type:
   - Confirm algorithm requirements for Request-Signature in UCP 2026-01-11 and standardize across SDKs.
3. Scope:
   - Will we implement “search” as best-effort via feed, or keep UCP connector checkout-only for v1?
