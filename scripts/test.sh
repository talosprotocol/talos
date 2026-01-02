#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Root Project Test Script
# =============================================================================

echo "Testing talos (root project)..."

# Lint checks
echo "Running ruff check..."
ruff check src tests

echo "Running ruff format check..."
if ! ruff format --check src tests 2>/dev/null; then
  echo "  ⚠ Some files need formatting (run: ruff format src tests)"
fi

# Unit tests
echo "Running pytest..."
pytest tests/ --maxfail=1 -q

echo "talos (root) tests passed."
