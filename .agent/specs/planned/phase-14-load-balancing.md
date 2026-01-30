---
description: Phase 14 Global Load Balancing - LOCKED SPEC
---

# Phase 14: Global Load Balancing (LOCKED)

## 1. Goal

Route agent traffic to the optimal region based on proximity and health.

## 2. Technical Invariants

- **Geo-Routing**: Use client IP to identify nearest region.
- **Health-Aware**: Regions reported as unhealthy via `/health/ready` MUST be removed from rotation.

## 3. Implementation Details

- **GSLB Policy**: Latency-based or Geographic.
- **Monitoring**: Integrated with Prometheus/ServiceMonitors.

## 4. Verification

- `tests/test_gslb.py` must pass with >95% accuracy in routing logic.
