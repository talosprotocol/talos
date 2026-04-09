# Talos Local Command Map

Setup and sync:
- `deploy/scripts/setup.sh`
- `git submodule update --init --recursive`

Common root commands:
- `make build` for the pre-commit validation pipeline
- `make test` for the default test suite
- `deploy/scripts/run_all_tests.sh --changed` for changed-surface validation
- `deploy/scripts/run_all_tests.sh --ci` for the CI-style discovery run
- `deploy/scripts/run_all_tests.sh --full` for the broadest suite

Runtime commands:
- `make dev` or `deploy/scripts/start_all.sh` to boot the local stack
- `start.sh` for the quick gateway plus dashboard demo path
- `deploy/scripts/cleanup_all.sh` to stop and clean up

Scoped checks:
- Python root code: `pytest tests/...`
- Dashboard app: `cd site/dashboard && npm run lint && npm run test`
- Deployment and packaging: `make docker-build` or `make docker-build-all`
- `.agent` sync: `python3 scripts/verify_agent_layout.py`

Selection rules:
- Prefer root commands only when the change truly spans multiple components.
- Use the closest service or SDK test entrypoint when the change is localized.
- Read nested `AGENTS.md` files before running service-specific commands.
