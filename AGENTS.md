# Repository Guidelines

This guide applies to the root repository and all checked-out submodules. If a submodule ships its own `CONTRIBUTING.md` or `AGENTS.md`, follow those in addition.

## Project Structure & Module Organization
Talos is a multi-component monorepo with submodules and shared tooling. `contracts/` is the schema and test-vector source of truth; other components consume its artifacts. Key locations:
- `src/` and `core/`: Python protocol engine, CLI, and services.
- `services/`: runtime services (gateway, audit, connectors).
- `sdks/`: language SDKs (Go/Java/Rust/Python/TypeScript).
- `site/dashboard` and `site/marketing`: Next.js UI apps.
- `deploy/`: setup scripts, Helm/Kubernetes manifests, and CI helpers.
- `tests/`: root pytest suite; component-specific tests live with each module.
- `docs/`, `examples/`, `proto/`, `tools/`: supporting docs and tooling.

## Build, Test, and Development Commands
- `./deploy/scripts/setup.sh`: initialize submodules and dev hooks.
- `make build`: runs the pre-commit validation pipeline.
- `make dev` or `./deploy/scripts/start_all.sh`: start the full local stack.
- `./start.sh`: quick-start gateway + dashboard for local demos.
- `make test` or `./run_all_tests.sh --ci --changed`: run the discovery-based test suite.
- `./run_all_tests.sh --full`: unit + integration + coverage for all repos.
- `make docker-build` / `make docker-build-all`: build service and SDK images.

## Coding Style & Naming Conventions
- Python: 4-space indentation, type hints where practical, and PEP 8 layout.
- JavaScript/TypeScript (UI): use `npm run lint` and `npm run format` in `site/dashboard` (ESLint + Prettier).
- Tests follow `test_*.py` naming in `tests/` and module-specific directories.
- Avoid hardcoded absolute paths; the pre-commit hook blocks them.

## Testing Guidelines
- Python tests use `pytest` (configured in `pyproject.toml`).
- `run_all_tests.sh` discovers `.agent/test_manifest.yml` files and enforces coverage in `--ci`/`--full` modes.
- Dashboard tests run via `npm run test` (Vitest). SDKs use their local `make test` or `scripts/test.sh`.

## Commit & Pull Request Guidelines
- Commit messages generally follow Conventional Commits style: `feat:`, `fix:`, `chore:`, `docs:` with optional scopes (e.g., `feat(perf): ...`).
- Sign off commits for DCO compliance: `git commit -s`.
- PRs should include a clear summary, tests run, and linked issues. Add screenshots for UI changes and call out submodule pointer updates.

## Security & Configuration Tips
- Use `.env.example` and `.env.local` for local settings; never commit secrets.
- Report vulnerabilities privately as described in `SECURITY.md`.
