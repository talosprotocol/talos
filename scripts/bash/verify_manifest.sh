#!/bin/bash
set -e

# Wrapper script to run the Python manifest validator
# Usage: ./verify_manifest.sh <path_to_manifest>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR_SCRIPT="${SCRIPT_DIR}/validate_manifest.py"

if [ ! -f "$VALIDATOR_SCRIPT" ]; then
    echo "❌ Error: Validator script not found at $VALIDATOR_SCRIPT"
    exit 1
fi

# Ensure output is unbuffered
export PYTHONUNBUFFERED=1

# Execute the python validator
python3 "$VALIDATOR_SCRIPT" "$@"
