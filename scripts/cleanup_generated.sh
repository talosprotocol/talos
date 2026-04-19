#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$ROOT_DIR/deploy/scripts/common.sh"

cleanup_generated_files "$ROOT_DIR"
rm -f /tmp/talos-*.pid /tmp/talos-*.log 2>/dev/null || true

log "Generated logs, temp files, and test caches removed."
