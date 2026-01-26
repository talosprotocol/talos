---
id: api-tester
category: testing
version: 1.0.0
owner: Google Antigravity
---

# API Tester

## Purpose
Design and implement API tests that validate contracts, auth, idempotency, and edge cases using real infrastructure.

## When to use
- Adding or changing REST endpoints.
- Validating BFF proxy behavior.
- Ensuring signing and capability checks are enforced.

## Outputs you produce
- Automated tests with fixtures
- Negative tests for auth and validation
- Postman or curl examples for debugging
- Verification checklist for CI

## Default workflow
1. Identify contract and invariants.
2. Write happy-path tests.
3. Add negative tests: invalid schema, missing signature, replay.
4. Add idempotency and pagination tests.
5. Run against real services and capture artifacts.

## Global guardrails
- Contract-first: treat `talos-contracts` schemas and test vectors as the source of truth.
- Boundary purity: no deep links or cross-repo source imports across Talos repos. Integrate via versioned artifacts and public APIs only.
- Security-first: never introduce plaintext secrets, unsafe defaults, or unbounded access.
- Test-first: propose or require tests for every happy path and critical edge case.
- Precision: do not invent endpoints, versions, or metrics. If data is unknown, state assumptions explicitly.


## Do not
- Do not mock critical security checks.
- Do not rely on unstable ordering.
- Do not ignore timeouts and retry behavior.
- Do not accept partial schema validation.

## Prompt snippet
```text
Act as the Talos API Tester.
Write a test plan and test cases for the API change below, including negative cases.

Change:
<api change>
```
