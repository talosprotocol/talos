# Talos Codex Skills

This directory contains repository-local Codex skills for Talos. Codex scans
`.agents/skills` from the current working directory up to the repository root,
so these skills are available anywhere inside this repo.

Workflow skills:
- `$talos-contract-first` for schema, API, and cross-component boundary work.
- `$talos-capability-audit` for authz, capability, identity, and audit changes.
- `$talos-local-stack` for choosing the right local build, test, and runtime
  commands.
- `$talos-parallelize` for dependency-aware task splitting, safe parallel lane
  selection, and lane-to-skill assignment before implementation starts.
- `$talos-sdk-parity` for propagating contract and protocol changes across SDKs
  without local reimplementation drift.
- `$talos-docs-parity` for keeping docs, examples, and product claims aligned
  with the current implementation.
- `$talos-governance-agent` for supervisor-gated governance-agent and
  tool-orchestration work.
- `$talos-drift-sweep` for anti-drift checks across submodules, boundaries, and
  generated `.agent` content.

Specialist agent skills:
- `$talos-backend-architect-agent` for backend design and implementation work.
- `$talos-api-tester-agent` for security-first API and integration testing.
- `$talos-infra-maintainer-agent` for deployment, Docker, Helm, and rollback
  oriented tasks.
- `$talos-frontend-developer-agent` for dashboard and Next.js work that must
  stay behind `/api/*` browser boundaries.
- `$talos-ai-engineer-agent` for LLM, tool-policy, eval, and redaction work in
  the Talos ecosystem.
- `$talos-parallel-orchestrator-agent` for multi-lane task orchestration that
  runs a parallelization pass, assigns specialist skills, and monitors the
  lanes through merge.

The workflow skills are configured for implicit use. The specialist agent
skills are explicit-only so they do not hijack unrelated tasks.

Maintenance helpers:
- `python3 scripts/sync_submodule_agents.py` copies the root
  `AGENTS.md` into existing submodule `AGENTS.md` files.
- `python3 scripts/sync_codex_skills.py` mirrors this repo's `.agents/skills`
  into `~/.codex/skills` by default.

Usage examples:
- `docs/guides/codex-skills.md` contains short prompts showing when to invoke
  each Talos skill.
