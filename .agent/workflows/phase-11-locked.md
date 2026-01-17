# Phase 11: Production Hardening - LOCKED SPEC

## Global Invariants (Non-Negotiable)

1. **Fail-Closed in Production**:

   - If `MODE=prod` and rate limiting enabled: Redis MUST be configured/reachable.
   - If `MODE=prod` and tracing enabled: OTLP exporter MUST be configured/initialized.
   - Gateway MUST raise CRITICAL check failure at startup if these are unmet.

2. **No Sensitive Data in Telemetry**:

   - Redact: `Authorization`, `X-*Signature*`, tokens.
   - Redact: A2A frame fields (`header_b64u`, `ciphertext_b64u`), secrets envelopes.
   - SQL statements DISABLED by default.

3. **Stable Error Codes**:

   - `RATE_LIMITED` (429)
   - `SERVER_SHUTTING_DOWN` (503)
   - `RATE_LIMITER_UNAVAILABLE` (503, dev only)

4. **Order of Enforcement**:
   - Rate Limit -> Auth Parsing -> Handler.

## Implementation Details

### 11.1 Rate Limiting (Gateway)

- **Token Bucket** logic.
- **Keying**:
  - Auth: `principal_id` (sub claim).
  - Anon: `client_ip_hash` or "anonymous".
- **Storage**: Redis (Lua atomic update).
- **Config**: Global defaults + Surface Registry overrides.

### 11.2 Distributed Tracing

- **Propagation**: `traceparent`.
- **Redaction**: Custom SpanProcessor or Hooks to scrub sensitive attributes.
- **SDK**: Trace header injection in `Wallet.sign_http_request` (or before/after if signed). Spec says "If request signing covers headers, then traceparent MUST be included before signing".

### 11.3 Health Checks

- `/health/live` (200 OK).
- `/health/ready` (Check DB/Redis). Returns 503 if dependencies down.

### 11.4 Graceful Shutdown

- **Shutdown Gate Middleware**:
  - Reject new requests with 503 `SERVER_SHUTTING_DOWN`.
  - Drain existing requests (timeout).
  - Close resources (DB, Redis).

## Configuration

Env Vars: `MODE`, `RATE_LIMIT_ENABLED`, `RATE_LIMIT_BACKEND`, `REDIS_URL`, `TRACING_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`.
