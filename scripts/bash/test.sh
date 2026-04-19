#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Root Project Test Script
# =============================================================================

echo "Testing talos (root project)..."

# Lint checks
echo "Running ruff check..."
ruff check src tests api-testing/pytest

echo "Running ruff format check..."
if ! ruff format --check src tests api-testing/pytest 2>/dev/null; then
	echo "  ⚠ Some files need formatting (run: ruff format src tests api-testing/pytest)"
fi

# Unit tests
echo "Running pytest..."
pytest tests/ api-testing/pytest --maxfail=1 -q

echo "talos (root) tests passed."
