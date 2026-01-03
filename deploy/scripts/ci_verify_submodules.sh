#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# CI: Verify Submodules
# =============================================================================
# Ensures required submodules are present and initialized in strict mode.
# Run in CI to enforce submodule integrity.
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

REPOS=(
  talos-contracts
  talos-core-rs
  talos-sdk-ts
  talos-dashboard
  talos-mcp-connector
  talos-sdk-py
  talos-gateway
  talos-audit-service
)

missing=()

# Ensure .gitmodules exists and paths are declared
if [[ ! -f .gitmodules ]]; then
  echo "✖ .gitmodules missing"
  exit 1
fi

for r in "${REPOS[@]}"; do
  path="deploy/repos/$r"
  if ! git config -f .gitmodules --get-regexp "submodule\..*\.path" | grep -q " $path$"; then
    echo "✖ Submodule path not declared in .gitmodules: $path"
    missing+=("$r")
    continue
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "✖ Missing submodule declarations: ${missing[*]}"
  exit 1
fi

# Initialize (strict mode)
export TALOS_SETUP_MODE=strict
./deploy/scripts/setup.sh

# Verify each submodule dir has a checked-out HEAD
for r in "${REPOS[@]}"; do
  path="deploy/repos/$r"
  if [[ ! -d "$path/.git" ]] && ! git submodule status "$path" >/dev/null 2>&1; then
    echo "✖ Submodule not initialized: $r ($path)"
    exit 1
  fi
done

echo "✓ Submodules present and initialized"
