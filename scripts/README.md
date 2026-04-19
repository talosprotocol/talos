# Talos Scripts

This directory is for root-level developer tooling. Keep service-specific scripts
inside the owning service's `scripts/` directory, and keep full-stack operations
under `deploy/scripts/`.

## Canonical Entry Points

- `deploy/scripts/setup.sh`: initialize submodules and local tooling.
- `deploy/scripts/start_all.sh`: start the full local stack.
- `deploy/scripts/stop_all.sh`: stop local stack processes.
- `deploy/scripts/run_all_tests.sh`: run the discovery-based test runner.
- `deploy/scripts/cleanup_all.sh`: stop services and clean dependencies/caches.
- `scripts/cleanup_generated.sh`: remove generated logs, response files, local
  test DB sidecars, Python caches, and downloaded test artifacts without
  touching source, `.env`, or user config.
- `api-testing/`: root-level API testing assets, including Postman, pytest,
  Karate, and local-stack seed helpers.
- `docs/metrics/`: benchmark and performance result snapshots.

## Layout

- `scripts/bash/`: shell helpers and hooks that operate from the repo root.
- `scripts/python/`: Python utilities for contract, vector, traffic, and demo
  workflows.
- `scripts/gates/`: CI and preflight gates.
- `scripts/perf/`: benchmark and performance tooling.
- `scripts/db/`: local database bootstrap SQL.

Avoid adding one-off logs, response JSON files, PID files, or downloaded jars to
the repo root. Use `scripts/cleanup_generated.sh` before handing off a local
stack run.
