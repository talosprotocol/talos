#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Start All Services
# =============================================================================
# harden: deterministic installs, canonical entrypoints, and health checks.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"
REPORTS_DIR="$ROOT_DIR/deploy/reports"
LOGS_DIR="$REPORTS_DIR/logs"

mkdir -p "$LOGS_DIR"

log() { printf '%s\n' "$*"; }
info() { printf 'ℹ️  %s\n' "$*"; }
warn() { printf '⚠  %s\n' "$*"; }
error() { printf '✖  %s\n' "$*" >&2; }

# =============================================================================
# 0. Setup
# =============================================================================
info "Running Setup (Lenient Mode)..."
# Using env var for now until setup.sh is upgraded to flags in Phase 3
TALOS_SETUP_MODE=lenient "$SCRIPT_DIR/setup.sh" || {
    error "Setup failed. Check logs."
    exit 1
}

# =============================================================================
# Service Definitions
# =============================================================================
# Format: repo_name:service_name:port:health_path
SERVICES=(
    "talos-gateway:talos-gateway:8080:/api/gateway/status"
    "talos-audit-service:talos-audit-service:8081:/health"
    "talos-mcp-connector:talos-mcp-connector:8082:/health"
    "talos-dashboard:talos-dashboard:3000:/"
)

# =============================================================================
# Helpers
# =============================================================================
wait_for_port() {
    local port="$1"
    local endpoint="$2"
    local name="$3"
    local retries=30
    local wait=2

    info "Waiting for $name on port $port..."
    for ((i=1; i<=retries; i++)); do
        if curl -sf "http://127.0.0.1:${port}${endpoint}" >/dev/null 2>&1; then
            info "✓ $name is healthy!"
            return 0
        fi
        sleep "$wait"
    done
    error "Timed out waiting for $name"
    return 1
}

install_deps() {
    local repo_dir="$1"
    local repo_name="$2"
    
    info "Installing dependencies for $repo_name..."
    cd "$repo_dir"

    # 1. Custom Setup Script
    if [[ -f "scripts/setup.sh" ]]; then
        info "  Running scripts/setup.sh..."
        bash "scripts/setup.sh"
        return $?
    fi

    # 2. Node.js
    if [[ -f "package-lock.json" ]]; then
        info "  Found package-lock.json, running npm ci..."
        npm ci > "$LOGS_DIR/${repo_name}.install.log" 2>&1
        return 0
    fi

    # 3. Python (pyproject.toml)
    if [[ -f "pyproject.toml" ]]; then
        info "  Found pyproject.toml, running pip install -e..."
        pip install -e ".[dev]" > "$LOGS_DIR/${repo_name}.install.log" 2>&1
        return 0
    fi
    
    # 4. Python (requirements.txt)
    if [[ -f "requirements.txt" ]]; then
        info "  Found requirements.txt, running pip install..."
        pip install -r requirements.txt > "$LOGS_DIR/${repo_name}.install.log" 2>&1
        return 0
    fi
    
    # 5. Rust
    if [[ -f "Cargo.toml" ]]; then
        info "  Found Cargo.toml, fetching..."
        cargo fetch > "$LOGS_DIR/${repo_name}.install.log" 2>&1
        return 0
    fi

    warn "No recognized dependency file found for $repo_name. Skipping install."
    return 0
}

start_service() {
    local repo_name="$1"
    local service_name="$2"
    local port="$3"
    local endpoint="$4"
    local repo_dir="$REPOS_DIR/$repo_name"

    info "Starting $service_name..."
    
    # Install Deps
    install_deps "$repo_dir" "$repo_name" || {
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
for service in "${SERVICES[@]}"; do
    IFS=':' read -r repo svc port endpoint <<< "$service"
    start_service "$repo" "$svc" "$port" "$endpoint" || exit 1
done

info ""
info "All services started successfully."
log "Logs available in: $LOGS_DIR"
