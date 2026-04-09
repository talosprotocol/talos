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

python3 "$ROOT_DIR/scripts/python/check_submodules_topology.py"
mapfile -t REPOS < <(python3 "$ROOT_DIR/deploy/submodules.py" --field name)

missing=()

# Ensure .gitmodules exists and paths are declared
if [[ ! -f .gitmodules ]]; then
  echo "✖ .gitmodules missing"
  exit 1
fi

for r in "${REPOS[@]}"; do
  # Look up new_path from submodules.json using python helper
  path=$(python3 "$ROOT_DIR/deploy/submodules.py" --name "$r" --field new_path)
  
  if [[ -z "$path" ]]; then
    echo "✖ Submodule $r not found in manifest"
    missing+=("$r")
    continue
  fi

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
./deploy/scripts/setup.sh --strict

# Verify each submodule dir has a checked-out HEAD
for r in "${REPOS[@]}"; do
  path=$(python3 "$ROOT_DIR/deploy/submodules.py" --name "$r" --field new_path)
  if [[ ! -d "$path/.git" ]] && ! git submodule status "$path" >/dev/null 2>&1; then
    echo "✖ Submodule not initialized: $r ($path)"
    exit 1
  fi
done

echo "✓ Submodules present and initialized"
