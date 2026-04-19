#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "DEPRECATED: scripts/run-karate.sh has moved to api-testing/karate/run-karate.sh" >&2
exec "$ROOT_DIR/api-testing/karate/run-karate.sh" "$@"
