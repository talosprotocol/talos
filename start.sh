#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

source_env_file() {
  local file="$1"
  if [ -f "$file" ]; then
    set -a
    . "$file"
    set +a
  fi
}

# 1. Load Environment
source_env_file "$ROOT_DIR/.env"
source_env_file "$ROOT_DIR/.env.local"

# 2. Defaults
export TALOS_ENV="${TALOS_ENV:-development}"
export MODE="${MODE:-dev}"
export DEV_MODE="${DEV_MODE:-true}"
export TALOS_BIND_HOST="${TALOS_BIND_HOST:-127.0.0.1}"
export TALOS_GATEWAY_PORT="${TALOS_GATEWAY_PORT:-8000}"
export TALOS_DASHBOARD_PORT="${TALOS_DASHBOARD_PORT:-3000}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${TALOS_GATEWAY_PORT}}"

# 3. Arguments
CHECK_TOPOLOGY=false
for arg in "$@"; do
  if [ "$arg" == "--check-topology" ]; then
    CHECK_TOPOLOGY=true
  fi
done

# 4. Topology Verification (Phase 12 Alignment)
if [ "$CHECK_TOPOLOGY" = true ]; then
  printf 'Verifying Gateway Topology...\n'
  MISSING=0
  for REGION in US EU ASIA; do
    VAR="MCP_SERVER_${REGION}"
    if [ -z "${!VAR:-}" ]; then
      printf '  ⚠️  %s is not set (Regional failover may be limited)\n' "$VAR"
      MISSING=$((MISSING+1))
    else
      printf '  ✓ %s: %s\n' "$VAR" "${!VAR}"
    fi
  done
  
  if [ "$MISSING" -eq 3 ] && [ "$MODE" = "prod" ]; then
    printf '  ❌ ERROR: No regional gateways configured for production topology.\n'
    exit 1
  fi
  printf 'Topology check complete.\n\n'
  if [ "$#" -eq 1 ]; then exit 0; fi # Exit if only checking
fi

# 5. Start Stack
printf 'Starting Talos quick-start stack (Canonical: ai-gateway)\n'
printf '  Ingress:   http://%s:%s\n' "$TALOS_BIND_HOST" "$TALOS_GATEWAY_PORT"
printf '  Dashboard: http://%s:%s\n' "$TALOS_BIND_HOST" "$TALOS_DASHBOARD_PORT"

# Ensure we use the hardened ai-gateway
bash "$ROOT_DIR/services/ai-gateway/scripts/start.sh"
bash "$ROOT_DIR/site/dashboard/scripts/start.sh"
