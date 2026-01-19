#!/bin/bash
set -euo pipefail

echo "Cleaning talos-sdk-py..."
# Python artifacts
rm -rf *.egg-info build dist .venv venv .pytest_cache .ruff_cache conformance.xml
# Coverage & reports
rm -f .coverage .coverage.* coverage.xml junit.xml 2>/dev/null || true
rm -rf htmlcov coverage 2>/dev/null || true
# Cache files
rm -rf .mypy_cache .pytype 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "✓ talos-sdk-py cleaned"
