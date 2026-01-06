# Development

This guide covers the development workflow for the Talos multi-repo project.

## Repository Structure

Talos uses git submodules for 8 component repositories:

| Repo | Type | Tech |
|------|------|------|
| `talos-contracts` | Library | TypeScript + Python |
| `talos-core-rs` | Library | Rust + PyO3 |
| `talos-sdk-py` | Library | Python |
| `talos-sdk-ts` | Library | TypeScript |
| `talos-gateway` | Service | FastAPI |
| `talos-audit-service` | Service | FastAPI |
| `talos-mcp-connector` | Service | Python |
| `talos-dashboard` | Service | Next.js |

## Makefile Targets

Every repo has a `Makefile` with consistent targets:

```bash
cd deploy/repos/<repo-name>

make install    # Install dependencies
make build      # Build artifacts
make test       # Run tests
make lint       # Run linters
make clean      # Remove dependencies (source-only)

# Services only:
make start      # Start service
make stop       # Stop service
make status     # Check service status
```

## Master Scripts

### `setup.sh` – Initialize Submodules

```bash
./deploy/scripts/setup.sh
```

| Variable | Default | Description |
|----------|---------|-------------|
| `TALOS_SETUP_MODE` | `lenient` | `strict` fails on missing repos |
| `TALOS_USE_GLOBAL_INSTEADOF` | `0` | Set `1` for global HTTPS config |

### `start_all.sh` – Start All Services

Validates services, rebuilds if unhealthy, restarts:

```bash
./deploy/scripts/start_all.sh
```

Services started:
| Service | Port |
|---------|------|
| talos-gateway | 8080 |
| talos-audit-service | 8081 |
| talos-mcp-connector | 8082 |
| talos-dashboard | 3000 |

### `cleanup_all.sh` – Full Clean

Stops all services and removes dependencies:

```bash
./deploy/scripts/cleanup_all.sh
```

Leaves only source code, ready for fresh `setup.sh`.

### `run_all_tests.sh` – Master Test Runner

```bash
# Default (unit tests)
./deploy/scripts/run_all_tests.sh

# With live integration
./deploy/scripts/run_all_tests.sh --with-live

# Skip build steps
./deploy/scripts/run_all_tests.sh --skip-build

# Single repo
./deploy/scripts/run_all_tests.sh --only talos-contracts
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TALOS_ENV` | `production` | Set to `test` during tests |
| `TALOS_RUN_ID` | `default` | Unique test run ID for isolation |
| `TALOS_GATEWAY_PORT` | `8080` | Gateway port |
| `TALOS_DASHBOARD_PORT` | `3000` | Dashboard port |

## Boundary Rules

**Contract-First Architecture:**

```
talos-contracts (source of truth)
        ↓
    Publishes:
    - @talosprotocol/contracts (npm)
    - talos-contracts (PyPI)
        ↓
    Consumed by:
    - talos-sdk-*
    - talos-gateway
    - talos-dashboard
```

**Rules:**
1. ❌ No reimplementing `deriveCursor`, `base64url`, etc.
2. ❌ No `btoa`/`atob` in browser code
3. ❌ No deep cross-repo imports
4. ✅ Use published packages only

## Workflow: Adding a Feature

1. **Contracts first**: Start with schema/vector changes in `talos-contracts`
2. **SDK updates**: Propagate to `talos-sdk-py` / `talos-sdk-ts`
3. **Service updates**: Update Gateway, Audit, MCP if needed
4. **Dashboard**: Update UI if user-facing

## Workflow: Running CI Locally

Mirror CI behavior:

```bash
# Strict submodule check
TALOS_SETUP_MODE=strict ./deploy/scripts/setup.sh

# Full CI pipeline
./deploy/scripts/check_boundaries.sh
./deploy/scripts/ci_verify_vectors.sh
./deploy/scripts/run_all_tests.sh
```

## Logs and Reports

| Path | Description |
|------|-------------|
| `/tmp/talos-*.log` | Service logs |
| `/tmp/talos-*.pid` | Service PIDs |
| `deploy/reports/logs/` | Test runner logs |

## Git Submodule Workflow

### Update submodule to latest

```bash
cd deploy/repos/talos-contracts
git pull origin main
cd ../..
git add deploy/repos/talos-contracts
git commit -m "chore: update talos-contracts submodule"
```

### Check submodule status

```bash
git submodule status
```

### Reinitialize all

```bash
git submodule update --init --recursive
```
