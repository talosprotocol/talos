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

### 4. Export Evidence JSON (Bulk)

- **Location**: `ui/dashboard/src/lib/utils/export.ts`
- **Status**: ✅ Implemented
- **Features**:
  - Bulk export from Audit Explorer with filters
  - Includes `cursor_range` and `gateway_snapshot`
  - Integrity summary with `by_denial_reason` breakdown
  - Progress indicator and outcome preview in dialog

## 🔴 Planned Features (v1.1+)

### 5. Gap Backfill UI

- **Status**: ✅ Implemented
- **Description**: "Gap in history" banner when cursor_gap detected
- **Components**: `deploy/repos/talos-dashboard/src/components/dashboard/GapBanner.tsx`

### 6. Cursor Mismatch Banner

- **Status**: ✅ Implemented
- **Description**: UI warning when cursor validation fails
- **Components**: `deploy/repos/talos-dashboard/src/components/dashboard/CursorMismatchBanner.tsx`

### 7. WebSocket Streaming Mode

- **Status**: ✅ Implemented
- **Description**: Real-time event streaming via WebSocket
- **Usage**: Set `NEXT_PUBLIC_TALOS_DATA_MODE=WS` to enable
- **Components**: `deploy/repos/talos-dashboard/src/lib/data/WsClient.ts`, `deploy/repos/talos-dashboard/src/lib/data/WsDataSource.ts`

### 8. Audit Explorer Page (`/audit`)

- **Status**: ✅ Implemented
- **Description**: Flagship audit table with virtualization, filters, bulk export
- **Spec**: v3.2 Section 3B

### 9. Session Intelligence Page (`/sessions`)

- **Status**: ✅ Implemented
- **Description**: Session analysis with suspicious score calculation
- **Spec**: v3.2 Section 3C

### 10. Gateway Status Page (`/gateway`)

- **Status**: ✅ Implemented
- **Description**: Gateway health, uptime, cache stats
- **Spec**: v3.2 Section 3D

## Related Documentation

- [Implementation Plan v3.2](implementation_plan.md)
- [Run Dashboard](run-dashboard.md)
