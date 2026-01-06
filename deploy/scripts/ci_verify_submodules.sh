#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# CI: Verify Submodules
# =============================================================================
# Ensures required submodules are present and initialized in strict mode.
# Run in CI to enforce submodule integrity.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

# Source common helpers for COMMON_REPOS
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

# Use the canonical list from common.sh
REPOS=("${COMMON_REPOS[@]}")

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
