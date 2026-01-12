---
status: Implemented
audience: Operator
---

# Hardening Guide

> **Problem**: Production deployments need security hardening.  
> **Guarantee**: Checklist of security configurations.  
> **Non-goal**: Threat elimination—see [Threat Model](Threat-Model).

---

## Pre-Deployment Checklist

| Category       | Item                                    | Priority       |
| -------------- | --------------------------------------- | -------------- |
| **Keys**       | Use encrypted key storage               | 🔴 Critical    |
| **Keys**       | Set key file permissions to 600         | 🔴 Critical    |
| **Keys**       | Consider HSM/TPM for production         | 🟡 Recommended |
| **Network**    | Enable TLS for registry connections     | 🔴 Critical    |
| **Network**    | Configure firewall rules                | 🔴 Critical    |
| **Network**    | Use private network for bootstrap nodes | 🟡 Recommended |
| **Storage**    | Encrypt audit log at rest               | 🔴 Critical    |
| **Storage**    | Set appropriate file permissions        | 🔴 Critical    |
| **Config**     | Disable debug mode                      | 🔴 Critical    |
| **Config**     | Set appropriate log levels              | 🟡 Recommended |
| **Monitoring** | Enable audit streaming                  | 🟡 Recommended |
| **Monitoring** | Set up alerting                         | 🟡 Recommended |

---

## Key Management

### Encrypted Storage

```python
# Always use password-protected key storage
client = await TalosClient.create(
    "production-agent",
    data_dir="/secure/path/agent_data",
    password=os.environ["TALOS_KEY_PASSWORD"]  # From secrets manager
)
```

### File Permissions

```bash
# Set restrictive permissions on key files
chmod 600 /secure/path/agent_data/identity.key
chmod 700 /secure/path/agent_data/

# Verify
ls -la /secure/path/agent_data/
# Should show: -rw------- ... identity.key
```

### HSM Integration (Advanced)

For high-security deployments:

```python
# HSM-backed key storage (future)
client = await TalosClient.create(
    "secure-agent",
    key_backend="hsm",
    hsm_config={
        "module": "/usr/lib/softhsm/libsofthsm2.so",
        "slot": 0,
        "pin": os.environ["HSM_PIN"]
    }
)
```

---

## Network Security

### TLS Configuration

```python
# Enable TLS for registry connections
client = await TalosClient.create(
    "agent",
    registry_url="wss://registry.example.com:443",
    tls_verify=True,
    tls_ca_cert="/path/to/ca.crt"
)
```

### Firewall Rules

```bash
# Allow only necessary ports
# Talos P2P (default)
ufw allow 8765/tcp

# Registry (if running)
ufw allow 8766/tcp

# Deny everything else
ufw default deny incoming
ufw enable
```

### Network Policies (Kubernetes)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: talos-agent
spec:
  podSelector:
    matchLabels:
      app: talos-agent
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: talos-agent
      ports:
        - port: 8765
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: talos-registry
      ports:
        - port: 8766
```

---

## Storage Security

### Encrypted Audit Log

```python
# Enable at-rest encryption for audit
client = await TalosClient.create(
    "agent",
    audit_config={
        "encrypt_at_rest": True,
        "encryption_key": os.environ["AUDIT_ENCRYPTION_KEY"]
    }
)
```

### Storage Permissions

```bash
# Audit log directory
chmod 700 /var/lib/talos/audit/
chown talos:talos /var/lib/talos/audit/

# LMDB files
chmod 600 /var/lib/talos/audit/*.mdb
```

---

## Configuration Hardening

### Production Configuration

```yaml
# config/production.yaml
talos:
  mode: production
  debug: false

  logging:
    level: INFO # Not DEBUG
    format: json

  security:
    require_tls: true
    min_capability_expiry: 60 # Minimum 1 minute
    max_capability_expiry: 86400 # Maximum 24 hours

  audit:
    enabled: true
    anchor_interval: 300 # 5 minutes
    encrypt_at_rest: true
    canonical_format: rfc8785 # JCS (Normative)
    integrity_verification: sha256_jcs
    surface_completeness_gate: enabled # Fails if routes not in inventory
```

### Environment Variables

```bash
# Required secrets (never in config files)
export TALOS_KEY_PASSWORD="..."
export TALOS_AUDIT_KEY="..."
export TALOS_REGISTRY_TOKEN="..."

# Audit Hardening (Normative v5.1)
export AUDIT_IP_HMAC_KEY="..."      # HMAC-SHA256 salt for IP hashing
export AUDIT_IP_HMAC_KEY_ID="..."   # Key identifier for IP salt
export TRUSTED_PROXIES="10.0.0.1/24" # Mandatory CIDRs for IP trusted-hop

# Never log these
export TALOS_LOG_REDACT_SECRETS=true
```

---

## Secrets Management

### Recommended Patterns

| Pattern               | Use Case               |
| --------------------- | ---------------------- |
| Environment variables | Container deployments  |
| Kubernetes Secrets    | K8s deployments        |
| HashiCorp Vault       | Enterprise deployments |
| AWS Secrets Manager   | AWS deployments        |

### Example: Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: talos-secrets
type: Opaque
stringData:
  key-password: "${KEY_PASSWORD}"
  audit-key: "${AUDIT_KEY}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: talos-agent
spec:
  template:
    spec:
      containers:
        - name: agent
          envFrom:
            - secretRef:
                name: talos-secrets
```

---

## Monitoring & Alerting

### Metrics to Monitor

| Metric                         | Alert Threshold |
| ------------------------------ | --------------- |
| `talos_session_failures`       | > 10/minute     |
| `talos_capability_revocations` | > 5/hour        |
| `talos_audit_anchor_failures`  | Any             |
| `talos_key_rotation_age_days`  | > 30            |
| `talos_peer_disconnections`    | > 50% of peers  |

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "talos"
    static_configs:
      - targets: ["localhost:9090"]
    metrics_path: /metrics
```

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: talos
    rules:
      - alert: TalosAuditAnchorFailure
        expr: increase(talos_audit_anchor_failures[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Audit anchoring failed"

      - alert: TalosKeyRotationOverdue
        expr: talos_key_rotation_age_days > 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Key rotation overdue"
```

---

## Container Hardening

### Dockerfile Best Practices

```dockerfile
# Use minimal base image
FROM python:3.11-slim

# Run as non-root
RUN useradd -r -s /bin/false talos
USER talos

# Read-only filesystem where possible
# Mount data directories as volumes

# No shell access
RUN rm /bin/sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD talos status || exit 1
```

### Pod Security

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
    - name: talos
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
```

---

## Operational Security

### Key Rotation Schedule

| Key Type              | Rotation Frequency        |
| --------------------- | ------------------------- |
| Prekeys               | Weekly                    |
| Session keys          | Per-message (automatic)   |
| Identity keys         | Annually or on compromise |
| Audit encryption keys | Quarterly                 |

### Incident Response

1. **Suspected key compromise**:

   ```bash
   talos emergency-rotate --revoke-old
   ```

2. **Revoke compromised agent**:

   ```bash
   talos revoke --did did:talos:compromised --reason "security incident"
   ```

3. **Audit investigation**:
   ```bash
   talos audit export --from "2024-01-01" --include-proofs > investigation.json
   ```

---

## Compliance Considerations

### Data Handling

| Requirement                | Talos Feature               |
| -------------------------- | --------------------------- |
| Data at rest encryption    | Audit encryption            |
| Data in transit encryption | E2EE (mandatory)            |
| Key management             | Encrypted storage, rotation |
| Audit trail                | Blockchain-anchored proofs  |
| Access control             | Capability tokens           |

### Retention Policies

```python
# Configure audit retention
client = await TalosClient.create(
    "agent",
    audit_config={
        "retention_days": 365,  # Comply with regulations
        "archive_to": "s3://audit-archive/"
    }
)
```

---

**See also**: [Threat Model](Threat-Model) | [Agent Lifecycle](Agent-Lifecycle) | [Infrastructure](Infrastructure)
