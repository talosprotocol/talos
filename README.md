# Talos Protocol

> **Secure, Decentralized Communication for the AI Agent Era**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://img.shields.io/badge/tests-700%2B%20passing-green.svg)](#testing)
[![Docker Build & Push](https://github.com/talosprotocol/talos/actions/workflows/docker.yml/badge.svg)](https://github.com/talosprotocol/talos/actions/workflows/docker.yml)

> **Note to Contributors (Phase 1 Migration)**: The `talos-docs` submodule has moved from `deploy/repos/talos-docs` to `docs/`. Please run the following to update your workspace:
>
> ```bash
> git submodule sync --recursive
> git submodule update --init --recursive
> ```

## 🚀 Quick Start

```bash
# Clone with all submodules
git clone --recurse-submodules git@github.com:talosprotocol/talos.git
cd talos

# Initialize and validate
./deploy/scripts/setup.sh
./run_all_tests.sh --ci --changed
```

> **SSH not available?** The setup script auto-falls back to HTTPS.

---

## 📂 Repository Topology

This is a **multi-repo project** using git submodules:

```text
talos/                          # Orchestrator (this repo)
├── deploy/
│   ├── repos/                  # 12 submodules
│   │   ├── talos-contracts/    # Source of truth (schemas, vectors)
│   │   ├── talos-core-rs/      # Rust performance kernel
│   │   ├── talos-sdk-py/       # Python SDK
│   │   ├── talos-sdk-ts/       # TypeScript SDK
│   │   ├── talos-sdk-go/       # Go SDK
│   │   ├── talos-sdk-java/     # Java SDK
│   │   ├── talos-gateway/      # FastAPI Gateway
│   │   ├── talos-audit-service/# Audit aggregator
│   │   ├── talos-mcp-connector/# MCP bridge
│   │   ├── talos-dashboard/    # Next.js Console
│   │   ├── talos-docs/         # Documentation wiki
│   │   └── talos-examples/     # Example applications
│   └── scripts/
│       ├── setup.sh            # Initialize submodules
│       ├── start_all.sh        # Start all services
│       ├── cleanup_all.sh      # Clean all dependencies
│       └── setup_hooks.sh      # Install git hooks
├── run_all_tests.sh            # Master test runner (Discovery-based)
└── docs/wiki/                  # Documentation (deprecated, use talos-docs)
```

| Repo                  | Purpose                        | Tech                |
| --------------------- | ------------------------------ | ------------------- |
| `talos-contracts`     | Schemas, test vectors, helpers | TypeScript + Python |
| `talos-core-rs`       | High-performance kernel        | Rust + PyO3         |
| `talos-sdk-py`        | Python SDK                     | Python              |
| `talos-sdk-ts`        | TypeScript SDK                 | TypeScript          |
| `talos-sdk-go`        | Go SDK                         | Go                  |
| `talos-sdk-java`      | Java SDK                       | Java                |
| `talos-gateway`       | REST API Gateway               | FastAPI             |
| `talos-audit-service` | Audit log aggregation          | FastAPI             |
| `talos-mcp-connector` | MCP protocol bridge            | Python              |
| `talos-dashboard`     | Security console UI            | Next.js             |
| `talos-docs`          | Documentation wiki             | Markdown            |
| `talos-examples`      | Example applications           | Mixed               |

---

## 📜 Contract-Driven Architecture

**`talos-contracts` is the single source of truth.** All other repos consume:

| Artifact                              | Description               |
| ------------------------------------- | ------------------------- |
| `schemas/*.json`                      | JSON Schema definitions   |
| `test_vectors/*.json`                 | Golden test cases         |
| `src/` (TS) / `talos_contracts/` (Py) | Reference implementations |

**Boundary Rules:**

- ❌ No reimplementing `deriveCursor`, `base64url`, etc. outside contracts
- ❌ No `btoa`/`atob` in browser code (use contracts helpers)
- ❌ No deep cross-repo imports (use published packages)

---

## v4.0 Features

| Feature                         | Status | Description                                    |
| ------------------------------- | ------ | ---------------------------------------------- |
| 📜 **Contract-Driven Kernel**   | ✅     | `talos-contracts` as single source of truth    |
| 🔐 **Capability Authorization** | ✅     | Cryptographic tokens, <1ms session-cached auth |
| 📦 **Polyglot SDKs**            | ✅     | Native Python & TypeScript SDKs                |
| 🦀 **Rust Wedge**               | ✅     | High-performance Rust core                     |
| 🔄 **Double Ratchet**           | ✅     | Signal protocol for forward secrecy            |
| ✅ **Validation Engine**        | ✅     | 5-layer block validation                       |
| 💡 **Light Client**             | ✅     | SPV proof verification                         |
| 🤖 **MCP Integration**          | ✅     | Secure tool invocation                         |
| ⚡ **Performance**              | ✅     | 695k auth/sec, <5ms p99                        |

---

## 🚢 Production-Ready Deployment

**SRE-Grade Kubernetes deployment with comprehensive CI/CD and monitoring.**

| Component         | Status | Description                             |
| ----------------- | ------ | --------------------------------------- |
| 🐳 **Docker**     | ✅     | Multi-stage builds, non-root (UID 1001) |
| ☸️ **Kubernetes** | ✅     | Manifests, NetworkPolicies, Kustomize   |
| 🔄 **CI/CD**      | ✅     | GitHub Actions, Trivy, SBOM, Kind       |
| 📊 **Monitoring** | ✅     | Prometheus metrics, ServiceMonitors     |
| 📦 **Helm Chart** | ✅     | Production + dev values                 |

### Quick Deploy

```bash
# Helm (recommended)
helm install talos deploy/helm/talos \
  --namespace talos-system --create-namespace

# Kustomize
kubectl apply -k deploy/k8s/overlays/kind
```

**Key Features:**

- ✅ Zero-curl healthchecks (Python-based)
- ✅ Read-only rootfs with proper mounts
- ✅ Two-ingress architecture (no routing collisions)
- ✅ Migration Jobs with readiness validation
- ✅ Comprehensive CI (build, scan, test)
- ✅ Prometheus metrics + alerting

📖 **[Production Deployment Guide](docs/DEPLOYMENT.md)**

## 🛠️ Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Rust (stable)
- Git with SSH keys (or HTTPS fallback)

### Setup Modes

| Mode      | Default | Behavior                               |
| --------- | ------- | -------------------------------------- |
| `lenient` | Local   | Warns on missing submodules, continues |
| `strict`  | CI      | Fails if any submodule unavailable     |

```bash
# Local development (lenient)
./deploy/scripts/setup.sh

# Mirror CI behavior
TALOS_SETUP_MODE=strict ./deploy/scripts/setup.sh
```

### Service Management

```bash
# Start all services
./deploy/scripts/start_all.sh

# Stop and clean everything
./deploy/scripts/cleanup_all.sh

# Per-repo Makefile
cd deploy/repos/talos-gateway
make install build test start
```

### Submodule Management

This project uses a **pinned-SHA** strategy for submodules to guarantee reproducibility.

- **Strict Drift Gate**: CI fails if pinned SHAs do not match the remote `origin/main` of the submodule.
- **Automated Sync**: A bot workflow runs periodically to fast-forward submodules to `latest main` and opens a PR.

**Common Commands:**

```bash
# Initialize submodules to pinned state
git submodule update --init --recursive

# Check for drift (Are my pins behind?)
./scripts/check_submodule_drift.sh

# Manually sync local submodules (updates working tree only)
git submodule foreach 'git fetch origin main && git reset --hard origin/main'
```

> **Private Repositories**: If a submodule becomes private, you must ensure your CI environment and local git configuration have appropriate credentials (via SSH keys or `GITHUB_TOKEN` permissions), otherwise the drift check will fail.

### Testing

```bash
# Run standard CI suite for changed repos (Discovery-based)
./run_all_tests.sh --ci --changed

# Run full suite (Unit + Integration + Coverage)
./run_all_tests.sh --full

# Single repo manual override
cd core && scripts/test.sh --unit
```

---

### Dashboard & Examples

Once started, access the Security Console:

- **Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Examples Catalog**: [http://localhost:3000/examples](http://localhost:3000/examples)

---

## 📚 Documentation

Documentation is maintained in the [Wiki](https://github.com/talosprotocol/talos/wiki).

| Topic           | Link                                                                           |
| --------------- | ------------------------------------------------------------------------------ |
| Getting Started | [Getting Started](https://github.com/talosprotocol/talos/wiki/Getting-Started) |
| Architecture    | [Architecture](https://github.com/talosprotocol/talos/wiki/Architecture)       |
| Development     | [Development](https://github.com/talosprotocol/talos/wiki/Development)         |
| Testing         | [Testing](https://github.com/talosprotocol/talos/wiki/Testing)                 |
| Python SDK      | [Python SDK](https://github.com/talosprotocol/talos/wiki/Python-SDK)           |
| TypeScript SDK  | [TypeScript SDK](https://github.com/talosprotocol/talos/wiki/TypeScript-SDK)   |
| MCP Integration | [MCP Integration](https://github.com/talosprotocol/talos/wiki/MCP-Integration) |

---

## Why Talos Exists

AI agents lack a trustable communication substrate:

| Problem              | Current State             | Talos Solution                   |
| -------------------- | ------------------------- | -------------------------------- |
| **Identity**         | No cryptographic identity | Self-sovereign DIDs              |
| **Authorization**    | Centralized OAuth/RBAC    | Scoped capability tokens         |
| **Confidentiality**  | TLS at best               | Forward secrecy (Double Ratchet) |
| **Accountability**   | Trust the operator        | Blockchain-anchored proofs       |
| **Decentralization** | Central servers           | P2P with DHT discovery           |

> **Talos is the missing trust layer for autonomous AI systems.**

📖 [Why Talos Wins](docs/wiki/Why-Talos-Wins.md) | [Threat Model](docs/wiki/Threat-Model.md) | [Alternatives](docs/wiki/Alternatives-Comparison.md)

---

## License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE).

# trigger

# ci
