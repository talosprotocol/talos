#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Start All Services
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"
REPORTS_DIR="$ROOT_DIR/deploy/reports"
LOGS_DIR="$REPORTS_DIR/logs"

mkdir -p "$LOGS_DIR"

# Source common helpers
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

# =============================================================================
# 0. Setup
# =============================================================================
export TALOS_GATEWAY_PORT=8000 # Force Gateway to 8000 (Dashboard expectation)
export TALOS_GATEWAY_URL="http://localhost:8000"

info "Running Setup (Lenient Mode)..."
# Using flag --lenient (upgraded from env var)
"$SCRIPT_DIR/setup.sh" --lenient || {
    error "Setup failed. Check logs."
    exit 1
}

# =============================================================================
# Helpers
# =============================================================================
# wait_for_port matches common.sh


# Uses shared install_deps from common.sh

start_service() {
    local repo_name="$1"
    local service_name="$2"
    local port="$3"
    local endpoint="$4"
    local repo_dir="$REPOS_DIR/$repo_name"

    info "Starting $service_name..."
    
    # Install Deps (using shared helper)
    install_deps "$repo_dir" "$repo_name" "$LOGS_DIR" || {
        error "Dependency installation failed for $repo_name"
        return 1
    }

    # Start
    local start_script="$repo_dir/scripts/start.sh"
    if [[ ! -f "$start_script" ]]; then
        error "Missing start script: $start_script"
        return 1
    fi

    # Run start script
    # We rely on the script to background itself or use a process manager if needed.
    # But wait, our canonical start scripts (dashboard/mcp) DO background themselves.
    # talos-sdk-ts is a test runner, not a service, so we don't start it here in the service loop.
    
    # Passing env vars if needed
    bash "$start_script" > "$LOGS_DIR/${service_name}.start.log" 2>&1
    
    # Wait
    wait_for_port "$port" "$endpoint" "$service_name"
}

# =============================================================================
# Main Loop
# =============================================================================
for service in "${COMMON_SERVICES[@]}"; do
    IFS=':' read -r name port endpoint <<< "$service"
    # Note: repo_name is assumed to be same as name for simple services
    start_service "$name" "$name" "$port" "$endpoint" || exit 1
done

info ""
info "All services started successfully."
log "Logs available in: $LOGS_DIR"
