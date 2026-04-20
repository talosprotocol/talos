---
name: talos-tdd-workflow
description: Use when applying Test-Driven Development (TDD) to any Talos code change. Prioritize empirical failure, surgical fixes, and 80%+ test coverage. This is a high-rigor engineering workflow for ensuring behavioral correctness.
---

# Talos TDD Workflow

Use this skill for any feature addition, bug fix, or refactoring task where
reliability and correctness are paramount.

Load these first:
- `.agent/planning/program-anchor-index.md`
- The closest module `AGENTS.md`
- `CONTRIBUTING.md`

Workflow:
1. **Red Phase (Reproduction):** Write a failing test case that captures the
   bug or describes the new feature. Use existing test patterns in the module.
   Verify the test fails with a clear, expected error.
2. **Green Phase (Implementation):** Write the minimal amount of code needed
   to make the test pass. Follow `talos-contract-first` if boundaries change.
3. **Refactor Phase (Optimization):** Clean up the implementation while
   ensuring tests remain green. Adhere to Python/TS/Rust idiomatic patterns.
4. **Coverage Check:** Ensure at least 80% coverage for the new or modified logic.
   Run `deploy/scripts/run_all_tests.sh --changed` to verify no regressions.

Non-negotiables:
- Do not skip the Red phase. If you cannot reproduce the failure, you do not
  understand the problem yet.
- Do not use wide mocks for security or protocol-critical logic; prefer
  narrow, focused tests that exercise real enforcement paths.
- Do not leave unused or commented-out code after the Refactor phase.
- Do not claim completion until the test suite is green and coverage is met.

Done checklist:
- Failing test case committed/verified.
- Implementation passes all tests in the affected module.
- No regressions in related modules (via `--changed` runner).
- Coverage target met for the changed surface.
- Final summary includes the exact test command and outcome.
