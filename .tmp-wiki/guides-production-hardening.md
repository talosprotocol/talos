# Production Hardening

> **Phase 11 Feature** | Released 2026-01-29

## Overview

Phase 11 adds enterprise-grade production reliability features to the Talos Gateway:

- **Rate Limiting**: Token bucket with Redis backend
- **Distributed Tracing**: OpenTelemetry with sensitive data redaction
- **Health Checks**: Liveness and readiness probes
- **Graceful Shutdown**: Zero-downtime deployments

All features enforce **fail-closed** behavior in production mode to prevent security degradation.

---

## 1. Rate Limiting

### Rate Limiting Overview

Talos implements a **Token Bucket** rate limiter with:

- Redis backend for distributed rate limiting
- Per-principal and per-IP limiting
- Surface-specific rate limit overrides
- Atomic operations via Lua scripts

### Rate Limit Configuration

```bash
# Enable rate limiting
RATE_LIMIT_ENABLED=true

# Backend (memory or redis)
RATE_LIMIT_BACKEND=redis  # REQUIRED in production
REDIS_URL=redis://localhost:6379

# Default limits (can be overridden per-surface)
RATE_LIMIT_DEFAULT_RPS=5      # Requests per second
RATE_LIMIT_DEFAULT_BURST=10   # Burst capacity
```

### Rate Limit Fail-Closed

In **production mode** (`MODE=prod`):

- `RATE_LIMIT_BACKEND` **MUST** be `redis`
- `REDIS_URL` **MUST** be configured
- Gateway fails to start if these are missing

### Surface-Specific Limits

Override rates per-surface in [`gateway_surface.json`](file:///Users/nileshchakraborty/workspace/talos/services/ai-gateway/gateway_surface.json):

```json
{
  "surface_id": "llm.chat.completions",
  "rate_limit_rps": 10,
  "rate_limit_burst": 20
}
```

### Error Codes

| Code | HTTP | When | Mode |
| :--- | :--- | :--- | :--- |
| `RATE_LIMITED` | 429 | Quota exceeded | All |
| `RATE_LIMITER_UNAVAILABLE` | 503 | Redis down | Dev only |

### Rate Limit Testing

```bash
# Test rate limiting
for i in {1..20}; do 
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/v1/chat/completions
done

# Should see 429 responses after hitting limit
```

---

## 2. Distributed Tracing

### Distributed Tracing Overview

Talos integrates **OpenTelemetry** for distributed tracing with:

- Automatic span generation (FastAPI, SQLAlchemy)
- OTLP export to Jaeger, Zipkin, or other collectors
- **Automatic redaction** of sensitive data
- SQL statement logging disabled by default

### Tracing Configuration

```bash
# Enable tracing
TRACING_ENABLED=true

# OTLP endpoint (REQUIRED in production if tracing enabled)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Optional: Service name
OTEL_RESOURCE_ATTRIBUTES=service.name=talos-gateway
```

### Tracing Fail-Closed

In **production mode** (`MODE=prod`):

- If `TRACING_ENABLED=true`, `OTEL_EXPORTER_OTLP_ENDPOINT` **MUST** be set
- Gateway fails to start if missing

### Automatic Redaction

The [`TalosSpanProcessor`](file:///Users/nileshchakraborty/workspace/talos/services/ai-gateway/app/observability/tracing.py) automatically redacts:

- **Headers**: `Authorization`, `Cookie`, `Set-Cookie`
- **A2A Fields**: `header_b64u`, `ciphertext_b64u`, `ciphertext_hash`
- **Signatures**: Any attribute matching `*signature*`, `*token*`, `*secret*`, `*nonce*`
- **HTTP Headers**: All `http.request.header.*` and `http.response.header.*`

Redacted values are replaced with `[REDACTED]`.

### SQL Statement Logging

Per Phase 11 spec, SQL statement logging is **disabled**:

```python
SQLAlchemyInstrumentor().instrument(
    tracer_provider=provider,
    db_statement_enabled=False  # Disabled for security
)
```

### Setup Jaeger (Example)

```bash
# Run Jaeger all-in-one
docker run -d \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# Set endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Start Gateway
python -m uvicorn app.main:app

# View traces at http://localhost:16686
```

---

## 3. Health Checks

### Health Checks Overview

Talos provides two health check endpoints:

- **`/health/live`**: Liveness probe (always responds)
- **`/health/ready`**: Readiness probe (checks dependencies)

### `/health/live`

Returns **200 OK** immediately, no dependency checks.

```bash
$ curl http://localhost:8000/health/live
{"status": "healthy", "timestamp": "2026-01-29T19:00:00Z"}
```

**Available during shutdown**: This endpoint responds even when the shutdown gate is active.

### `/health/ready`

Checks **PostgreSQL** and **Redis** (if rate limiting enabled).

```bash
$ curl http://localhost:8000/health/ready
{
  "status": "healthy",
  "db": "connected",
  "redis": "connected"
}
```

Returns **503 Service Unavailable** if any dependency is down:

```bash
$ curl http://localhost:8000/health/ready
{
  "status": "unhealthy",
  "db": "error",
  "redis": "connected"
}
```

### Kubernetes Integration

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: gateway
    image: talos-gateway:latest
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 30
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 10
```

---

## 4. Graceful Shutdown

### Graceful Shutdown Overview

Talos implements graceful shutdown via [`ShutdownGateMiddleware`](file:///Users/nileshchakraborty/workspace/talos/services/ai-gateway/app/middleware/shutdown_gate.py):

- Rejects new requests with **503 SERVER_SHUTTING_DOWN**
- Allows `/health/live` to continue responding
- Drains in-flight requests (with timeout)
- Stops background workers cleanly
- Closes database and Redis connections

### Behavior

1. **SIGTERM received** (e.g., `kill -SIGTERM <pid>`)
2. **Shutdown gate activates**: New requests get 503
3. **Background tasks stop**: Workers check `shutdown_event`
4. **Request draining**: Wait up to 30s for in-flight requests
5. **Resource cleanup**: DB, Redis, tracing exporters flushed
6. **Exit**

### Error Code

Non-health requests during shutdown receive:

```json
{
  "error": "SERVER_SHUTTING_DOWN",
  "detail": "Server is shutting down"
}
```

HTTP status: **503 Service Unavailable**

### Shutdown Testing

```bash
# Start Gateway in background
python -m uvicorn app.main:app &
PID=$!

# Make a request (should succeed)
curl http://localhost:8000/v1/chat/completions

# Send SIGTERM
kill -SIGTERM $PID

# New requests should get 503
curl http://localhost:8000/v1/chat/completions
# {"error": "SERVER_SHUTTING_DOWN"}

# Health live still works
curl http://localhost:8000/health/live
# {"status": "healthy"}
```

---

## 5. Error Code Reference

Phase 11 introduces the following stable error codes:

| Code | HTTP | Description | Mode |
| :--- | :--- | :--- | :--- |
| `RATE_LIMITED` | 429 | Request rate exceeded | All |
| `RATE_LIMITER_UNAVAILABLE` | 503 | Rate limiter backend down | Dev only |
| `SERVER_SHUTTING_DOWN` | 503 | Graceful shutdown in progress | All |

All error responses include a `Retry-After` header when appropriate.

---

## 6. Deployment Checklist

### Production Mode Requirements

- [ ] `MODE=prod` environment variable set
- [ ] `RATE_LIMIT_BACKEND=redis` (if rate limiting enabled)
- [ ] `REDIS_URL` configured and accessible
- [ ] `OTEL_EXPORTER_OTLP_ENDPOINT` configured (if tracing enabled)
- [ ] Health check endpoints tested
- [ ] Graceful shutdown tested (SIGTERM handling)

### Recommended Configuration

```bash
# Production environment
MODE=prod

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_BACKEND=redis
REDIS_URL=redis://redis-cluster:6379
RATE_LIMIT_DEFAULT_RPS=10
RATE_LIMIT_DEFAULT_BURST=20

# Distributed Tracing
TRACING_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger-collector:4317
OTEL_RESOURCE_ATTRIBUTES=service.name=talos-gateway,environment=prod

# Database
DATABASE_WRITE_URL=postgresql://user:pass@db-primary:5432/talos
DATABASE_READ_URL=postgresql://user:pass@db-replica:5432/talos
```

### Monitoring

**Metrics to track**:

- Rate limiting: `talos_rate_limit_rejections_total`
- Tracing: Span export errors
- Health checks: `/health/ready` success rate
- Shutdown: Request drain duration

**Alerts to configure**:

- Redis connection failures
- OTLP export failures
- Health check failures
- Prolonged shutdown (>60s)

---

## 7. Troubleshooting

### Rate Limiting Issues

**Problem**: 503 `RATE_LIMITER_UNAVAILABLE` in development

**Solution**: Set `RATE_LIMIT_DEV_FAIL_OPEN=true` to fail open (dev only)

**Problem**: Gateway won't start - "RATE_LIMIT_BACKEND must be 'redis'"

**Solution**: In production, you must use Redis. Set `REDIS_URL`.

### Tracing Issues

**Problem**: Gateway won't start - "OTEL_EXPORTER_OTLP_ENDPOINT must be present"

**Solution**: Set the OTLP endpoint or disable tracing (`TRACING_ENABLED=false`)

**Problem**: Sensitive data visible in traces

**Solution**: Verify `TalosSpanProcessor` is being used. Check `app/main.py:setup_opentelemetry()`

### Health Check Issues

**Problem**: `/health/ready` always returns 503

**Solution**: Check PostgreSQL and Redis connectivity. Review logs for connection errors.

**Problem**: Kubernetes killing pods due to liveness failures

**Solution**: Increase `initialDelaySeconds` and `periodSeconds` in probe config

### Graceful Shutdown Issues

**Problem**: Requests fail immediately on SIGTERM

**Solution**: Verify `ShutdownGateMiddleware` is added to middleware stack

**Problem**: Shutdown takes >60s

**Solution**: Check for long-running background tasks. Reduce request drain timeout if needed.

---

## 8. See Also

- [A2A Channels](features-messaging-a2a-channels) - Agent-to-Agent communication (Phase 10)
- [Deployment Guide](deployment) - Full deployment instructions
- [Architecture](architecture-overview) - System architecture overview
- [API Reference](api-api-reference) - Complete API documentation
