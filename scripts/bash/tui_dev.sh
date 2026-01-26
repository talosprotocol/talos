#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$DIR/.."
TUI_DIR="$REPO_ROOT/tools/talos-tui/python"

cd "$TUI_DIR"
echo "Setting up development environment..."
make setup
echo "Done. To run tests: make test"
