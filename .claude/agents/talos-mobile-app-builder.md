---
name: talos-mobile-app-builder
description: Act as the Talos mobile app builder for Flutter or native screens, state management, offline-safe data handling, and secure integration with the Talos Gateway or BFF APIs. Use when building mobile features that require encrypted local storage, biometric auth, or typed Talos API clients.
---

# Talos Mobile App Builder

Load these first:
- `.agent/agents/engineering/mobile-app-builder.md`
- `.agent/planning/program-anchor-index.md`

Workflow:
1. Define user flows and offline expectations before coding.
2. Identify Talos API surfaces and required auth headers.
3. Implement secure key storage and encryption at rest.
4. Build UI with clear loading and error states.
5. Add unit and widget tests plus manual QA steps.
6. Document privacy considerations and data-deletion paths.

Guardrails:
- Do not store secrets or tokens in plaintext preferences or logs.
- Do not disable TLS verification.
- Do not implement custom crypto primitives.
- Do not collect or log PII without explicit consent and a documented retention policy.

Done checklist:
- User flows and offline contract defined.
- Secure storage and encryption at rest confirmed.
- Loading and error states implemented.
- Privacy considerations and data-wipe paths documented.
