---
description: List of pending features and known placeholders in the dashboard
---

# Pending Dashboard Features

This file tracks features that are partially implemented or planned for future development in the Talos Security Dashboard.

## ✅ Recently Completed (v3.2)

### 1. Denial Taxonomy Chart
- **Location**: `ui/dashboard/src/components/dashboard/DenialTaxonomyChart.tsx`
- **Status**: ✅ Implemented
- **Description**: Pie chart showing breakdown of denial reasons (all 9 types)

### 2. Request Volume (24h) Chart
- **Location**: `ui/dashboard/src/components/dashboard/RequestVolumeChart.tsx`
- **Status**: ✅ Implemented
- **Description**: Stacked area chart showing OK/DENY/ERROR over time

### 3. Demo Traffic Mode Indicator
- **Location**: `ui/dashboard/src/components/dashboard/StatusBanners.tsx`
- **Status**: ✅ Implemented
- **Description**: Shows "LIVE API" and "DEMO TRAFFIC" banners when in demo mode

## 🔶 Partially Implemented

### 4. Export Evidence JSON
- **Location**: `ui/dashboard/src/lib/utils/export.ts`
- **Status**: 🔶 Single-event export only
- **Current**: Exports single event as EvidenceBundle from ProofDrawer
- **Future**: 
  - Bulk export from Audit Explorer with filters
  - Include `cursor_range` and `gateway_snapshot`
  - Add integrity summary with full `by_denial_reason` breakdown

## 🔴 Planned Features (v1.1+)

### 5. Gap Backfill UI
- **Status**: 🔴 Not implemented
- **Description**: "Gap in history" banner when cursor_gap detected
- **Components needed**: Banner component, backfill progress indicator

### 6. Cursor Mismatch Banner
- **Status**: 🔴 Not implemented
- **Description**: UI warning when cursor validation fails
- **Dependencies**: Integrate `validateCursor()` into data flow

### 7. WebSocket Streaming Mode
- **Status**: 🔴 Not implemented
- **Description**: Real-time event streaming via WebSocket
- **Current**: HTTP polling only

### 8. Audit Explorer Page (`/audit`)
- **Status**: 🔴 Not implemented
- **Description**: Flagship audit table with virtualization, filters, bulk export
- **Spec**: v3.2 Section 3B

### 9. Session Intelligence Page (`/sessions`)
- **Status**: 🔴 Not implemented
- **Description**: Session analysis with suspicious score calculation
- **Spec**: v3.2 Section 3C

### 10. Gateway Status Page (`/gateway`)
- **Status**: 🔴 Not implemented
- **Description**: Gateway health, uptime, cache stats
- **Spec**: v3.2 Section 3D

## Related Documentation

- [Implementation Plan v3.2](implementation_plan.md)
- [Run Dashboard](run-dashboard.md)
