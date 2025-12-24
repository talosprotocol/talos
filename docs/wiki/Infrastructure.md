# Infrastructure

> **Docker and Kubernetes deployment for Talos Protocol**

## Docker

### Quick Start

```bash
# Build image
docker build -t talos-protocol:latest .

# Run single node
docker run -d -p 8765:8765 -p 8468:8468 talos-protocol:latest

# Run tests
docker build --target development -t talos-test .
docker run talos-test
```

### Docker Compose

```bash
# Start node
docker-compose up -d talos-node

# Start with bootstrap node
docker-compose --profile bootstrap up -d

# Start with Ollama AI
docker-compose --profile ai up -d

# Run tests
docker-compose --profile dev run talos-test

# View logs
docker-compose logs -f talos-node

# Stop
docker-compose down
```

### Services

| Service | Ports | Description |
|---------|-------|-------------|
| `talos-node` | 8765, 8468 | Main P2P node |
| `talos-bootstrap` | 8766, 8469 | Bootstrap node |
| `ollama` | 11434 | AI backend |
| `talos-test` | - | Test runner |

---

## Kubernetes (Helm)

### Quick Start

```bash
# Install chart
helm install talos ./deploy/helm/talos

# Install with custom values
helm install talos ./deploy/helm/talos \
  --set replicaCount=5 \
  --set talos.difficulty=3

# Upgrade
helm upgrade talos ./deploy/helm/talos

# Uninstall
helm uninstall talos
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `replicaCount` | 3 | Number of replicas |
| `image.repository` | talos-protocol | Image name |
| `image.tag` | 2.0.0 | Image tag |
| `service.type` | ClusterIP | Service type |
| `service.p2pPort` | 8765 | P2P WebSocket port |
| `service.dhtPort` | 8468 | DHT UDP port |
| `talos.difficulty` | 2 | Mining difficulty |
| `persistence.enabled` | true | Enable PVC |
| `persistence.size` | 1Gi | Storage size |
| `autoscaling.enabled` | false | Enable HPA |

### Custom Values

```yaml
# custom-values.yaml
replicaCount: 5

talos:
  difficulty: 3
  logLevel: DEBUG

resources:
  limits:
    cpu: 1000m
    memory: 1Gi

persistence:
  size: 10Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
```

```bash
helm install talos ./deploy/helm/talos -f custom-values.yaml
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TALOS_NODE_ID` | auto | Node identifier |
| `TALOS_DIFFICULTY` | 2 | Mining difficulty |
| `TALOS_LOG_LEVEL` | INFO | Log level |
| `TALOS_DATA_DIR` | /app/data | Data directory |
| `TALOS_KEYS_DIR` | /app/keys | Keys directory |
| `TALOS_BOOTSTRAP` | false | Bootstrap mode |

---

## Security

- Non-root user in container
- Read-only filesystem (optional)
- Resource limits
- Network policies
- Secret management for keys

---

## Monitoring

```yaml
# Pod annotations for Prometheus
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
```

---

## See Also

- [Getting Started](Getting-Started.md)
- [Development](Development.md)
