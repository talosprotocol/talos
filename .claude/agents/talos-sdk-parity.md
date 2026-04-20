---
name: talos-sdk-parity
description: Use when a Talos contract, protocol primitive, frame shape, digest rule, capability field, or validation behavior must be propagated across one or more SDKs. Preserve contract ownership, avoid local reimplementation drift, update language-specific conformance tests, and call out which SDKs were intentionally left unchanged.
---

# Talos SDK Parity

Use this skill when a change must remain consistent across multiple language
SDKs.

Load only what the task needs:
- `.agent/skills/talos-sdk-parity/references/sdk-map.md`
- `.agent/planning/program-anchor-index.md`
- The closest SDK `AGENTS.md` or `CLAUDE.md`

Workflow:
1. Identify the owning contract, vector, or protocol rule first.
2. Map impacted SDKs before editing. Python and TypeScript are the most likely
   first-order consumers, but Go, Java, and Rust may also need parity updates.
3. Prefer consuming published contract artifacts or shared generated outputs over
   re-implementing canonical logic in each SDK.
4. For each touched SDK, update the smallest test or conformance path that
   proves parity.
5. State explicitly which SDKs were updated, which were reviewed only, and which
   still need follow-up.

Guardrails:
- Do not silently fork behavior between SDKs on hashed, signed, or validated
  payloads.
- Do not bury a protocol change inside one SDK without tracing the others.
- Do not claim multi-SDK parity without naming the validated languages.

Done checklist:
- Source-of-truth artifact identified.
- Impacted SDKs traced.
- Per-language validation updated or justified.
- Final summary names parity status by SDK.
