---
name: talos-doctor
description: Use when setting up a new environment or troubleshooting mysterious local failures. This skill performs a comprehensive health check of the Talos Protocol stack, including dependencies, tools, and service connectivity.
---

# Talos Doctor

Use this skill to diagnose and heal your local Talos development environment.

Load these first:
- `../../../CONTRIBUTING.md`
- `../../../Makefile`
- `../planning/program-anchor-index.md`

Workflow:
1. **Tool Check:** Verify that essential tools are installed and available
   (e.g., `docker`, `docker-compose`, `npm`, `python3`, `openssl`, `grep`).
2. **Dependency Check:** Check for common vulnerability drift and missing
   submodule initialization. Run `make pull` to synchronize.
3. **Secret Check:** Verify that `.env.local` exists and contains the
   required secrets. Run `make secrets` if missing.
4. **Service Check:** Test connectivity to local services if they are
   running. Check for port conflicts.
5. **Build Check:** Run a minimal build validation (`make build`).

Non-negotiables:
- Do not ignore missing tool warnings.
- Do not proceed with implementation if the "doctor" report shows critical
  infrastructure failures.
- Do not modify system-wide configuration without explicit user confirmation.

Done checklist:
- Local tools and dependencies verified.
- Secrets and environment configuration checked.
- Service connectivity and build health reported.
- Final summary provides actionable steps to fix any identified issues.
