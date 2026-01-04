#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Setup Script
# =============================================================================
# Initializes submodules and validates the development environment.
# Usage: ./setup.sh [--lenient | --strict]
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"

# Required submodules (must exist)
REQUIRED_REPOS=(
    "talos-contracts"
    "talos-examples"
    "talos-docs"
)

MODE="strict" # Default to strict, downgrade to lenient with flag or env var

# Argument Parsing
for arg in "$@"; do
  case $arg in
    --lenient) MODE="lenient" ;;
    --strict)  MODE="strict" ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# Fallback to env var if set
if [[ -n "${TALOS_SETUP_MODE:-}" ]]; then
    MODE="$TALOS_SETUP_MODE"
fi

# Source common helpers
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

# =============================================================================
# 1. Environment Checks
# =============================================================================
log "== Environment Validation ($MODE) =="

check_version "python3" "Python" "3.11" "$MODE"
check_version "node" "Node.js" "20.0" "$MODE"
check_version "npm" "npm" "10.0" "$MODE"

if command -v cargo >/dev/null 2>&1; then
    log "✓ Cargo detected"
else
    # Only strict fail if we are building Rust? No, let's keep it optional but warn.
    warn "Cargo (Rust) not found. Rust components will not build."
    if [[ "$MODE" == "strict" ]]; then
         # Check if we actually need rust
         if [[ -d "$REPOS_DIR/talos-core-rs" ]]; then
             die "Cargo missing but talos-core-rs is present."
         fi
    fi
fi

echo ""

# =============================================================================
# 2. Submodule Initialization
# =============================================================================
log "== Submodule Initialization =="

if [[ ! -f "$ROOT_DIR/.gitmodules" ]]; then
    die ".gitmodules not found."
fi

# Try SSH, fallback to HTTPS if configured globally or just try
# We'll use the specific init logic from before but simplified
echo "Updating submodules..."
if git submodule update --init --recursive; then
    log "✓ Submodules updated."
else
    msg="Submodule update failed."
    if [[ "$MODE" == "strict" ]]; then
        die "$msg"
    else
        warn "$msg Continuing in lenient mode (some repos may be empty)."
    fi
fi

# Validate presence of required repos
for repo in "${REQUIRED_REPOS[@]}"; do
    if [[ ! -d "$REPOS_DIR/$repo" ]] || [[ -z "$(ls -A "$REPOS_DIR/$repo")" ]]; then
        msg="Required submodule '$repo' is missing or empty."
        if [[ "$MODE" == "strict" ]]; then
            die "$msg"
        else
            warn "$msg"
        fi
    else
        log "✓ Verified $repo"
    fi
done

echo ""
log "Setup Complete."
