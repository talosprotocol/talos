# Talos Drift Checks

Existing checks and helpers:
- `../../../../deploy/scripts/check_boundaries.sh`
- `../../../../scripts/verify_agent_layout.py`
- `../../../../scripts/agent_sync.py`
- `../../../../deploy/scripts/run_all_tests.sh`

Signals worth tracing:
- Duplicate cursor, canonicalization, or base64url logic outside contracts
- Browser code bypassing dashboard `/api/*` boundaries
- Stale `.agent` copies in submodules
- Docs or examples that no longer match the repo layout
- Unexplained submodule pointer changes

Sweep strategy:
- Start with the narrowest relevant check.
- Use `rg` to trace every matching duplicate before fixing.
- If a generated artifact is stale, repair via the owning sync path rather than
  hand-editing copies.
