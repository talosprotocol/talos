# Talos Helm Chart

Production-ready Helm chart for deploying Talos Protocol to Kubernetes.

## Installation

### From OCI Registry (GitHub Container Registry)

```bash
helm install talos oci://ghcr.io/talosprotocol/charts/talos \
  --namespace talos-system --create-namespace \
  --set image.tag=<version>
```

### From Source

```bash
helm install talos deploy/helm/talos \
  --namespace talos-system --create-namespace \
  --set image.tag=latest
```

### Development (Local)

```bash
helm install talos deploy/helm/talos \
  --namespace talos-system --create-namespace \
  --values deploy/helm/talos/values-dev.yaml
```

## Configuration

### Key Values

| Parameter               | Description                      | Default       |
| ----------------------- | -------------------------------- | ------------- |
| `global.environment`    | Environment name                 | `production`  |
| `image.registry`        | Image registry                   | `ghcr.io`     |
| `image.tag`             | Image tag (overrides appVersion) | `""`          |
| `gateway.replicaCount`  | Gateway replicas                 | `3`           |
| `gateway.env.devMode`   | Enable dev mode                  | `false`       |
| `monitoring.enabled`    | Enable Prometheus monitoring     | `true`        |
| `networkPolicy.enabled` | Enable NetworkPolicies           | `true`        |
| `ingress.host`          | Ingress hostname                 | `talos.local` |

### Secrets

Create secrets externally before installation:

```bash
kubectl create secret generic <release>-talos-secrets \
  --from-literal=database-url=postgresql://... \
  --namespace talos-system
```

Or use `sealed-secrets` or `external-secrets` operator in production.

## Upgrading

```bash
helm upgrade talos oci://ghcr.io/talosprotocol/charts/talos \
  --namespace talos-system \
  --set image.tag=<new-version>
```

## Uninstalling

```bash
helm uninstall talos --namespace talos-system
```

## Requirements

- Kubernetes 1.24+
- Helm 3.8+
- Ingress controller (nginx recommended)
- Prometheus Operator (optional, for monitoring)

## See Also

- [Values Reference](values.yaml)
- [Development Values](values-dev.yaml)
