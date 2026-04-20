---
name: talos-local-stack
description: Use when starting, stopping, debugging, building, or testing the Talos local stack, or when choosing the smallest correct command across services, SDKs, dashboards, Docker, and the discovery-based test runner. Prefer the narrowest command that covers the changed surface.
---

# Talos Local Stack

Use this skill to pick the right local command and verification path for Talos.

Load:
- `.agent/skills/talos-local-stack/references/commands.md`
- The nearest module `AGENTS.md`

Workflow:
1. Scope the task by path and runtime first. Distinguish root Python code,
   service code, SDKs, dashboard apps, docs-only changes, and infra changes.
2. Prefer the smallest command that covers the changed surface before jumping to
   the full stack.
3. If a runtime issue exists, capture the failing command, logs, and health
   endpoint before widening the investigation.
4. If the task crosses services or submodules, widen validation intentionally
   and call out what was and was not verified.

Guardrails:
- Do not default to `make dev` or the full test suite when a narrower command is
  enough.
- Do not ignore module-specific instructions in nested `AGENTS.md` files.
- Do not treat submodule pointer changes as ordinary file edits; mention them
  explicitly.

Done checklist:
- The chosen command matches the touched area.
- Verification scope is stated clearly.
- Failures include the command, service, and artifact that failed.
