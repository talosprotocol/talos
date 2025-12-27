---
description: List of pending features and known placeholders in the dashboard
---

# Pending Dashboard Features

This file tracks features that are placeholders or not yet implemented in the Talos Security Dashboard.

## Placeholder Components (Not in Implementation Plan v1)

### 1. Denial Taxonomy Chart (`/` Overview Page)
- **Location**: `ui/dashboard/src/app/page.tsx` line 61-63
- **Status**: 🔴 Placeholder only
- **Description**: Empty panel showing "Chart: Denial Taxonomy"
- **Implementation Suggestion**: 
  - Pie chart showing breakdown by `denial_reason`
  - Data source: Aggregate `AuditEvent` where `outcome=DENY` grouped by `denial_reason`
  - Use Recharts (already in stack)

### 2. Request Volume (24h) Chart (`/` Overview Page)
- **Location**: `ui/dashboard/src/app/page.tsx` line 64-66
- **Status**: 🔴 Placeholder only
- **Description**: Empty panel showing "Chart: Request Volume (24h)"
- **Implementation Suggestion**:
  - Line/area chart showing requests over time
  - Data source: Time-series aggregation of `AuditEvent` by hour
  - Use Recharts with smooth curves

## Considerations

### Option A: Implement Charts
Add these as v1.1 features:
1. Create `DenialTaxonomyChart.tsx` component
2. Create `RequestVolumeChart.tsx` component
3. Add aggregation endpoints to backend API

### Option B: Remove Placeholders
If charts are out of scope for v1:
1. Remove the placeholder panels
2. Adjust grid layout to be single-column

## Related Implementation Plan References

The current [implementation_plan.md](file:///Users/nileshchakraborty/.gemini/antigravity/brain/dcabdbe3-9440-401c-90bc-8876af979299/implementation_plan.md) specifies:
- **KPIs** (Requests, Auth Success %, Denial Rate, Latency) ✅ Implemented
- **Stream/ActivityFeed** ✅ Implemented
- **Evidence Bundle** has `integrity_summary.by_denial_reason` which could power Denial Taxonomy

Charts were NOT explicitly specified in the v1 implementation plan.
