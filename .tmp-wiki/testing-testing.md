# Testing

This guide covers the Talos test infrastructure.

## Overview

The test suite validates:

- **Contract compliance**: Schemas, vectors, helpers
- **Boundary purity**: No duplicated logic across repos
- **Unit tests**: Per-repo test suites
- **Integration tests**: Live service validation

## Test Runner (Universal Orchestrator)

The master test runner uses **auto-discovery** to detect and valid repositories. It scans for `.agent/test_manifest.yml` and triggers the standardized contract.

```bash
./run_all_tests.sh [options]
```

### Flags

| Flag               | Description                                         |
| ------------------ | --------------------------------------------------- |
| `--ci`             | Run standard CI suite (Smoke + Unit + Coverage)     |
| `--full`           | Run everything (Unit + Integration + Coverage)      |
| `--changed`        | Only run tests for repos affected by recent changes |
| `--changed-mode M` | Discovery mode: `staged`, `workspace`, or `ci`      |
| `--keep-going`     | Continue running even if a repo fails               |

### Examples

```bash
# Optimized developer workflow (staged changes only)
./run_all_tests.sh --ci --changed --changed-mode staged

# Full workspace regression
./run_all_tests.sh --full

# Single repo manual run
cd core && scripts/test.sh --ci
```

## Test Isolation

Tests use environment isolation:

| Variable                               | Purpose                |
| -------------------------------------- | ---------------------- |
| `TALOS_ENV=test`                       | Marks test environment |
| `TALOS_RUN_ID=<uuid>`                  | Unique per test run    |
| `TALOS_DB_PATH=/tmp/talos_test_*.db`   | Ephemeral storage      |

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

| Repo                | Test Framework  | Linter        |
| ------------------- | --------------- | ------------- |
| talos-contracts     | Vitest + pytest | ESLint + ruff |
| talos-core-rs       | cargo test      | clippy        |
| talos-sdk-py        | pytest          | ruff          |
| talos-sdk-ts        | Vitest          | ESLint        |
| talos-gateway       | pytest          | ruff          |
| talos-audit-service | pytest          | ruff          |
| talos-mcp-connector | pytest          | ruff          |
| talos-dashboard     | Vitest          | ESLint        |

Run via Makefile:

```bash
cd services/gateway
make test
make lint
```

## Live Integration Tests

Enabled with `--with-live`:

1. Starts Gateway on port 8000
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

| Location                    | Content                      |
| --------------------------- | ---------------------------- |
| `deploy/reports/logs/*.log` | Per-repo test output         |
| `/tmp/talos-*.log`          | Service runtime logs         |
| Console output              | Summary with ✓/✗ indicators  |

## Coverage Enforcement

Coverage is automatically enforced by the `coverage_coordinator.py`.

### Threshold Levels

1. **Global**: Line and branch rates for the whole repo (manifested).
2. **Critical Paths**: High-security paths (e.g., `src/crypto/**`) can have higher requirements (95-100%).

### Workflow

1. Repos run tests and emit **Cobertura XML** to `artifacts/coverage/coverage.xml`.
2. The coordinator parses these reports and validates against `.agent/test_manifest.yml`.
3. CI/Hooks fail if any threshold is violated.

```bash
# Manual check of coverage artifacts
python3 scripts/coverage_coordinator.py --repos core sdks-python
```

## Adding Tests

1. **Schema tests**: Add to `talos-contracts/test_vectors/`
2. **Unit tests**: Add to repo's `tests/` or `test/` directory
3. **Integration tests**: Extend `test_integration.sh`

## Performance Testing

### Running Performance Tests

The project includes comprehensive performance tests to ensure SLA compliance and track performance regressions.

#### Core SLA Tests

Core authorization and capability tests with strict latency targets:

```bash
# From repo root
PYTHONPATH=src pytest tests/test_performance.py -v
```

#### Python SDK Benchmarks

Cryptographic operations benchmarks (wallet, double ratchet, A2A):

```bash
cd sdks/python
PYTHONPATH=src python benchmarks/bench_crypto.py
```

#### Full Performance Suite

Run all performance tests with JSON output and multiple runs:

```bash
./scripts/perf/run_all.sh
```

Results are saved to `artifacts/perf/<date>-<sha>/` with full metadata.

### Performance SLAs

- Authorization (cached session): <1ms p99
- Signature verification: <500μs
- Total Talos overhead: <5ms p99
- Authorization throughput: >10,000 auth/sec

See [Benchmarks](benchmarks) for detailed results and historical data.
