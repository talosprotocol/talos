# Testing

This guide covers the Talos test infrastructure.

## Overview

The test suite validates:
- **Contract compliance**: Schemas, vectors, helpers
- **Boundary purity**: No duplicated logic across repos
- **Unit tests**: Per-repo test suites
- **Integration tests**: Live service validation

## Test Runner

The master test runner orchestrates all tests:

```bash
./deploy/scripts/run_all_tests.sh
```

### Flags

| Flag | Description |
|------|-------------|
| `--with-live` | Run live integration tests (starts services) |
| `--skip-build` | Skip build steps (faster, uses cached artifacts) |
| `--only <repo>` | Test single repo only |
| `--report <path>` | Custom report output path |

### Examples

```bash
# Full unit tests
./deploy/scripts/run_all_tests.sh

# With live integration
./deploy/scripts/run_all_tests.sh --with-live

# Single repo
./deploy/scripts/run_all_tests.sh --only talos-contracts

# CI mode (skip build for cached artifacts)
./deploy/scripts/run_all_tests.sh --skip-build
```

## Test Isolation

Tests use environment isolation:

| Variable | Purpose |
|----------|---------|
| `TALOS_ENV=test` | Marks test environment |
| `TALOS_RUN_ID=<uuid>` | Unique per test run |
| `TALOS_DB_PATH=/tmp/talos_test_*.db` | Ephemeral storage |

## Boundary Gate

The boundary purity gate prevents architectural drift:

```bash
./deploy/scripts/check_boundaries.sh
```

**Checks:**
1. ❌ No `deriveCursor` reimplementation outside contracts
2. ❌ No `btoa`/`atob` usage (use contracts helpers)
3. ❌ No deep cross-repo imports

## Vector Compliance

Test vectors in `talos-contracts/test_vectors/` are the source of truth:

```bash
./deploy/scripts/ci_verify_vectors.sh
```

**Validates:**
- Directory exists
- JSON files are valid
- At least one vector file present

## Per-Repo Tests

Each repo has a `scripts/test.sh`:

| Repo | Test Framework | Linter |
|------|----------------|--------|
| talos-contracts | Vitest + pytest | ESLint + ruff |
| talos-core-rs | cargo test | clippy |
| talos-sdk-py | pytest | ruff |
| talos-sdk-ts | Vitest | ESLint |
| talos-gateway | pytest | ruff |
| talos-audit-service | pytest | ruff |
| talos-mcp-connector | pytest | ruff |
| talos-dashboard | Vitest | ESLint |

Run via Makefile:

```bash
cd deploy/repos/talos-gateway
make test
make lint
```

## Live Integration Tests

Enabled with `--with-live`:

1. Starts Gateway on port 8080
2. Starts Dashboard on port 3000
3. Validates `/api/gateway/status` endpoint
4. Runs cross-language vector verification
5. Cleans up on exit (trap-based)

## CI Workflow

GitHub Actions runs on every PR:

```yaml
jobs:
  verify:
    steps:
      - Verify submodules (strict)
      - Contract boundary purity gate
      - Verify test vectors
      - Run master test runner
```

### Running CI Locally

```bash
# Mirror CI environment
TALOS_SETUP_MODE=strict ./deploy/scripts/setup.sh
./deploy/scripts/check_boundaries.sh
./deploy/scripts/ci_verify_vectors.sh
./deploy/scripts/run_all_tests.sh --skip-build
```

## Reports and Logs

| Location | Content |
|----------|---------|
| `deploy/reports/logs/*.log` | Per-repo test output |
| `/tmp/talos-*.log` | Service runtime logs |
| Console output | Summary with ✓/✗ indicators |

## Coverage

Coverage targets are per-repo. Run with:

```bash
# Python
cd deploy/repos/talos-gateway
pytest --cov=.

# TypeScript
cd deploy/repos/talos-sdk-ts
npm test -- --coverage
```

## Adding Tests

1. **Schema tests**: Add to `talos-contracts/test_vectors/`
2. **Unit tests**: Add to repo's `tests/` or `test/` directory
3. **Integration tests**: Extend `test_integration.sh`
