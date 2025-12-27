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
1. Check dependencies
2. Install Python packages (if missing)
3. Build the UI
4. Start the Backend API (port 8000)
5. Start the Frontend (port 3000)
6. Start the Traffic Generator

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
