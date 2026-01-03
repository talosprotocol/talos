# Talos Protocol

> **Secure, Decentralized Communication for the AI Agent Era**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-700%2B%20passing-green.svg)](#testing)

## 🚀 Quick Start

```bash
# Clone with all submodules
git clone --recurse-submodules git@github.com:talosprotocol/talos.git
cd talos

# Initialize and validate
./deploy/scripts/setup.sh
./deploy/scripts/run_all_tests.sh
```

> **SSH not available?** The setup script auto-falls back to HTTPS.

---

## 📂 Repository Topology

This is a **multi-repo project** using git submodules:

```
talos/                          # Orchestrator (this repo)
├── deploy/
│   ├── repos/                  # 8 submodules
│   │   ├── talos-contracts/    # Source of truth (schemas, vectors)
│   │   ├── talos-core-rs/      # Rust performance kernel
│   │   ├── talos-sdk-py/       # Python SDK
│   │   ├── talos-sdk-ts/       # TypeScript SDK
│   │   ├── talos-gateway/      # FastAPI Gateway
│   │   ├── talos-audit-service/# Audit aggregator
│   │   ├── talos-mcp-connector/# MCP bridge
│   │   └── talos-dashboard/    # Next.js Console
│   └── scripts/
│       ├── setup.sh            # Initialize submodules
│       ├── start_all.sh        # Start all services
│       ├── cleanup_all.sh      # Clean all dependencies
│       └── run_all_tests.sh    # Master test runner
└── docs/wiki/                  # Documentation
```

| Repo | Purpose | Tech |
|------|---------|------|
| `talos-contracts` | Schemas, test vectors, helpers | TypeScript + Python |
| `talos-core-rs` | High-performance kernel | Rust + PyO3 |
| `talos-sdk-py` | Python SDK | Python |
| `talos-sdk-ts` | TypeScript SDK | TypeScript |
| `talos-gateway` | REST API Gateway | FastAPI |
| `talos-audit-service` | Audit log aggregation | FastAPI |
| `talos-mcp-connector` | MCP protocol bridge | Python |
| `talos-dashboard` | Security console UI | Next.js |

---

## 📜 Contract-Driven Architecture

**`talos-contracts` is the single source of truth.** All other repos consume:

| Artifact | Description |
|----------|-------------|
| `schemas/*.json` | JSON Schema definitions |
| `test_vectors/*.json` | Golden test cases |
| `src/` (TS) / `talos_contracts/` (Py) | Reference implementations |

**Boundary Rules:**
- ❌ No reimplementing `deriveCursor`, `base64url`, etc. outside contracts
- ❌ No `btoa`/`atob` in browser code (use contracts helpers)
- ❌ No deep cross-repo imports (use published packages)

---

## v4.0 Features

| Feature | Status | Description |
|---------|--------|-------------|
| 📜 **Contract-Driven Kernel** | ✅ | `talos-contracts` as single source of truth |
| 🔐 **Capability Authorization** | ✅ | Cryptographic tokens, <1ms session-cached auth |
| 📦 **Polyglot SDKs** | ✅ | Native Python & TypeScript SDKs |
| 🦀 **Rust Wedge** | ✅ | High-performance Rust core |
| 🔄 **Double Ratchet** | ✅ | Signal protocol for forward secrecy |
| ✅ **Validation Engine** | ✅ | 5-layer block validation |
| 💡 **Light Client** | ✅ | SPV proof verification |
| 🤖 **MCP Integration** | ✅ | Secure tool invocation |
| ⚡ **Performance** | ✅ | 695k auth/sec, <5ms p99 |

---

## 🛠️ Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Rust (stable)
- Git with SSH keys (or HTTPS fallback)

### Setup Modes

| Mode | Default | Behavior |
|------|---------|----------|
| `lenient` | Local | Warns on missing submodules, continues |
| `strict` | CI | Fails if any submodule unavailable |

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

### Testing

```bash
# Run all tests (unit only)
./deploy/scripts/run_all_tests.sh

# With live integration tests
./deploy/scripts/run_all_tests.sh --with-live

# Single repo
./deploy/scripts/run_all_tests.sh --only talos-contracts
```

---

## 📚 Documentation

| Topic | Link |
|-------|------|
| Getting Started | [docs/wiki/Getting-Started.md](docs/wiki/Getting-Started.md) |
| Architecture | [docs/wiki/Architecture.md](docs/wiki/Architecture.md) |
| Development | [docs/wiki/Development.md](docs/wiki/Development.md) |
| Testing | [docs/wiki/Testing.md](docs/wiki/Testing.md) |
| Python SDK | [docs/wiki/Python-SDK.md](docs/wiki/Python-SDK.md) |
| TypeScript SDK | [docs/wiki/TypeScript-SDK.md](docs/wiki/TypeScript-SDK.md) |
| MCP Integration | [docs/wiki/MCP-Integration.md](docs/wiki/MCP-Integration.md) |

---

## Why Talos Exists

AI agents lack a trustable communication substrate:

| Problem | Current State | Talos Solution |
|---------|---------------|----------------|
| **Identity** | No cryptographic identity | Self-sovereign DIDs |
| **Authorization** | Centralized OAuth/RBAC | Scoped capability tokens |
| **Confidentiality** | TLS at best | Forward secrecy (Double Ratchet) |
| **Accountability** | Trust the operator | Blockchain-anchored proofs |
| **Decentralization** | Central servers | P2P with DHT discovery |

> **Talos is the missing trust layer for autonomous AI systems.**

📖 [Why Talos Wins](docs/wiki/Why-Talos-Wins.md) | [Threat Model](docs/wiki/Threat-Model.md) | [Alternatives](docs/wiki/Alternatives-Comparison.md)

---

## License

MIT © 2024 Talos Protocol Contributors

