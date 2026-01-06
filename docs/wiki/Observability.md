---
status: Implemented
audience: Operator, Developer
---

# Observability

> **Problem**: Production systems need visibility into Talos behavior.  
> **Guarantee**: Structured logs, metrics, and tracing.  
> **Non-goal**: Application-level monitoring—focus on Talos internals.

---

## Overview

| Observability Type | What It Provides |
|-------------------|------------------|
| **Metrics** | Quantitative measurements (latency, throughput, errors) |
| **Logs** | Structured event records |
| **Traces** | Request flow across components |

---

## Metrics

### Prometheus Endpoint

```python
# Enable metrics endpoint
client = await TalosClient.create(
    "agent",
    metrics_port=9090  # Prometheus scrape endpoint
)
```

Access at: `http://localhost:9090/metrics`

### Core Metrics

#### Session Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `talos_sessions_active` | Gauge | Current active sessions |
| `talos_sessions_established_total` | Counter | Total sessions established |
| `talos_session_establishment_seconds` | Histogram | Session setup latency |
| `talos_session_failures_total` | Counter | Failed session attempts |

#### Message Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `talos_messages_sent_total` | Counter | Messages sent |
| `talos_messages_received_total` | Counter | Messages received |
| `talos_message_send_seconds` | Histogram | Send latency |
| `talos_message_size_bytes` | Histogram | Message sizes |
| `talos_messages_queued` | Gauge | Messages waiting to send |

#### Capability Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `talos_capabilities_granted_total` | Counter | Capabilities issued |
| `talos_capabilities_revoked_total` | Counter | Capabilities revoked |
| `talos_capabilities_active` | Gauge | Currently valid capabilities |
| `talos_capability_verification_seconds` | Histogram | Verification latency |

#### Audit Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `talos_audit_entries_total` | Counter | Audit log entries |
| `talos_audit_anchor_total` | Counter | Blockchain anchors |
| `talos_audit_anchor_failures_total` | Counter | Failed anchors |
| `talos_audit_size_bytes` | Gauge | Audit log size |

#### Cryptography Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `talos_crypto_operations_total` | Counter | Crypto operations by type |
| `talos_crypto_operation_seconds` | Histogram | Operation latency |
| `talos_key_rotation_timestamp` | Gauge | Last key rotation time |

### Example Prometheus Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'talos-agents'
    static_configs:
      - targets: 
        - 'agent-1:9090'
        - 'agent-2:9090'
    scrape_interval: 15s
```

### Grafana Dashboard

Key panels to create:

```
┌─────────────────────────────────────────────────────────┐
│  Messages/sec    Sessions Active    Capabilities Active │
│  ████████████    ████████████       ████████████        │
├─────────────────────────────────────────────────────────┤
│  Session Latency (p50, p95, p99)                        │
│  ═══════════════════════════════════════════════        │
├─────────────────────────────────────────────────────────┤
│  Error Rate        Audit Anchors     Queue Depth        │
│  ████████████      ████████████      ████████████       │
└─────────────────────────────────────────────────────────┘
```

---

## Structured Logging

### Configuration

```python
import logging

# Configure structured JSON logging
client = await TalosClient.create(
    "agent",
    log_config={
        "level": "INFO",
        "format": "json",
        "output": "stdout"
    }
)
```

### Log Format

```json
{
  "timestamp": "2024-01-15T10:23:45.123Z",
  "level": "INFO",
  "component": "session",
  "event": "session_established",
  "trace_id": "abc123",
  "peer_id": "did:talos:bob",
  "session_id": "sess_7f3k2m",
  "duration_ms": 45
}
```

### Log Levels

| Level | Use Case |
|-------|----------|
| `DEBUG` | Development, troubleshooting |
| `INFO` | Normal operations |
| `WARNING` | Unusual but handled situations |
| `ERROR` | Failures requiring attention |
| `CRITICAL` | System-level failures |

### Key Log Events

```python
# Session events
{"event": "session_established", "peer_id": "...", "duration_ms": 45}
{"event": "session_terminated", "peer_id": "...", "reason": "user_request"}
{"event": "session_failed", "peer_id": "...", "error": "timeout"}

# Message events
{"event": "message_sent", "peer_id": "...", "size_bytes": 256}
{"event": "message_received", "peer_id": "...", "size_bytes": 128}

# Capability events
{"event": "capability_granted", "subject": "...", "scope": "..."}
{"event": "capability_revoked", "capability_id": "...", "reason": "..."}

# Security events
{"event": "signature_invalid", "peer_id": "...", "message_hash": "..."}
{"event": "capability_expired", "capability_id": "..."}
{"event": "key_rotated", "old_key_hash": "...", "new_key_hash": "..."}
```

---

## Distributed Tracing

### Trace IDs

Every message carries a trace ID for end-to-end tracking:

```python
# Send with explicit trace ID
await client.send(
    peer_id,
    message,
    trace_id="unique-trace-123"
)

# Or auto-generated
result = await client.send(peer_id, message)
print(f"Trace ID: {result.trace_id}")
```

### Span Structure

```
Trace: message-send-abc123
├── Span: encrypt (2ms)
├── Span: sign (1ms)
├── Span: audit_commit (5ms)
├── Span: network_send (15ms)
│   └── Span: retry_1 (timeout)
│   └── Span: retry_2 (success)
└── Span: ack_received (3ms)
```

### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Configure exporter
client = await TalosClient.create(
    "agent",
    tracing={
        "enabled": True,
        "exporter": "jaeger",
        "endpoint": "http://jaeger:14268/api/traces"
    }
)
```

---

## SIEM Integration

### Audit Streaming

```python
# Stream audit events to SIEM
client = await TalosClient.create(
    "agent",
    audit_streaming={
        "enabled": True,
        "destination": "syslog://siem.example.com:514",
        "format": "cef"  # Common Event Format
    }
)
```

### CEF Format Example

```
CEF:0|Talos|Protocol|2.0.6|SESSION_ESTABLISHED|Session Established|3|
  src=did:talos:alice dst=did:talos:bob
  cs1=sess_7f3k2m cs1Label=SessionID
  cn1=45 cn1Label=DurationMs
```

---

## Health Checks

### Endpoints

```python
# Enable health endpoints
client = await TalosClient.create(
    "agent",
    health_port=8080
)
```

| Endpoint | Purpose |
|----------|---------|
| `/health` | Overall health status |
| `/health/live` | Liveness (process running) |
| `/health/ready` | Readiness (can accept traffic) |

### Response Format

```json
{
  "status": "healthy",
  "checks": {
    "storage": "ok",
    "network": "ok",
    "audit": "ok",
    "keys": "ok"
  },
  "version": "2.0.6",
  "uptime_seconds": 3600
}
```

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Alerting Rules

### Critical Alerts

```yaml
groups:
- name: talos-critical
  rules:
  - alert: TalosDown
    expr: up{job="talos"} == 0
    for: 1m
    labels:
      severity: critical
      
  - alert: AuditAnchorFailing
    expr: increase(talos_audit_anchor_failures_total[1h]) > 5
    labels:
      severity: critical
      
  - alert: SignatureVerificationFailures
    expr: increase(talos_signature_failures_total[5m]) > 0
    labels:
      severity: critical
```

### Warning Alerts

```yaml
- alert: HighMessageLatency
  expr: histogram_quantile(0.95, talos_message_send_seconds) > 1
  for: 5m
  labels:
    severity: warning
    
- alert: QueueBacklog
  expr: talos_messages_queued > 100
  for: 5m
  labels:
    severity: warning
    
- alert: KeyRotationOverdue
  expr: (time() - talos_key_rotation_timestamp) > 2592000  # 30 days
  labels:
    severity: warning
```

---

## CLI Diagnostics

```bash
# Overall status
talos status

# Detailed diagnostics
talos diagnose --verbose

# Network connectivity
talos diagnose --network

# Storage health
talos diagnose --storage

# Export diagnostic bundle
talos diagnose --export /tmp/talos-diag.tar.gz
```

---

**See also**: [Hardening Guide](Hardening-Guide) | [Failure Modes](Failure-Modes) | [Infrastructure](Infrastructure)
