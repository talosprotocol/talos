# MVP plan: complete the backend

MVP definition (backend): the gateway and supporting services are complete enough that `talos-governance-agent` can safely operate with read and write actions under strict supervision.

## MVP acceptance criteria (non-negotiable)

1. Auth, identity, and audit are mandatory on every request

   - Identity validation per Phase 6
   - Audit emission per Phase 5
   - Stable error responses for both

2. RBAC is the only authorization mechanism for nontrivial surfaces

   - Role, binding, and permission model
   - Deterministic resolution
   - Surface registry declares required permission(s)

3. Secrets are envelope-encrypted at rest

   - No plaintext secrets in storage
   - No secret material in logs
   - Rotation is supported via `kek_id`

4. Contracts are the source of truth
   - All schemas and vectors are in `talos-contracts`
   - Gateway and SDKs validate using bundled artifacts

## Stage breakdown (PR series)

### Stage 0: Baseline gates and drift checks

Repos: talos-contracts, talos-gateway, SDKs

Deliverables:

- CI gate that runs contract schema validation and vector runner.
- CI gate in each consumer repo that fails if contract logic is duplicated.
  - Target patterns: cursor encoding, base64url, uuidv7 regex, stable error code maps.

Exit criteria:

- A no-op change in consumer repos does not break gates.
- Any duplicated contract helper triggers CI failure.

### Stage 1: RBAC contracts (Phase 7.0)

Repo: talos-contracts

Deliverables:

- `schemas/rbac/role.schema.json`
- `schemas/rbac/binding.schema.json`
- `test_vectors/rbac/rbac_vectors.json`
  - valid: platform, org, team
  - invalid: null vs absent, uppercase UUID, extra properties, wrong scope nesting
  - matching: scope matching matrix

Exit criteria:

- Vector runner validates the matrix.
- SDKs can load and validate these schemas from published artifacts.

### Stage 2: RBAC engine + gateway enforcement (Phase 7.1)

Repo: talos-gateway

Deliverables:

- PolicyEngine module (domain) with deterministic resolution.
- Middleware that:
  - maps incoming surface -> required permission(s)
  - loads principal bindings + roles
  - returns allow or deny deterministically

Hard requirements:

- Audit must record authz decision input and output (without leaking secrets).
- `request.state.authz_decision` must be set to drive Phase 5 outcome mapping.

Exit criteria:

- End-to-end tests cover allow and deny for each scope type.
- Telemetry counters exist: allow_total, deny_total by surface and permission.

### Stage 3: Secrets contracts + SDK wrappers (Phase 8.0)

Repos: talos-contracts, talos-sdk-py, talos-sdk-ts

Deliverables:

- `schemas/secrets/envelope.schema.json`
- vectors: valid/invalid envelopes
- SDK interface: KEK Provider
  - encrypt(plaintext) -> envelope
  - decrypt(envelope) -> plaintext

Hard requirements:

- `iv` length 12 bytes, `tag` length 16 bytes, both hex-encoded.
- `alg` is `aes-256-gcm` only.

Exit criteria:

- SDK tests reject malformed envelopes and any extra properties.

### Stage 4: SecretsManager service integration (Phase 8.1)

Repo: talos-gateway

Deliverables:

- `SecretsManager` domain service with storage adapter.
- Rotation workflow: re-wrap all stored envelopes with new `kek_id`.
- Redaction rules: never log plaintext or raw ciphertext.

Exit criteria:

- Integration tests prove plaintext never touches persistence.
- Rotation tests verify old envelopes can be re-wrapped and still decrypted.

### Stage 5: Surface registry and permissions mapping

Repo: talos-gateway, talos-contracts

Deliverables:

- Registry entry per surface that declares required permission(s).
- A generated artifact that the governance agent can consume to reason about capabilities.

Exit criteria:

- Every public route is in the registry.
- 404 path template is always `/__unmatched__` in audit.

## MVP status reporting

Each week, update this table in a PR.

| Stage | Status      | Owner       | Links                                   |
| ----- | ----------- | ----------- | --------------------------------------- |
| 0     | ✅ complete | Antigravity | CI gates in all repos                   |
| 1     | ✅ complete | Antigravity | Phase 7.0 RBAC contracts                |
| 2     | ✅ complete | Antigravity | Phase 7.1-7.2 PolicyEngine + middleware |
| 3     | ✅ complete | Antigravity | Phase 8: secrets envelope + SDK KEK     |
| 4     | ✅ complete | Antigravity | Phase 8: PostgresSecretStore            |
| 5     | ✅ complete | Antigravity | Phase 7.2: surface_registry.json        |
