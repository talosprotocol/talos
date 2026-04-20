---
name: talos-code-reviewer
description: Use when performing a code review or preparing a PR. This skill enforces Talos project standards, idiomatic patterns, and security best practices.
---

# Talos Code Reviewer

Use this skill to ensure high code quality, consistency, and compliance with
the protocol's core mandates.

Load these first:
- `AGENTS.md`
- `CONTRIBUTING.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. **Architecture:** Verify the change aligns with `talos-contract-first`.
   Check for cross-repo leaks or deep imports.
2. **Security:** Check for secret leakage, unsafe defaults, and authz-sensitive
   holes. Use `talos-capability-audit` if needed.
3. **Idiomaticity:** Ensure Python follows PEP 8 and TS/JS follows the site's
   lint/format rules. Check for consistency with the existing codebase.
4. **Testing:** Verify the change is covered by tests and follows
   `talos-tdd-workflow`. Run `deploy/scripts/run_all_tests.sh --changed`.
5. **Documentation:** Ensure all changed public APIs or CLI flags are documented.

Non-negotiables:
- No deep cross-repo imports.
- No hardcoded secrets or absolute paths.
- No change without tests (negative cases included for security-critical logic).
- No undocumented breaking changes or CLI flags.

Done checklist:
- Code reviewed for architecture, security, and idiomaticity.
- Tests verified and green.
- Documentation parity checked.
- PR description draft includes a clear summary and impact analysis.
- Final review summary lists findings clearly with actionable feedback.
