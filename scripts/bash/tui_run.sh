#!/bin/bash
set -e

# Get directory of this script (repo/scripts)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$DIR/.."
TUI_DIR="$REPO_ROOT/tools/talos-tui/python"

cd "$TUI_DIR"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Running setup..."
    make setup
fi

echo "Starting Talos TUI..."
source .venv/bin/activate
talos-tui "$@"
