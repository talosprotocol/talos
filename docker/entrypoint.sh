#!/bin/sh
set -e

# Talos Node Entrypoint Shim
# This script standardizes the container interface.

cmd="$1"

# Function to run the Talos server
run_server() {
    # Default to 8000 if PORT is not set
    PORT="${PORT:-8000}"
    exec python -m src.server.server --port "$PORT" --host "0.0.0.0" "$@"
}

# Function to run health check
run_healthcheck() {
    # Check if the server is running on localhost:8000/healthz
    if command -v curl >/dev/null 2>&1; then
        exec curl -f http://localhost:8000/healthz
    else
        echo "Error: curl not found"
        exit 1
    fi
}

show_help() {
    echo "Talos Node Container"
    echo "Usage:"
    echo "  serve         Start the Talos Node (Gateway/Control Plane)"
    echo "  healthcheck   Run a health check against the local node"
    echo "  help          Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  TALOS_MODE    Node mode (default: gateway)"
    echo "  PORT          Listening port (default: 8000)"
}

case "$cmd" in
    "serve")
        shift
        run_server "$@"
        ;;
    "healthcheck")
        run_healthcheck
        ;;
    "help")
        show_help
        ;;
    *)
        # If the command is not recognized, assume it's "serve" if it starts with a flag,
        # or execute it directly if it looks like a command.
        if [ "${cmd#http}" != "$cmd" ] || [ "${cmd#-}" != "$cmd" ]; then
             # If argument starts with - (flag), pass to server
             run_server "$@"
        else
            # Otherwise, just exec the command (useful for debugging like /bin/sh)
            exec "$@"
        fi
        ;;
esac
