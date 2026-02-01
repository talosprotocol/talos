---
status: Implemented
audience: Developer, Operator
---

# Compatibility Matrix

> **Problem**: Users need to know what's supported.  
> **Guarantee**: Explicit compatibility information.  
> **Non-goal**: Supporting every platform.

---

## Python Support

| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.11+ | ✅ Supported | Recommended |
| 3.10 | ⚠️ Partial | May work, not tested |
| 3.9 and below | ❌ Not supported | Missing async features |

**Required**:
```bash
python --version  # Must be 3.11+
```

---

## Operating Systems

| OS | Status | Notes |
|----|--------|-------|
| **macOS** (Intel) | ✅ Supported | Tested on Monterey+ |
| **macOS** (Apple Silicon) | ✅ Supported | Native ARM, tested on M1/M2 |
| **Linux** (x86_64) | ✅ Supported | Ubuntu 20.04+, Debian 11+ |
| **Linux** (ARM64) | ✅ Supported | Raspberry Pi 4+, AWS Graviton |
| **Windows** | ⚠️ Partial | Works with WSL2 |
| **Windows** (Native) | ❌ Not tested | LMDB may have issues |

---

## Container Platforms

| Platform | Status | Notes |
|----------|--------|-------|
| **Docker** | ✅ Supported | Official image available |
| **Docker Compose** | ✅ Supported | Multi-node setup |
| **Podman** | ✅ Supported | Rootless works |
| **containerd** | ✅ Supported | K8s compatible |

**Docker image**:
```bash
docker pull ghcr.io/nileshchakraborty/talos:latest
```

---

## Kubernetes

| K8s Version | Status | Notes |
|-------------|--------|-------|
| 1.28+ | ✅ Supported | Recommended |
| 1.25-1.27 | ✅ Supported | Tested |
| 1.24 and below | ⚠️ Partial | May work |

| Distribution | Status |
|--------------|--------|
| **EKS** | ✅ Supported |
| **GKE** | ✅ Supported |
| **AKS** | ✅ Supported |
| **k3s** | ✅ Supported |
| **minikube** | ✅ Supported |
| **kind** | ✅ Supported |
| **OpenShift** | ⚠️ Partial |

**Helm chart**:
```bash
helm repo add talos https://nileshchakraborty.github.io/talos/charts
helm install talos talos/talos
```

---

## Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `cryptography` | ≥41.0 | Ed25519, X25519, ChaCha20 |
| `pydantic` | ≥2.0 | Data validation |
| `websockets` | ≥12.0 | P2P transport |
| `lmdb` | ≥1.4 | Local storage |
| `orjson` | ≥3.9 | Fast JSON |
| `click` | ≥8.1 | CLI |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `prometheus-client` | ≥0.17 | Metrics export |
| `opentelemetry-api` | ≥1.20 | Tracing |
| `uvloop` | ≥0.19 | Performance (Linux/macOS) |

---

## Network Requirements

### Ports

| Port | Protocol | Purpose | Required |
|------|----------|---------|----------|
| 8765 | TCP/WebSocket | P2P communication | Yes |
| 8766 | TCP/WebSocket | Registry server | If running registry |
| 9090 | TCP/HTTP | Prometheus metrics | Optional |
| 8000 | TCP/HTTP | Health endpoints | Optional |

### Firewall

```bash
# Required for agent
ufw allow 8765/tcp

# Required for registry
ufw allow 8766/tcp
```

### NAT Traversal

| Method | Status | Notes |
|--------|--------|-------|
| UPnP | ⚠️ Partial | If router supports |
| STUN | 📋 Planned | Roadmap |
| TURN | 📋 Planned | Roadmap |
| Manual port forward | ✅ Works | Recommended for servers |

---

## Storage Requirements

### Disk Space

| Component | Requirement | Notes |
|-----------|-------------|-------|
| Installation | ~50 MB | Python package |
| Runtime | ~100 MB | Keys, config |
| Audit log | Variable | ~1 KB per entry |
| Docker image | ~250 MB | Compressed |

### Database

| Backend | Status | Notes |
|---------|--------|-------|
| LMDB | ✅ Default | Fast, embedded |
| SQLite | 📋 Planned | Alternative |
| PostgreSQL | 📋 Planned | Enterprise option |

---

## Blockchain Anchoring

| Chain | Status | Notes |
|-------|--------|-------|
| Ethereum L2 (Optimism) | ✅ Supported | Recommended |
| Ethereum L2 (Arbitrum) | ✅ Supported | Alternative |
| Ethereum Mainnet | ✅ Supported | Expensive |
| Polygon | ⚠️ Partial | Testing |
| Private Ethereum | ✅ Supported | Enterprise |
| None (local only) | ✅ Supported | No external anchor |

---

## LLM Integration

| Framework | Status | Notes |
|-----------|--------|-------|
| **LangChain** | 📋 Planned | Adapter in progress |
| **LlamaIndex** | 📋 Planned | Adapter planned |
| **CrewAI** | 📋 Planned | Integration guide |
| **Ollama** | ✅ Supported | Local-first |
| **OpenAI API** | ✅ Works | Via MCP |
| **Anthropic API** | ✅ Works | Via MCP |

---

## MCP Compatibility

| MCP Server | Status | Notes |
|------------|--------|-------|
| `@modelcontextprotocol/server-filesystem` | ✅ Tested | File operations |
| `@modelcontextprotocol/server-postgres` | ✅ Tested | Database |
| `@modelcontextprotocol/server-slack` | ⚠️ Partial | Needs testing |
| Custom MCP servers | ✅ Supported | Follow spec |

---

## Testing Matrix

| Test Type | CI Status | Coverage |
|-----------|-----------|----------|
| Unit tests | ✅ Passing | 79% |
| Integration tests | ✅ Passing | - |
| E2E tests | ✅ Passing | - |
| Security tests | ✅ Passing | - |
| Performance tests | ✅ Passing | - |

**Test counts**:
- Total: 496 tests
- Crypto: 50+
- Protocol: 100+
- SDK: 19
- MCP: 20+

---

## Known Limitations

| Limitation | Workaround |
|------------|------------|
| Windows native not fully tested | Use WSL2 |
| No iOS/Android SDK | Use HTTP bridge |
| No browser SDK | TypeScript SDK planned |
| LMDB max DB size 10TB | Sufficient for most cases |

---

## Version Compatibility

| Talos Version | Wire Protocol | Breaking Changes |
|---------------|---------------|------------------|
| 5.15.x | v2 | - |
| 1.x | v1 | Not compatible with 2.x |

**Protocol negotiation**: Automatic version detection on handshake.

---

**See also**: [Getting Started](getting-started-getting-started) | [Infrastructure](architecture-infrastructure) | [Testing](testing)
