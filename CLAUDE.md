# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the Talos Protocol, a secure, decentralized communication platform for AI agents. The repository uses a multi-repo architecture with git submodules as the core organizational pattern.

## Repository Structure

The project follows a contract-driven architecture where `contracts/` is the single source of truth. Key directories include:

- `contracts/` - JSON schemas, test vectors, and reference implementations
- `core/` - Rust performance kernel
- `sdks/` - Polyglot SDKs (Python, TypeScript, Go, Java, Rust)
- `services/` - Various microservices (gateway, audit, MCP connector, etc.)
- `site/` - Dashboard and marketing site
- `deploy/` - Deployment configurations and scripts

## Common Development Commands

### Setup and Initialization
```bash
# Clone with all submodules
git clone --recurse-submodules <repository-url>
cd talos

# Initialize environment
./deploy/scripts/setup.sh

# Update submodules to pinned versions
git submodule update --init --recursive
```

### Building
```bash
# Build entire ecosystem
make build

# Build all SDKs
make build-all-sdks

# Run pre-commit validation
scripts/pre-commit
```

### Testing
```bash
# Run all tests
make test

# Run tests with discovery-based runner
./run_all_tests.sh

# Run tests for changed files only
./run_all_tests.sh --changed

# Run full CI suite
./run_all_tests.sh --ci

# Run specific repo tests
cd core && scripts/test.sh --unit
```

### Running Services
```bash
# Start all services locally
make dev
# or
./deploy/scripts/start_all.sh

# Stop and clean up
make clean
# or
./deploy/scripts/cleanup_all.sh
```

### Docker Operations
```bash
# Build core Docker images
make docker-build

# Build all Docker images
make docker-build-all

# Start SDK development environment
make docker-dev-up
```

## Architecture Guidelines

1. **Contract-Driven Development**: All interfaces and data structures are defined in `contracts/` and must be consumed by all other repositories.

2. **Boundary Rules**:
   - No reimplementing core functions outside contracts
   - No browser-specific functions like `btoa`/`atob`
   - No deep cross-repo imports

3. **Submodule Management**:
   - Uses pinned-SHA strategy for reproducibility
   - CI fails if pinned SHAs don't match remote `origin/main`
   - Automated sync workflows update submodules periodically

4. **Testing Strategy**:
   - Each repo has a standardized `scripts/test.sh` entrypoint
   - Discovery-based test runner finds `.agent/test_manifest.yml` files
   - Supports smoke, unit, integration, and coverage test modes
   - CI enforces coverage thresholds via `scripts/coverage_coordinator.py`

## Language-Specific Patterns

### Rust (Core)
- Uses `cargo test` for unit tests
- `cargo llvm-cov` for coverage reports
- Tests located in `tests/` directory

### Python (SDKs)
- Uses `pytest` with `PYTHONPATH=src`
- Coverage via `--cov` flags
- Tests located in `tests/` directory

### TypeScript (Contracts, SDKs)
- Uses `npm test` (typically Jest)
- Tests colocated with source files
- Build validation via `npm run build`

## Key Scripts and Tools

- `run_all_tests.sh` - Orchestration script for running tests across all repos
- `deploy/scripts/setup.sh` - Environment setup and submodule initialization
- `deploy/scripts/start_all.sh` - Service startup orchestration
- `scripts/pre-commit` - Pre-commit validation hook
- `deploy/submodules.py` - Submodule management utility

## Development Workflow

1. Make changes in appropriate submodule/repository
2. Run `make test` or `./run_all_tests.sh --changed` to validate
3. Run `make build` to ensure build integrity
4. Commit changes (triggers pre-commit hooks)
5. Push to remote for CI validation