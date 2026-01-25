---
description: Phase 13 Secrets Rotation Automation - LOCKED SPEC
---

# Phase 13: Secrets Rotation Automation (LOCKED)

## 1. Goal

Ensure zero-downtime rotation of cryptographic keys and service secrets.

## 2. Technical Invariants

- **Atomic Rotation**: Secrets MUST be updated within a transaction.
- **Concurrency Control**: Use Postgres advisory locks to prevent race conditions between workers.
- **Multi-KEK Support**: `MultiKekProvider` MUST be able to decrypt envelopes encrypted with the previous N KEK versions during the rotation window.

## 3. Implementation Details

- **Worker**: Background loop with configurable interval.
- **Fail-Closed**: If a new secret cannot be successfully encrypted/stored, the old version MUST remain active.

## 4. Verification

- Manual verification via `GET /admin/v1/secrets/rotation/status`.
