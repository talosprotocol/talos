# Talos Codex Skills

This directory contains repository-local Codex skills for Talos. Codex scans
`.agent/skills` from the current working directory up to the repository root,
so these skills are available anywhere inside this repo.

Workflow skills:
- `$talos-ops-sweep` for one coordinated Talos analysis pass across CI/build
  triage, UI surface parity, and dirty-worktree or submodule hygiene.
- `$talos-ci-triage` for first-signal CI/build/test triage, owner mapping, and
  smallest local repro selection.
- `$talos-contract-first` for schema, API, and cross-component boundary work.
- `$talos-capability-audit` for authz, capability, identity, and audit changes.
- `$talos-ui-surface-parity` for dashboard shell, API Workbench, and TUI parity
  inventories before cross-surface fixes.
- `$talos-local-stack` for choosing the right local build, test, and runtime
  commands.
- `$talos-parallelize` for dependency-aware task splitting, safe parallel lane
  selection, and lane-to-skill assignment before implementation starts.
- `$talos-sdk-parity` for propagating contract and protocol changes across SDKs
  without local reimplementation drift.
- `$talos-submodule-hygiene` for classifying dirty worktrees, generated
  artifacts, and ignore-rule candidates across submodules.
- `$talos-docs-parity` for keeping docs, examples, and product claims aligned
  with the current implementation.
- `$talos-governance-agent` for supervisor-gated governance-agent and
  tool-orchestration work.
- `$talos-drift-sweep` for anti-drift checks across submodules, boundaries, and
  generated `.agent` content.

Specialist agent skills:
- `$talos-ops-sweeper-agent` for running the combined Talos sweep and routing
  the next lane to the right workflow skill or specialist agent.
- `$talos-ci-failure-manager-agent` for CI/build/log triage that isolates the
  first actionable failure and chooses the smallest repro.
- `$talos-backend-architect-agent` for backend design and implementation work.
- `$talos-api-tester-agent` for security-first API and integration testing.
- `$talos-ui-parity-builder-agent` for cross-surface parity analysis and
  verification across dashboard, API Workbench, and TUI.
- `$talos-infra-maintainer-agent` for deployment, Docker, Helm, and rollback
  oriented tasks.
- `$talos-frontend-developer-agent` for dashboard and Next.js work that must
  stay behind `/api/*` browser boundaries.
- `$talos-ai-engineer-agent` for LLM, tool-policy, eval, and redaction work in
  the Talos ecosystem.
- `$talos-artifact-janitor-agent` for generated-artifact cleanup planning and
  ignore hygiene without reverting intentional source changes.
- `$talos-parallel-orchestrator-agent` for multi-lane task orchestration that
  runs a parallelization pass, assigns specialist skills, and monitors the
  lanes through merge.
- `$talos-deduplication-agent` for repeated logic and copy-paste cleanup that
  consolidates only when it genuinely reduces complexity.
- `$talos-type-consolidation-agent` for duplicated or drifted type definitions
  that need one contract-aware source of truth.
- `$talos-dead-code-removal-agent` for removing confirmed-dead exports,
  functions, files, fixtures, and dependencies after manual verification.
- `$talos-circular-dependencies-agent` for mapping dependency cycles and
  breaking only the ones that hurt correctness, startup, tests, or ownership.
- `$talos-type-strengthening-agent` for replacing weak placeholder types with
  researched strong types while preserving true boundary `unknown`s.
- `$talos-error-handling-cleanup-agent` for removing swallowed errors and
  masking fallbacks while preserving real recovery and reporting boundaries.
- `$talos-deprecated-code-cleanup-agent` for removing obsolete paths and
  low-value AI artifacts without breaking active compatibility.

The workflow skills are configured for implicit use. The specialist agent
skills are narrow role modes; invoke them explicitly or when the task clearly
matches their domain.

Maintenance helpers:
- `python3 scripts/sync_submodule_agents.py` copies the root
  `AGENTS.md` into existing submodule `AGENTS.md` files.
- `python3 scripts/sync_codex_skills.py` mirrors this repo's `.agent/skills`
  into `~/.codex/skills` by default.

Usage examples:
- `docs/guides/codex-skills.md` contains short prompts showing when to invoke
  each Talos skill.
