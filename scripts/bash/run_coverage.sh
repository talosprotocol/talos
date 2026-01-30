#!/bin/bash
set -e

# Wrapper script to run the Python Coverage Coordinator
# Usage: ./run_coverage.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COORDINATOR_SCRIPT="${SCRIPT_DIR}/../python/coverage_coordinator.py"

if [ ! -f "$COORDINATOR_SCRIPT" ]; then
    echo "❌ Error: Coordinator script not found at $COORDINATOR_SCRIPT"
    exit 1
fi

# Ensure output is unbuffered
export PYTHONUNBUFFERED=1

echo "🚀 Launching Coverage Coordinator..."
python3 "$COORDINATOR_SCRIPT" "$@"
