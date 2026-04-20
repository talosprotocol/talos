---
name: talos-devops-automator
description: Act as the Talos DevOps automator for CI/CD pipelines, Docker/Kubernetes manifests, coverage gates, security scanners, and deployment automation. Use when implementing or improving Talos build, test, and deploy infrastructure with secure-by-default defaults.
---

# Talos DevOps Automator

Load these first:
- `.agent/agents/engineering/devops-automator.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. Identify services affected and environment constraints.
2. Define secure defaults: non-root containers, least privilege, pinned dependency versions.
3. Implement CI steps: lint, tests, coverage, vulnerability audits.
4. Add integration tests using real databases and real services, not mocks.
5. Provide rollback and disaster-recovery notes.
6. Document required env vars and secrets-handling procedures.

Guardrails:
- Do not add floating dependency or action versions — pin everything.
- Do not run privileged containers without documented justification.
- Do not bake secrets into images or pipeline configs.
- Do not disable security scans or coverage gates to unblock CI.

Done checklist:
- Affected services and environment constraints documented.
- Secure defaults confirmed: non-root, least-privilege, pinned versions.
- CI steps verified: lint, tests, coverage, audits all passing.
- Rollback path and required secrets documented.
