#!/usr/bin/env bash
# =============================================================================
# Talos Protocol - Shared Operations Helpers
# =============================================================================

# Standard Logging
log() { printf '%s\n' "$*"; }
info() { printf 'ℹ️  %s\n' "$*"; }
warn() { printf '⚠  %s\n' "$*"; }
error() { printf '✖  %s\n' "$*" >&2; }
die() { printf '✖  ERROR: %s\n' "$*" >&2; exit 1; }

# Canonical Repository List (in dependency order)
COMMON_REPOS=(
    "talos-contracts"
    "talos-core-rs"
    "talos-sdk-py"
    "talos-sdk-ts"
    "talos-sdk-go"
    "talos-sdk-java"
    "talos-gateway"
    "talos-audit-service"
    "talos-mcp-connector"
    "talos-dashboard"
)

# Services that can be started/stopped
COMMON_SERVICES=(
    "talos-gateway:8080:/api/gateway/status"
    "talos-audit-service:8081:/health"
    "talos-mcp-connector:8082:/health"
    "talos-dashboard:3000:/"
)

# Version Validation (major.minor)
check_version() {
    local cmd="$1"
    local name="$2"
    local min_version="$3"
    local mode="${4:-strict}"
    
    if ! command -v "$cmd" >/dev/null 2>&1; then
        if [[ "$mode" == "strict" ]]; then
            die "$name not found ($cmd)."
        else
            warn "$name not found."
            return 1
        fi
    fi

    local version
    version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true)
    if [[ -z "$version" ]]; then
         version=$("$cmd" -v 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1 || true)
    fi

    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    local min_major=$(echo "$min_version" | cut -d. -f1)
    local min_minor=$(echo "$min_version" | cut -d. -f2)

    if [[ "$major" -gt "$min_major" ]] || [[ "$major" -eq "$min_major" && "${minor:-0}" -ge "${min_minor:-0}" ]]; then
        log "✓ $name $version (>= $min_version)"
    else
        local msg="Invalid $name version: $version (Required >= $min_version)"
        if [[ "$mode" == "strict" ]]; then
            die "$msg"
        else
            warn "$msg"
        fi
    fi
}

# Healthy Check Helper
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
