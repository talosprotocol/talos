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

log() { printf '%s\n' "$*"; }
warn() { printf '⚠ WARN: %s\n' "$*" >&2; }
die() { printf '✖ ERROR: %s\n' "$*" >&2; exit 1; }

check_version() {
    local cmd="$1"
    local name="$2"
    local min_version="$3" # Now supports x.y format
    
    if ! command -v "$cmd" >/dev/null 2>&1; then
        if [[ "$MODE" == "strict" ]]; then
            die "$name not found ($cmd)."
        else
            warn "$name not found."
            return 1
        fi
    fi

    # Basic version extraction
    local version
    version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true)
    
    if [[ -z "$version" ]]; then
         version=$("$cmd" -v 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true)
    fi

    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    local min_major=$(echo "$min_version" | cut -d. -f1)
    local min_minor=$(echo "$min_version" | cut -d. -f2)

    # Compare version components
    if [[ "$major" -gt "$min_major" ]] || [[ "$major" -eq "$min_major" && "${minor:-0}" -ge "${min_minor:-0}" ]]; then
        log "✓ $name $version (>= $min_version)"
    else
        msg="Invalid $name version: $version (Required >= $min_version)"
        if [[ "$MODE" == "strict" ]]; then
            die "$msg"
        else
            warn "$msg"
        fi
    fi
}

# =============================================================================
# 1. Environment Checks
# =============================================================================
log "== Environment Validation ($MODE) =="

check_version "python3" "Python" "3.11"
check_version "node" "Node.js" "20.0"
check_version "npm" "npm" "10.0"

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
