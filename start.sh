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

echo "[1/3] Checking dependencies..."
# We explicitly call install-python to ensure fastapi/uvicorn are present
# relying on the Makefile 'install' target which handles both
make install

echo "[2/3] Building UI (skipping for dev speed, run 'make build-ui' manually if needed)..."
# Optional: make build-ui

echo "[3/3] Launching Development Stack..."
echo "      - Backend: http://localhost:8000"
echo "      - Dashboard: http://localhost:3000"
echo "      - Traffic Gen: Active"
echo "Press Ctrl+C to stop all services."
echo ""

make dev
