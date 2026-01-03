#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Start All Services
# =============================================================================
# Validates all services are running, rebuilds and restarts if needed.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOS_DIR="$(cd "$SCRIPT_DIR/../repos" && pwd)"

# =============================================================================
# Validation
# =============================================================================
check_pyenv() {
    if ! command -v pyenv &> /dev/null; then
        echo -e "${RED}[ERROR] pyenv is not installed or not in PATH.${NC}"
        echo "Please install pyenv and configure it in your shell."
        exit 1
    fi
    
    if [[ -z "${PYENV_ROOT:-}" ]]; then
         # Try to detect if it's set up but variable missing
         if [[ ! -d "$HOME/.pyenv" ]]; then
            echo -e "${RED}[ERROR] pyenv not detected (PYENV_ROOT not set and ~/.pyenv missing).${NC}"
            exit 1
         fi
    fi
    
    log_info "pyenv detected."
}

# Service definitions: name:port:health_endpoint
SERVICES=(
    "talos-gateway:8080:/api/gateway/status"
    "talos-audit-service:8081:/health"
    "talos-mcp-connector:8082:/health"
    "talos-dashboard:3000:/"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Check if service is healthy
# =============================================================================
check_service_health() {
    local name="$1"
    local port="$2"
    local endpoint="$3"
    
    if curl -sf "http://127.0.0.1:${port}${endpoint}" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# =============================================================================
# Stop service
# =============================================================================
stop_service() {
    local name="$1"
    local pid_file="/tmp/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        kill "$(cat "$pid_file")" 2>/dev/null || true
        rm -f "$pid_file"
        log_info "Stopped $name"
    fi
}

# =============================================================================
# Build and start service
# =============================================================================
start_service() {
    local name="$1"
    local repo_dir="$REPOS_DIR/$name"
    local start_script="$repo_dir/scripts/start.sh"
    
    if [ ! -f "$start_script" ]; then
        log_warn "$name has no start.sh, skipping"
        return 0
    fi
    
    # Install dependencies and build
    log_info "Building $name..."
    (cd "$repo_dir" && make install build 2>/dev/null) || {
        log_warn "$name: make failed, trying npm/pip directly..."
        if [ -f "$repo_dir/package.json" ]; then
            (cd "$repo_dir" && npm ci 2>/dev/null) || true
        fi
    }
    
    # Start service
    log_info "Starting $name..."
    bash "$start_script"
}

# =============================================================================
# Main
# =============================================================================
echo "=========================================="
echo "Talos Protocol - Start All Services"
echo "=========================================="
echo ""

# First, check validations
check_pyenv

# Check existing services
log_info "Checking service health..."
needs_restart=()

for entry in "${SERVICES[@]}"; do
    IFS=':' read -r name port endpoint <<< "$entry"
    
    if check_service_health "$name" "$port" "$endpoint"; then
        log_info "$name is healthy (port $port)"
    else
        log_warn "$name is not running or unhealthy"
        needs_restart+=("$entry")
    fi
done

# Rebuild and restart unhealthy services
if [ ${#needs_restart[@]} -gt 0 ]; then
    echo ""
    log_info "Rebuilding and restarting ${#needs_restart[@]} service(s)..."
    echo ""
    
    for entry in "${needs_restart[@]}"; do
        IFS=':' read -r name port endpoint <<< "$entry"
        
        # Stop if running
        stop_service "$name"
        
        # Build and start
        start_service "$name"
        
        # Wait for health
        sleep 3
        if check_service_health "$name" "$port" "$endpoint"; then
            log_info "✓ $name is now healthy"
        else
            log_error "✗ $name failed to start"
        fi
    done
fi

# Final status
echo ""
echo "=========================================="
echo "Service Status Summary"
echo "=========================================="

all_healthy=true
for entry in "${SERVICES[@]}"; do
    IFS=':' read -r name port endpoint <<< "$entry"
    
    if check_service_health "$name" "$port" "$endpoint"; then
        echo -e "  ${GREEN}✓${NC} $name (port $port)"
    else
        echo -e "  ${RED}✗${NC} $name (port $port)"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    log_info "All services are running!"
else
    log_warn "Some services are not running. Check logs in /tmp/"
fi
