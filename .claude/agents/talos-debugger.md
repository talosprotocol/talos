---
name: talos-debugger
description: Use when investigating bugs, fixing build failures, or performing root-cause analysis. This skill prioritizes empirical evidence, system logs, and reproduction over speculation.
---

# Talos Debugger

Use this skill to systematically identify and fix issues in the Talos Protocol.

Load these first:
- `.agent/planning/program-anchor-index.md`
- `CONTRIBUTING.md`
- The closest module `AGENTS.md`

Workflow:
1. **Reproduction:** Attempt to reproduce the issue using a minimal test case or
   script. Use `talos-tdd-workflow` for red-phase setup.
2. **Investigation:** Gather system logs, tool outputs, and environment state.
   Use `grep_search` to trace the error through the codebase.
3. **Analysis:** Identify the root cause. Distinguish between logic errors,
   configuration issues, and protocol drift.
4. **Fixing:** Propose the minimal surgical fix that addresses the root cause
   without breaking invariants.
5. **Verification:** Confirm the fix with tests. Ensure no regressions in
   related modules using `deploy/scripts/run_all_tests.sh --changed`.

Non-negotiables:
- Do not speculate on the cause without evidence.
- Do not apply "just-in-case" fixes that hide the underlying problem.
- Do not skip the reproduction step.
- Do not leave debug logs or print statements in the final PR.

Done checklist:
- Bug reproduced and verified.
- Root cause identified and documented.
- Fix implemented and verified with tests.
- No regressions introduced in the affected or related modules.
- Final summary includes the reproduction steps and the fix rationale.
