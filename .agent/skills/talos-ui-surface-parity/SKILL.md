---
name: talos-ui-surface-parity
description: Use when dashboard shell pages, the dashboard API Workbench, and `tools/talos-tui` need a parity pass against the same runtime capabilities. Inventory the surfaces first, trace each action to its owner, then report confirmed gaps, intentional differences, and scoped verification.
---

# Talos UI Surface Parity

Use this skill for dashboard, API-console, and TUI parity analysis.

Load:
- `../planning/program-anchor-index.md`
- `../talos-local-stack/references/commands.md`
- The nearest surface `AGENTS.md`

Workflow:
1. Build a surface inventory before comparing behavior. Start with dashboard
   shell pages, `site/dashboard/src/lib/api/workbench.ts`, and
   `tools/talos-tui/python/src/talos_tui/app.py`.
2. Trace each visible action back to the owning same-origin route, adapter, or
   service handler. Keep browser work behind dashboard `/api/*` routes and TUI
   work behind the TUI adapter and token path.
3. Classify each finding as `aligned`, `missing`, `intentionally different`,
   or `unverified`. Do not call it drift until both surfaces and the owner path
   were inspected.
4. Use `scripts/build_surface_inventory.py --format markdown` when a fast
   baseline helps. Treat the script as an inventory seed, not as ground truth.
5. End with a compact parity matrix that names the two surfaces, owner path,
   status, and the smallest follow-up command or test.

Guardrails:
- Do not infer parity from labels alone; verify route ownership and auth
  boundaries.
- Do not propose parity fixes that bypass dashboard `/api/*` routes or the TUI
  session and token flow.
- Do not mix roadmap ideas with confirmed current-state gaps.

Done checklist:
- Dashboard shell, API Workbench, and TUI entrypoints relevant to the task were
  inventoried.
- Every reported gap names both surfaces and the owning path.
- Intentional differences and unknowns are labeled explicitly.
- Verification is scoped to the touched surface.
