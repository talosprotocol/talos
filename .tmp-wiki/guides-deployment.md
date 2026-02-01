# Production Deployment Guide

This guide covers deploying Talos Protocol services to production Kubernetes environments.

## Prerequisites

- Kubernetes 1.24+ cluster
- kubectl configured
- Helm 3.8+ (optional, for Helm-based deployment)
- Docker (for building images)
- Ingress controller (nginx recommended)

## Quick Start

### Option 1: Helm Chart (Recommended)

```bash
# Build images (or use GHCR)
export VERSION=$(git rev-parse --short HEAD)
docker build --build-arg GIT_SHA=$(git rev-parse HEAD) \
  --build-arg VERSION=$VERSION \
  --build-arg BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t ghcr.io/talosprotocol/talos-gateway:$VERSION \
  -f services/gateway/Dockerfile .

# Push to registry
docker push ghcr.io/talosprotocol/talos-gateway:$VERSION

# Install via Helm
helm install talos deploy/helm/talos \
  --namespace talos-system --create-namespace \
  --set image.tag=$VERSION
```

### Option 2: Kustomize

```bash
# Build images locally
make docker-build  # Or use the CI-built images

# Apply with Kustomize
cd deploy/k8s/overlays/prod
kustomize edit set image \
  talos-gateway=ghcr.io/talosprotocol/talos-gateway:$VERSION

kubectl apply -k .
```

## Configuration

### 1. Secrets

Create secrets before deployment:

```bash
kubectl create secret generic talos-secrets \
  --from-literal=database-url=postgresql://user:pass@host:5432/talos \
  --namespace talos-system
```

For production, use:

- **Sealed Secrets**: Encrypt secrets in Git
- **External Secrets Operator**: Sync from Vault/AWS Secrets Manager
- **SOPS**: Encrypt values with KMS

### 2. Ingress

Update hostname in values.yaml or kustomize patches:

```yaml
# Helm: values.yaml
ingress:
  host: talos.yourdomain.com
  tls:
    enabled: true
    secretName: talos-tls
```

### 3. Database

Production PostgreSQL is required (`DEV_MODE=false`).

**Option A: Managed Service** (Recommended)

```bash
# Use AWS RDS, GCP Cloud SQL, or Azure Database
DATABASE_URL=postgresql://user:pass@rds.amazonaws.com:5432/talos
```

**Option B: In-cluster StatefulSet**

```bash
kubectl apply -f deploy/k8s/base/postgres/statefulset.yaml
```

### 5. Phase 11: Production Hardening (Required)

Phase 11 introduces production-grade reliability features that **must** be configured for production deployments.

#### 5.1 Rate Limiting

**Redis Backend (Required in Production)**

```bash
# Create Redis secret
kubectl create secret generic talos-redis \
  --from-literal=redis-url=redis://redis-cluster:6379 \
  --namespace talos-system

# Or use managed service (AWS ElastiCache, GCP Memorystore)
kubectl create secret generic talos-redis \
  --from-literal=redis-url=redis://elasticache.amazonaws.com:6379 \
  --namespace talos-system
```

**Environment Variables:**

```yaml
# values.yaml or kustomize patch
env:
  - name: RATE_LIMIT_ENABLED
    value: "true"
  - name: RATE_LIMIT_BACKEND
    value: "redis"  # REQUIRED in production
  - name: REDIS_URL
    valueFrom:
      secretKeyRef:
        name: talos-redis
        key: redis-url
  - name: RATE_LIMIT_DEFAULT_RPS
    value: "10"
  - name: RATE_LIMIT_DEFAULT_BURST
    value: "20"
```

**Surface-Specific Limits:**

Update `gateway_surface.json` ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gateway-surface-config
data:
  gateway_surface.json: |
    {
      "surface_id": "llm.chat.completions",
      "rate_limit_rps": 10,
      "rate_limit_burst": 20
    }
```

#### 5.2 Distributed Tracing

**OTLP Collector (Required in Production if Tracing Enabled)**

**Option A: Jaeger**

```bash
# Install Jaeger Operator
kubectl create namespace observability
kubectl create -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml -n observability

# Deploy Jaeger instance
kubectl apply -f - <<EOF
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: talos-jaeger
  namespace: observability
spec:
  strategy: production
  collector:
    maxReplicas: 5
    resources:
      limits:
        cpu: 1000m
        memory: 1Gi
EOF
```

**Option B: Managed Service (Datadog, New Relic, etc.)**

```bash
kubectl create secret generic talos-otlp \
  --from-literal=endpoint=https://otlp.datadoghq.com:4317 \
  --namespace talos-system
```

**Environment Variables:**

```yaml
env:
  - name: TRACING_ENABLED
    value: "true"
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    valueFrom:
      secretKeyRef:
        name: talos-otlp
        key: endpoint  # REQUIRED in production if TRACING_ENABLED=true
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.name=talos-gateway,environment=prod"
```

**Automatic Redaction:**

The Gateway automatically redacts:
- `Authorization` headers
- A2A frame contents (`header_b64u`, `ciphertext_b64u`)
- All matching `*secret*`, `*token*`, `*signature*` attributes

#### 5.3 Health Checks

Configure Kubernetes probes:

```yaml
# Gateway Deployment
livenessProbe:
  httpGet:
    path: /health/live  # Phase 11: Always responds
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready  # Phase 11: Checks DB + Redis
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3
```

**Endpoints:**
- `/health/live`: Liveness (no dependency checks)
- `/health/ready`: Readiness (validates PostgreSQL, Redis connectivity)

#### 5.4 Graceful Shutdown

**Environment Variables:**

```yaml
env:
  - name: SHUTDOWN_DRAIN_TIMEOUT_SECONDS
    value: "30"  # Request drain timeout
```

**Deployment Configuration:**

```yaml
spec:
  terminationGracePeriodSeconds: 60  # Allow time for graceful shutdown
  template:
    spec:
      containers:
      - name: gateway
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 5"]  # Allow LB to remove endpoint
```

**Behavior:**
1. SIGTERM received
2. Shutdown gate activates (new requests get 503 `SERVER_SHUTTING_DOWN`)
3. `/health/live` continues responding
4. In-flight requests drain (up to `SHUTDOWN_DRAIN_TIMEOUT_SECONDS`)
5. Background workers stop
6. Connections closed

### 6. Monitoring (Optional)

Install Prometheus Operator:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values deploy/k8s/monitoring/prometheus-values.yaml
```

Enable ServiceMonitors:

```yaml
# Helm: values.yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
  prometheusRule:
    enabled: true
```

## Architecture

### Two-Ingress Pattern

```
                    ┌─────────────────┐
                    │  Ingress-Nginx  │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼─────┐    ┌─────▼──────┐
              │ Dashboard │    │  API Path  │
              │ Ingress   │    │  Ingress   │
              │   "/"     │    │ "/api/*"   │
              └─────┬─────┘    │ "/audit/*" │
                    │          │ "/mcp/*"   │
                    │          └─────┬──────┘
                    │                │
           ┌────────▼───┐    ┌───────┴──────┐
           │ Dashboard  │    │   Gateway    │
           │  Service   │    │   Audit      │
           │ (Port 3000)│    │   MCP        │
           └────────────┘    └──────────────┘
```

### Security Features

- **Non-root containers**: UID 1001
- **Read-only rootfs**: Writable mounts for /tmp
- **NetworkPolicies**: Default deny + explicit allowances
- **Pod security**: Capabilities dropped, seccomp enabled
- **TLS**: Ingress with cert-manager

## Health Check Endpoints

All services expose standardized health endpoints:

- `/healthz` - Liveness probe (no dependencies)
- `/readyz` - Readiness probe (checks dependencies)
- `/version` - Build metadata (git SHA, version, build time)
- `/metrics` - Prometheus metrics

## Migration Strategy

Migrations run as a **versioned Kubernetes Job**:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: gateway-migrations-v1 # Increment version
```

**Workflow:**

1. Job runs `alembic upgrade head`
2. Gateway `/readyz` checks schema version
3. Returns 503 until migrations complete
4. No initContainer race conditions

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: talos-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: talos-gateway
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Vertical Pod Autoscaling

Adjust resource requests/limits in `values.yaml`:

```yaml
gateway:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi
```

## Backup & Disaster Recovery

### Database Backups

```bash
# Automated backups via CronJob
kubectl apply -f deploy/k8s/base/postgres/backup-cronjob.yaml
```

### Audit Log Archival

Audit events stored in PostgreSQL with Merkle tree anchoring.

**Retention Policy:**

- Hot storage: 90 days
- Cold storage (S3): 7 years
- Compliance: SOC2, HIPAA, GDPR

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n talos-system

# View logs
kubectl logs -n talos-system -l app=talos-gateway --tail=50

# Check events
kubectl describe pod -n talos-system <pod-name>
```

### Ingress not routing

```bash
# Verify ingress created
kubectl get ingress -n talos-system

# Check ingress-nginx logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Test with port-forward
kubectl port-forward -n talos-system svc/talos-gateway 8000:8000
curl http://localhost:8000/healthz
```

### Database connection issues

```bash
# Check secret exists
kubectl get secret talos-secrets -n talos-system

# Verify DATABASE_URL
kubectl get secret talos-secrets -n talos-system -o jsonpath='{.data.database-url}' | base64 -d

# Test connectivity from pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql $DATABASE_URL
```

## Production Checklist

### Core Infrastructure
- [ ] Secrets externally managed (not in Git)
- [ ] TLS certificates configured
- [ ] Database backups enabled
- [ ] Monitoring alerts configured
- [ ] Resource limits set appropriately
- [ ] NetworkPolicies applied
- [ ] Pod security policies enforced
- [ ] Ingress rate limiting configured
- [ ] Log aggregation setup (ELK, Datadog, etc.)
- [ ] Disaster recovery plan documented

### Phase 11: Production Hardening
- [ ] `MODE=prod` environment variable set
- [ ] **Rate Limiting**: Redis backend configured (`RATE_LIMIT_BACKEND=redis`)
- [ ] **Rate Limiting**: `REDIS_URL` secret created
- [ ] **Tracing**: OTLP endpoint configured (if `TRACING_ENABLED=true`)
- [ ] **Tracing**: Verified sensitive data redaction
- [ ] **Health Checks**: Liveness probe uses `/health/live`
- [ ] **Health Checks**: Readiness probe uses `/health/ready`
- [ ] **Graceful Shutdown**: `terminationGracePeriodSeconds` ≥60s
- [ ] **Graceful Shutdown**: Tested SIGTERM handling
- [ ] **Monitoring**: Rate limit rejection metrics tracked
- [ ] **Monitoring**: Trace export errors alerted

## References

- [Kubernetes Manifests](../deploy/k8s/)
- [Helm Chart](../deploy/helm/talos/)
- [Monitoring Setup](../deploy/k8s/monitoring/)
- [CI/CD Pipeline](../.github/workflows/production-ready.yml)
