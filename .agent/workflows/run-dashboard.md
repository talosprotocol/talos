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
7. Start the Traffic Generator

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

## Known Placeholders

The Overview page (`/`) has two placeholder chart panels that are NOT yet implemented:
- "Chart: Denial Taxonomy" - Pie chart placeholder
- "Chart: Request Volume (24h)" - Time series placeholder

See `/pending-features` workflow for implementation guidance or removal instructions.

