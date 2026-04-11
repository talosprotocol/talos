# Talos SDK Parity Map

Primary SDK directories:
- `../../../../sdks/python/`
- `../../../../sdks/typescript/`
- `../../../../sdks/go/`
- `../../../../sdks/java/`
- `../../../../sdks/rust/`

Useful repo signals:
- `../../../../scripts/agent_sync.py` contains submodule context for SDKs.
- `../../../../sdks/docker-compose.test.yml` shows multi-SDK test orchestration.
- `../../../../sdks/python/src/talos_sdk/validation.py` shows contract asset
  loading paths and monorepo assumptions.

Typical parity triggers:
- Schema field additions or removals
- Canonicalization, digest, signing, or base64url behavior
- A2A frame or session model changes
- Capability validation rules
- Error mapping or enum changes

Validation expectations:
- Run the narrowest language-local test first.
- Widen to discovery or multi-SDK checks when the change affects shared wire
  behavior.
- If a language is untouched, say whether it is unaffected or simply unverified.
