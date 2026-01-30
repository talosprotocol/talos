---
description: Phase 12 Multi-Region Architecture - LOCKED SPEC
---

# Phase 12: Multi-Region Architecture (LOCKED)

## 1. Goal

Implement read/write database splitting with circuit-breaker failover to support geographic scaling and high availability.

## 2. Technical Invariants

- **Read/Write Separation**: All state-modifying requests (POST/PATCH/DELETE) MUST use the primary DB. Non-critical reads MAY use replicas.
- **Fail-Open Reads**: If a replica is unreachable, the gateway MUST fallback to the primary DB unless `READ_FALLBACK_ENABLED=false`.
- **Circuit Breaker**:
  - Threshold: 3 consecutive failures.
  - Duration: 30 seconds.
  - Fallback: Primary DB.

## 3. Implementation Details

- **SQL Level**: Use `SET TRANSACTION READ ONLY` for replica sessions.
- **Response Headers**:
  - `X-Talos-DB-Role`: `primary` | `replica`
  - `X-Talos-Read-Fallback`: `0` | `1`

## 4. Verification

- `verify_multi_region.py` must pass with `<5.0s` replication lag.
