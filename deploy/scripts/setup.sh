#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Setup Script
# =============================================================================
# Production-grade submodule initialization with SSH/HTTPS fallback.
#
# Environment Variables:
#   TALOS_SETUP_MODE          - lenient (default) | strict
#   TALOS_USE_GLOBAL_INSTEADOF - 0 (default) | 1
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

MODE="${TALOS_SETUP_MODE:-lenient}"   # lenient | strict
USE_GLOBAL_INSTEADOF="${TALOS_USE_GLOBAL_INSTEADOF:-0}"  # 0 | 1

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

log() { printf '%s\n' "$*"; }
warn() { printf '⚠ WARN: %s\n' "$*" >&2; }
die() { printf '✖ ERROR: %s\n' "$*" >&2; exit 1; }

has_ssh_github() {
  # Exit codes:
  # 1 is normal for GitHub ("successfully authenticated, but no shell access")
  # 255 usually means no key / no auth / network blocked
  local out
  out="$(ssh -o BatchMode=yes -o ConnectTimeout=5 -T git@github.com 2>&1 || true)"
  
  if [[ "$out" == *"successfully authenticated"* ]] || \
     [[ "$out" == *"You've successfully authenticated"* ]] || \
     [[ "$out" == *"Hi "* && "$out" == *"successfully authenticated"* ]] || \
     [[ "$out" == *"no shell access"* ]]; then
    return 0
  fi
  return 1
}

configure_https_fallback() {
  log "SSH not available. Configuring HTTPS fallback for this repo."
  if [[ "$USE_GLOBAL_INSTEADOF" == "1" ]]; then
    git config --global url."https://github.com/".insteadOf "git@github.com:"
    git config --global url."https://github.com/".insteadOf "ssh://git@github.com/"
  else
    git config url."https://github.com/".insteadOf "git@github.com:"
    git config url."https://github.com/".insteadOf "ssh://git@github.com/"
  fi
}

init_one() {
  local name="$1"
  local path="deploy/repos/$name"
  
  if [[ ! -d "$path" ]]; then
    warn "$name path missing ($path). Is the submodule declared in .gitmodules?"
    return 1
  fi

  # Initialize only this submodule. Do not recurse by default.
  if git submodule update --init "$path" >/dev/null 2>&1; then
    log "✓ Initialized $name"
    return 0
  fi

  warn "$name unavailable (private, no access, or network/auth issue)"
  return 1
}

main() {
  log "== Talos Setup =="
  log "Mode: $MODE"
  log "Repo: $ROOT_DIR"
  log ""

  if has_ssh_github; then
    log "Using SSH for submodules."
  else
    configure_https_fallback
  fi

  # Ensure submodule metadata is present
  if [[ ! -f ".gitmodules" ]]; then
    die ".gitmodules not found. Run submodule add steps first."
  fi

  local missing=()
  for r in "${REPOS[@]}"; do
    if ! init_one "$r"; then
      missing+=("$r")
    fi
  done

  echo ""
  if (( ${#missing[@]} > 0 )); then
    warn "Missing submodules: ${missing[*]}"
    if [[ "$MODE" == "strict" ]]; then
      die "Setup failed in strict mode due to missing submodules."
    else
      warn "Continuing in lenient mode."
    fi
  else
    log "✓ All submodules initialized."
  fi

  log ""
  log "Done. Run './deploy/scripts/run_all_tests.sh' to validate."
}

main "$@"
