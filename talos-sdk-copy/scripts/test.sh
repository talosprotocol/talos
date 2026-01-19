# =============================================================================
# talos-sdk-py Test Script
# =============================================================================
set -euo pipefail

log() { printf '%s\n' "$*"; }
info() { printf 'ℹ️  %s\n' "$*"; }

info "Testing talos-sdk-py..."

info "Installing package..."
pip install -e ".[dev]" -q 2>/dev/null || pip install -e . -q

info "Running ruff check..."
ruff check src tests 2>/dev/null || ruff check talos_sdk tests 2>/dev/null || true

info "Running ruff format check..."
ruff format --check src tests 2>/dev/null || ruff format --check talos_sdk tests 2>/dev/null || true

info "Running pytest..."
pytest tests/ --maxfail=1 -q

log "✓ talos-sdk-py tests passed."
