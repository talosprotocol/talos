#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Talos Protocol - Stop All Services
# =============================================================================
# Stops services via PID files (preferred) or Port killing (fallback).
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common helpers
if [[ -f "$SCRIPT_DIR/common.sh" ]]; then
    source "$SCRIPT_DIR/common.sh"
else
    printf '✖ ERROR: common.sh not found at %s\n' "$SCRIPT_DIR/common.sh" >&2
    exit 1
fi

kill_by_pid() {
    local name="$1"
    local pid_file="$2"

    if [[ -f "$pid_file" ]]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            info "Stopping $name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            # Wait for it to die
            for i in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then break; fi
                sleep 1
            done
            # Force kill if needed
            if kill -0 "$pid" 2>/dev/null; then
                warn "$name did not stop, sending SIGKILL..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        else
            info "$name PID file exists but process is gone."
        fi
        rm -f "$pid_file"
        return 0
    fi
    return 1
}

kill_by_port() {
    local name="$1"
    local port="$2"
    
    # lsof -ti :<port>
    local pids
    pids=$(lsof -ti :"$port" || true)
    
    if [[ -n "$pids" ]]; then
        warn "Found active process for $name on port $port (PIDs: $pids). Killing..."
        echo "$pids" | xargs kill -9 2>/dev/null || true
        return 0
    fi
    return 1
}

log "== Stopping All Services =="

for service in "${COMMON_SERVICES[@]}"; do
    IFS=':' read -r name port health_path <<< "$service"
    
    stopped=0
    
    # 1. Try /tmp PID (Current standard)
    if kill_by_pid "$name" "/tmp/${name}.pid"; then
        stopped=1
    fi
    
    # 2. Try Reports PID (Future standard)
    if kill_by_pid "$name" "$ROOT_DIR/deploy/reports/pids/${name}.pid"; then
        stopped=1
    fi
    
    # 3. Fallback to Port
    if kill_by_port "$name" "$port"; then
        stopped=1
    fi
    
    if [[ $stopped -eq 1 ]]; then
        log "✓ $name stopped"
    else
        log "✓ $name was not running"
    fi
done

log ""
log "All services stopped."
