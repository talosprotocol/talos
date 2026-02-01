# Getting Started

This guide walks you through setting up the Talos development environment.

## Prerequisites

| Tool | Version | Check |
| :--- | :--- | :--- |
| Python | 3.11+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| Rust | stable | `cargo --version` |
| Git | 2.x | `git --version` |

## Step 1: Clone with Submodules

```bash
# SSH (recommended if you have keys configured)
git clone --recurse-submodules git@github.com:talosprotocol/talos.git

# HTTPS (alternative)
git clone --recurse-submodules https://github.com/talosprotocol/talos.git

cd talos
```

> **Already cloned without submodules?**
>
> ```bash
> git submodule update --init --recursive
> ```

## Step 2: Run Setup

The setup script initializes all submodules and configures SSH/HTTPS fallback:

```bash
./deploy/scripts/setup.sh
```

**Environment Variables:**

| Variable | Default | Description |
| :--- | :--- | :--- |
| `TALOS_SETUP_MODE` | `lenient` | `lenient` = warn on missing repos, `strict` = fail |
| `TALOS_USE_GLOBAL_INSTEADOF` | `0` | Set to `1` to configure HTTPS fallback globally |

## Step 3: Validate Toolchain

```bash
# Check all prerequisites
./deploy/scripts/run_all_tests.sh --help
```

The test runner checks for:

- bash, python3, node, npm, curl
- cargo (Rust toolchain)
- rg (ripgrep, optional)

## Step 4: Run Tests

```bash
# Run all unit tests (no live services)
./deploy/scripts/run_all_tests.sh

# Run with live integration tests (starts Gateway + Dashboard)
./deploy/scripts/run_all_tests.sh --with-live

# Test single repo
./deploy/scripts/run_all_tests.sh --only talos-contracts
```

## Step 5: Start Services

```bash
# Start all services (validates, rebuilds if needed)
./deploy/scripts/start_all.sh

# Verify services are running
curl http://localhost:8000/api/gateway/status  # Gateway
curl http://localhost:3000                      # Dashboard
```

## Per-Repo Development

Each repo has a Makefile:

```bash
cd services/gateway

make install    # Install dependencies
make build      # Build artifacts
make test       # Run tests
make lint       # Run linters
make start      # Start service
make stop       # Stop service
make clean      # Remove all dependencies
```

## Directory Structure

```text
talos/
├── contracts/               # talos-contracts (Schemas & Vectors)
├── core/                    # talos-core-rs (Rust Performance Kernel)
├── sdks/                    # Polyglot SDKs
│   ├── python/              # talos-sdk-py
│   ├── typescript/          # talos-sdk-ts
│   ├── go/                  # talos-sdk-go
│   ├── java/                # talos-sdk-java
│   └── rust/                # talos-sdk-rust
├── services/                # Backend Services
│   ├── ai-gateway/          # LLM & MCP Unified Access
│   ├── audit/               # Tamper-Evident Audit Log
│   ├── mcp-connector/       # Secure Tool Sandbox
│   └── configuration/       # Adaptive Budgets & Policy
├── site/                    # Web Components
│   ├── dashboard/           # Security Console (Next.js)
│   └── marketing/           # Landing Page
├── deploy/                  # Infrastructure & Scripts
│   ├── k8s/                 # Kubernetes Manifests
│   ├── helm/                # Helm Charts
│   └── scripts/             # Setup & Orchestration Scripts
├── docs/                    # Documentation (talos-docs)
├── scripts/                 # Auxiliary Python/Bash Scripts
└── tools/                   # talos-tui & Setup Helpers
```

## Troubleshooting

### SSH fails, stuck on "Permission denied"

```bash
# Use HTTPS fallback
TALOS_USE_GLOBAL_INSTEADOF=1 ./deploy/scripts/setup.sh
```

### Submodule shows "(deleted)" or path missing

```bash
git submodule update --init --recursive
```

### Clean slate (remove all dependencies)

```bash
./deploy/scripts/cleanup_all.sh
./deploy/scripts/setup.sh
```

## Next Steps

- [Development Workflow](guides-development) – Makefiles, testing, scripts
- [Architecture](architecture-overview) – System design
- [Testing](testing-testing) – Test suite details
- [Python SDK](sdk-python-sdk) – Use the Python client
- [TypeScript SDK](sdk-typescript-sdk) – Use the TypeScript client
