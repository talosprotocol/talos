# Multi-Region Architecture

This page documents the multi-region database routing implementation for the Talos AI Gateway (Phase 12).

## Overview

The multi-region architecture enables read/write database splitting for improved scalability and disaster recovery. The Gateway can be deployed across multiple regions with:

- **Primary Database**: Handles all write operations and security-critical reads
- **Replica Database(s)**: Handle non-critical read operations with eventual consistency

## Consistency Model

### Primary-Required Endpoints

These endpoints always use the primary database to ensure strong consistency:

| Category           | Endpoints                           | Reason                    |
| ------------------ | ----------------------------------- | ------------------------- |
| **Secrets**        | `GET/POST/DELETE /admin/v1/secrets` | Read-your-writes required |
| **Authentication** | `GET /admin/v1/me`                  | Security-critical         |
| **Configuration**  | `GET /admin/v1/llm/*`               | Fresh config for routing  |
| **Catalog**        | `GET /admin/v1/catalog/*`           | Writes audit events       |
| **All Writes**     | `POST/PATCH/DELETE *`               | By definition             |

### Replica-Safe Endpoints

These endpoints can tolerate eventual consistency (seconds of staleness):

| Endpoint                        | Reason                       |
| ------------------------------- | ---------------------------- |
| `GET /admin/v1/mcp/servers`     | Pure select, no side effects |
| `GET /admin/v1/mcp/policies`    | Pure select, no side effects |
| `GET /admin/v1/telemetry/stats` | Aggregated metrics           |
| `GET /admin/v1/audit/stats`     | Aggregated metrics           |
| `GET /health/ready`             | Health probe                 |

## Circuit Breaker

The read replica connection uses a circuit breaker pattern to prevent cascading failures:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Circuit Breaker                           │
├─────────────────────────────────────────────────────────────┤
│  State: CLOSED                                               │
│  ├─ Failures: 0/3                                           │
│  ├─ On failure → increment counter                          │
│  └─ On threshold → OPEN                                     │
├─────────────────────────────────────────────────────────────┤
│  State: OPEN                                                │
│  ├─ Duration: 30 seconds                                    │
│  ├─ All requests → Primary (fallback)                       │
│  └─ After timeout → CLOSED (retry replica)                  │
└─────────────────────────────────────────────────────────────┘
```

### Configuration

```bash
READ_FAILURE_THRESHOLD=3       # Failures before circuit opens
CIRCUIT_OPEN_DURATION_SECONDS=30  # How long circuit stays open
DATABASE_READ_TIMEOUT_MS=1000  # Fast fail for replica reads
DATABASE_CONNECT_TIMEOUT_MS=3000  # Connection timeout
```

## Read-Only Enforcement

Misclassified endpoints (reads that accidentally write) are detected and blocked:

1. **SQL Layer**: `SET TRANSACTION READ ONLY` on replica sessions
2. **Database Layer**: `default_transaction_read_only=on` on replica

If a write is attempted on a read-only path:

- Returns HTTP 500 with error code `MISCLASSIFIED_ENDPOINT`
- Does **NOT** fallback to primary (this is a code bug, not availability issue)

## Response Headers

All read endpoints include observability headers:

| Header                  | Values                                                       | Description                        |
| ----------------------- | ------------------------------------------------------------ | ---------------------------------- |
| `X-Talos-DB-Role`       | `primary`, `replica`                                         | Which database handled the request |
| `X-Talos-Read-Fallback` | `0`, `1`                                                     | Whether fallback occurred          |
| `X-Talos-Read-Reason`   | `circuit_open`, `connect_error`, `timeout`, `pool_exhausted` | Why fallback happened              |

## Deployment

### Docker Compose (Development)

```bash
cd services/ai-gateway
docker-compose -f docker-compose.multi-region.yml up -d
```

This creates:

- `postgres-primary`: Primary database (port 5452)
- `postgres-replica`: Streaming replica (port 5453)
- `gateway-region-a`: Primary for both read/write
- `gateway-region-b`: Primary for write, replica for read

### Environment Variables

```bash
# Primary database (required)
DATABASE_WRITE_URL=postgresql://talos:talos@primary:5432/talos

# Replica database (optional)
DATABASE_READ_URL=postgresql://talos:talos@replica:5432/talos

# Fallback behavior
READ_FALLBACK_ENABLED=true  # Default: true
```

## Verification

Run the verification script to ensure replication is working:

```bash
python verify_multi_region.py --lag-threshold 5.0 --iterations 10
```

This tests:

1. **Happy Path**: Write to primary, read from replica within threshold
2. **Lag Measurement**: Reports p50/p95 replication delay
3. **Fallback Detection**: Verifies headers when replica is down

### CI Gate

The verification script can be used as a CI gate:

```yaml
- name: Multi-Region Integration Test
  run: |
    docker-compose -f docker-compose.multi-region.yml up -d
    sleep 30
    python verify_multi_region.py --lag-threshold 5.0
```

Fails if p95 replication lag exceeds the threshold.

## Architecture Diagram

```
┌─────────────────┐         ┌─────────────────┐
│   Gateway A     │         │   Gateway B     │
│   (Region A)    │         │   (Region B)    │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │ Writes                    │ Writes + Reads
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│                 │◄────────│                 │
│  Primary DB     │ Repl.   │  Replica DB     │
│  (us-east-1)    │────────►│  (us-west-2)    │
│                 │         │ (Read-Only)     │
└─────────────────┘         └─────────────────┘
```

## Related

- [Architecture](architecture-overview)
- [Observability](features-observability-observability)
- [Hardening Guide](guides-hardening-guide)
