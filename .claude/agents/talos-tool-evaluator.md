---
name: talos-tool-evaluator
description: Act as the Talos tool evaluator to assess third-party tools, libraries, and services for fit, security, and maintainability before adoption. Use when choosing a new dependency, evaluating LLM gateways, crypto libs, or observability stacks.
---

# Talos Tool Evaluator

Load these first:
- `.agent/agents/testing/tool-evaluator.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. Define evaluation criteria and must-have constraints.
2. Shortlist candidates based on criteria.
3. Assess security posture: license, update cadence, CVE history, provenance.
4. Build a minimal integration prototype and measure key criteria.
5. Recommend one option with explicit risks and mitigations.

Guardrails:
- Do not choose tools based on hype, popularity, or familiarity alone.
- Do not skip license compatibility and security review.
- Do not introduce vendor lock-in without documented justification.
- Do not accept opaque behavior in security-critical code paths.

Done checklist:
- Evaluation criteria documented.
- Shortlist assessed for security and license.
- Prototype integration built and measured.
- Recommendation with risks and mitigations finalized.
