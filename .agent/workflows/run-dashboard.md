---
description: How to run the Talos Security Dashboard
---

# How to Run the Dashboard

This workflow describes how to bring up the Talos Security Dashboard and its dependencies.

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm

## Quick Start (Recommended)

Run the unified start script:

```bash
./start.sh
```
// turbo
This will:
1. **Kill existing processes** (uvicorn, next dev, traffic_gen.py)
2. Check dependencies
3. Install Python packages (if missing)
4. Build the UI
5. Start the Backend API (port 8000)
6. Start the Frontend (port 3000)
7. Start the Traffic Generator (10% denial rate for demo)

## Dashboard Features (v3.2)

### Overview Page (`/`)
- **KPI Grid**: Total Requests, Auth Success Rate, Denial Rate, Latency
- **Denial Taxonomy Chart**: Pie chart showing breakdown by denial reason
- **Request Volume Chart**: Stacked area chart (OK/DENY/ERROR over 24h)
- **Activity Feed**: Live stream of audit events with cursor pagination
- **Status Banners**: Mode indicator (LIVE API / DEMO TRAFFIC), Redaction policy

### ProofDrawer
- Click any event to open audit proof details
- Shows integrity state, cryptographic bindings, session context
- **Export Evidence JSON**: Download v3.2 compliant evidence bundle

## Manual Startup

If you prefer to run components individually:

1. **Install Dependencies**
   ```bash
   make install
   ```
   // turbo

2. **Run Backend**
   ```bash
   python3 -m uvicorn src.api.server:app --reload --port 8000
   ```

3. **Run Frontend**
   ```bash
   cd ui/dashboard
   npm run dev
   ```

4. **Generate Traffic**
   ```bash
   python3 scripts/traffic_gen.py
   ```

## Pending Features (v1.1+)

See `/pending-features` workflow for the full list:
- Gap Backfill UI with "Gap in history" banner
- Cursor Mismatch Banner
- WebSocket Streaming Mode
- Audit Explorer Page (`/audit`)
- Session Intelligence Page (`/sessions`)
- Gateway Status Page (`/gateway`)

