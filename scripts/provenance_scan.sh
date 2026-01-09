#!/usr/bin/env bash
# provenance_scan.sh
# Scans repos for MIT license remnants and third-party directories.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_FILE="$SCRIPT_DIR/repos_manifest.txt"
REPORT_FILE="$SCRIPT_DIR/provenance_report.txt"
THIRD_PARTY_FILE="$SCRIPT_DIR/third_party_dirs.txt"
MIT_THIRD_PARTY_FILE="$SCRIPT_DIR/mit_matches_third_party.txt"

fail() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }

[[ -f "$MANIFEST_FILE" ]] || fail "Manifest not found: $MANIFEST_FILE"

# Patterns to search for
PATTERNS=(
  "MIT License"
  "Permission is hereby granted"
  "SPDX-License-Identifier: MIT"
)

# Third-party directory names
THIRD_PARTY_DIRS=(
  "vendor"
  "third_party"
  "external"
  "deps"
  "subprojects"
)

# Exclusion patterns (build outputs, dependencies)
EXCLUSIONS=(
  "*/node_modules/*"
  "*/.venv/*"
  "*/target/*"
  "*/dist/*"
  "*/build/*"
  "*/.next/*"
  "*/.cache/*"
  "*/.turbo/*"
  "*/.git/*"
  "*/package-lock.json"
  "*/yarn.lock"
  "*/pnpm-lock.yaml"
  "*/Cargo.lock"
)

echo "Starting provenance scan..."
echo "Manifest: $MANIFEST_FILE"
echo ""

# Initialize outputs
>"$REPORT_FILE"
>"$THIRD_PARTY_FILE"
>"$MIT_THIRD_PARTY_FILE"

found_third_party=false
found_mit_outside=false

# Build exclusion args for rg
EXCLUDE_ARGS=()
for excl in "${EXCLUSIONS[@]}"; do
  EXCLUDE_ARGS+=("-g" "!$excl")
done

# Read repos into array (macOS compatible)
repos=()
while IFS= read -r line; do
  [[ -n "$line" ]] && repos+=("$line")
done < "$MANIFEST_FILE"

for repo in "${repos[@]}"; do
  echo "==> Scanning: $repo"

  # Detect third-party directories
  for tp_dir in "${THIRD_PARTY_DIRS[@]}"; do
    while IFS= read -r -d '' found_dir; do
      echo "  [THIRD-PARTY] $found_dir" | tee -a "$THIRD_PARTY_FILE"
      found_third_party=true
    done < <(find "$repo" -type d -name "$tp_dir" -print0 2>/dev/null || true)
  done

  # Search for MIT patterns
  for pattern in "${PATTERNS[@]}"; do
    # Use rg if available, else grep
    if command -v rg &>/dev/null; then
      matches=$(rg -l --hidden "${EXCLUDE_ARGS[@]}" "$pattern" "$repo" 2>/dev/null || true)
    else
      matches=$(grep -rl --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=target --exclude-dir=dist --exclude-dir=build --exclude-dir=.git "$pattern" "$repo" 2>/dev/null || true)
    fi

    if [[ -n "$matches" ]]; then
      while IFS= read -r match; do
        # Check if match is inside a third-party dir
        is_third_party=false
        if [[ -f "$THIRD_PARTY_FILE" ]]; then
          while IFS= read -r tp_dir; do
            if [[ "$match" == "$tp_dir"* ]]; then
              is_third_party=true
              break
            fi
          done < "$THIRD_PARTY_FILE"
        fi

        if [[ "$is_third_party" == true ]]; then
          echo "  [MIT-THIRD-PARTY] $match (pattern: $pattern)" | tee -a "$MIT_THIRD_PARTY_FILE"
        else
          echo "  [MIT-OUTSIDE] $match (pattern: $pattern)" | tee -a "$REPORT_FILE"
          found_mit_outside=true
        fi
      done <<< "$matches"
    fi
  done
done

echo ""
echo "=== Provenance Scan Summary ==="

if [[ "$found_third_party" == true ]]; then
  echo "Third-party directories detected. See: $THIRD_PARTY_FILE"
  echo "MIT matches in third-party dirs: $MIT_THIRD_PARTY_FILE"
else
  echo "No third-party directories detected."
  rm -f "$THIRD_PARTY_FILE" "$MIT_THIRD_PARTY_FILE"
fi

if [[ "$found_mit_outside" == true ]]; then
  echo ""
  echo "FAIL: MIT remnants found outside third-party/exclusions!"
  echo "See: $REPORT_FILE"
  exit 1
else
  echo "No MIT remnants found outside third-party/exclusions."
  rm -f "$REPORT_FILE"
fi

echo ""
echo "Provenance scan PASSED."
