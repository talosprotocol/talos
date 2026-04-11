# Talos Contract Source Map

Core sources of truth:
- `../../../../contracts/` for schemas, vectors, and generated protocol artifacts.
- `../../../../.agent/planning/program-anchor-index.md` for anti-drift rules.
- `../../../../docs/reference/decision-log.md` for major architecture decisions.
- `../../../../deploy/scripts/check_boundaries.sh` for boundary and duplication
  checks.
- `../../../../scripts/verify_agent_layout.py` when `.agent/` structure is touched.

Common impact zones:
- Gateway and authz: `../../../../services/gateway/`,
  `../../../../services/ai-gateway/`, and
  `../../../../docs/features/authorization/`
- Audit: `../../../../services/audit/` and
  `../../../../docs/features/observability/`
- SDKs: `../../../../sdks/`
- Dashboard and marketing: `../../../../site/`
- Root engine and protocol code: `../../../../src/` and `../../../../core/`

Cross-component completion cues:
- If a field shape changed, inspect docs and examples in addition to runtime
  code.
- If ordering, hashing, or signatures changed, expect vectors or regression
  tests.
- If the change crosses repo boundaries, mention submodule pointer updates in
  the final summary.
