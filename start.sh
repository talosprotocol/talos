#!/bin/bash
set -e

# Talos Protocol - Quick Start Script

echo "=================================="
echo "   Talos Protocol - Quick Start   "
echo "=================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found."
    exit 1
fi

# Check for Node/NPM
if ! command -v npm &> /dev/null; then
    echo "Error: npm could not be found."
    exit 1
fi

# Kill any existing running instances
echo "[1/4] Cleaning up existing processes..."

# Kill uvicorn/backend processes
pkill -f "uvicorn src.api.server" 2>/dev/null || true
pkill -f "python3 -m uvicorn" 2>/dev/null || true

# Kill frontend dev server
pkill -f "next dev" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true

# Kill traffic generator
pkill -f "traffic_gen.py" 2>/dev/null || true

# Give processes time to terminate
sleep 1

echo "    Previous processes terminated."

echo "[2/4] Checking dependencies..."
# We explicitly call install-python to ensure fastapi/uvicorn are present
# relying on the Makefile 'install' target which handles both
make install

echo "[3/4] Building UI (skipping for dev speed, run 'make build-ui' manually if needed)..."
# Optional: make build-ui

echo "[4/4] Launching Development Stack..."
echo "      - Backend: http://localhost:8000"
echo "      - Dashboard: http://localhost:3000"
echo "      - Traffic Gen: Active"
echo "Press Ctrl+C to stop all services."
echo ""

make dev
