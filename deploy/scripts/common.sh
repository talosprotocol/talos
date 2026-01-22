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
# All 15 submodules from .gitmodules
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
    "talos-aiops"
    "talos-ai-chat-agent"
    "talos-ai-gateway"
    "talos-dashboard"
    "talos-examples"
    "talos-docs"
    "talos-site"
    "talos-ucp-connector"
)

# Services that can be started/stopped
COMMON_SERVICES=(
    "talos-gateway:8000:/api/gateway/status"
    "talos-audit-service:8001:/health"
    "talos-mcp-connector:8082:/health"
    "talos-ucp-connector:8083:/"
    "talos-aiops:8200:/health"
    "talos-ai-chat-agent:8100:/health"
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
# Install Dependencies for a Repo
install_deps() {
    local repo_dir="$1"
    local repo_name="$2"
    local logs_dir="${3:-/tmp}"
    
    info "Installing dependencies for $repo_name..."
    (
        cd "$repo_dir" || return 1
        local log_file="$logs_dir/${repo_name}.install.log"
        rm -f "$log_file"

        # 1. Custom Setup Script
        if [[ -f "scripts/setup.sh" ]]; then
            info "  Running scripts/setup.sh..."
            bash "scripts/setup.sh" >> "$log_file" 2>&1
            return $?
        fi

        # 2. Check for sub-packages (contracts style)
        local found=0
        for sub in "typescript" "python" "sdk"; do
            if [[ -d "$sub" ]]; then
                if [[ -f "$sub/package.json" ]]; then
                    info "  Found $sub/package.json, running npm install..."
                    (cd "$sub" && npm install --no-audit --no-fund >> "$log_file" 2>&1) || return 1
                    found=1
                fi
                if [[ -f "$sub/pyproject.toml" ]] || [[ -f "$sub/requirements.txt" ]]; then
                    info "  Found Python in $sub, running pip install..."
                    (cd "$sub" && pip install -e . >> "$log_file" 2>&1) || return 1
                    found=1
                fi
            fi
        done
        [[ $found -eq 1 ]] && return 0

        # 3. Root Level - Node.js
        if [[ -f "package-lock.json" ]] || [[ -f "package.json" ]]; then
            info "  Found Node.js, running npm install..."
            npm install --no-audit --no-fund >> "$log_file" 2>&1 || return 1
            return 0
        fi

        # 4. Root Level - Python
        if [[ -f "pyproject.toml" ]]; then
            info "  Found pyproject.toml, running pip install -e..."
            pip install -e ".[dev]" >> "$log_file" 2>&1 || return 1
            return 0
        fi
        
        if [[ -f "requirements.txt" ]]; then
            info "  Found requirements.txt, running pip install..."
            pip install -r requirements.txt >> "$log_file" 2>&1 || return 1
            return 0
        fi
        
        # 5. Root Level - Rust
        if [[ -f "Cargo.toml" ]]; then
            info "  Found Cargo.toml, fetching..."
            cargo fetch >> "$log_file" 2>&1 || return 1
            return 0
        fi

        # 6. Root Level - Go
        if [[ -f "go.mod" ]]; then
            info "  Found go.mod, downloading..."
            go mod download >> "$log_file" 2>&1 || return 1
            return 0
        fi

        # 7. Root Level - Java (Maven)
        if [[ -f "pom.xml" ]]; then
            info "  Found pom.xml, resolving..."
            local mvn_cmd="./mvnw"
            [[ ! -f "$mvn_cmd" ]] && mvn_cmd="mvn"
            $mvn_cmd install -DskipTests -q -am >> "$log_file" 2>&1 || return 1
            return 0
        fi

        warn "No recognized dependency file found for $repo_name. Skipping."
        return 0
    )
}
