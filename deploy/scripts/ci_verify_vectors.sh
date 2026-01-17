#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# CI: Verify Test Vectors
# =============================================================================
# Ensures test vectors exist, are non-empty, and are valid JSON.
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

VECTORS_DIR="contracts/test_vectors"

# Check directory exists
if [[ ! -d "$VECTORS_DIR" ]]; then
  echo "✖ test_vectors directory missing: $VECTORS_DIR"
  exit 1
fi

# Count vector files
count="$(find "$VECTORS_DIR" -type f \( -name "*.json" -o -name "*.jsonl" \) | wc -l | tr -d ' ')"
if [[ "$count" == "0" ]]; then
  echo "✖ No vector files found in $VECTORS_DIR"
  exit 1
fi

# Validate JSON files
bad=0
while IFS= read -r f; do
  if ! python3 -c 'import json,sys; json.load(open(sys.argv[1],"rb"))' "$f" >/dev/null 2>&1; then
    echo "✖ Invalid JSON: $f"
    bad=1
  fi
done < <(find "$VECTORS_DIR" -type f -name "*.json")

if [[ "$bad" == "1" ]]; then
  exit 1
fi

echo "✓ Vectors present and parseable ($count files)"
