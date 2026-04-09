# Talos Governance Agent Map

Primary planning and workflow docs:
- `../../../../.agent/planning/tga-plan.md`
- `../../../../.agent/workflows/development/tga-workflow.md`
- `../../../../docs/business/agent-lifecycle.md`

Likely implementation surfaces:
- `../../../../services/governance-agent/`
- `../../../../services/ai-gateway/`
- `../../../../services/gateway/`
- `../../../../contracts/`

Locked TGA principles to preserve:
- No direct tool calls outside Talos-protected MCP paths
- Contract-first schemas and vectors
- Supervisor authority for nontrivial writes
- Idempotent, deterministic execution artifacts
- Reconstructable audit chain from proposal through effect

Review prompts:
- Which risk tier is affected?
- Where is the minted capability created, checked, and logged?
- What proves a write cannot bypass supervisor approval?
- What test proves effect identifiers remain deterministic?
