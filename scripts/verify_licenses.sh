#!/usr/bin/env bash
# verify_licenses.sh
# Verifies that all repos in the manifest have correct Apache 2.0 licensing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_FILE="$SCRIPT_DIR/repos_manifest.txt"

fail() { echo "FAIL: $*" >&2; FAILURES=$((FAILURES + 1)); }
pass() { echo "PASS: $*"; }

[[ -f "$MANIFEST_FILE" ]] || { echo "ERROR: Manifest not found: $MANIFEST_FILE"; exit 1; }

FAILURES=0

# Read repos
repos=()
while IFS= read -r line; do
  [[ -n "$line" ]] && repos+=("$line")
done < "$MANIFEST_FILE"

echo "Verifying ${#repos[@]} repos..."
echo ""

for repo in "${repos[@]}"; do
  echo "==> Checking: $repo"

  # Check LICENSE exists and contains Apache 2.0
  license_file="$repo/LICENSE"
  if [[ -f "$license_file" ]]; then
    if grep -q "Apache License" "$license_file" && grep -q "Version 2.0" "$license_file"; then
      pass "LICENSE contains Apache 2.0"
    else
      fail "LICENSE does not contain Apache License Version 2.0"
    fi
  else
    fail "LICENSE file missing"
  fi

  # Check NOTICE exists
  notice_file="$repo/NOTICE"
  if [[ -f "$notice_file" ]]; then
    pass "NOTICE file exists"
  else
    fail "NOTICE file missing"
  fi

  # Check README references Apache 2.0 and no MIT
  readme_file=""
  [[ -f "$repo/README.md" ]] && readme_file="$repo/README.md"
  [[ -f "$repo/README.MD" ]] && readme_file="$repo/README.MD"

  if [[ -n "$readme_file" ]]; then
    if grep -qi "Apache" "$readme_file"; then
      pass "README references Apache"
    else
      fail "README does not reference Apache"
    fi

    if grep -qi "MIT License" "$readme_file"; then
      fail "README still references MIT License"
    else
      pass "README has no MIT License reference"
    fi
  fi

  # Check Python pyproject.toml (if exists)
  pyproject="$repo/pyproject.toml"
  if [[ -f "$pyproject" ]]; then
    if grep -Eq 'license\s*=.*LICENSE|license\s*=.*Apache' "$pyproject"; then
      pass "pyproject.toml has Apache license"
    elif grep -qi 'MIT' "$pyproject"; then
      fail "pyproject.toml still has MIT reference"
    else
      pass "pyproject.toml has no MIT reference (may not have license field)"
    fi
  fi

  # Check Node package.json (if exists)
  package_json="$repo/package.json"
  if [[ -f "$package_json" ]]; then
    if grep -Eq '"license"\s*:\s*"Apache-2\.0"' "$package_json"; then
      pass "package.json has Apache-2.0 license"
    elif grep -qi '"license".*MIT' "$package_json"; then
      fail "package.json still has MIT license"
    else
      pass "package.json has no MIT reference"
    fi
  fi

  # Check Rust Cargo.toml (if exists)
  cargo_toml="$repo/Cargo.toml"
  if [[ -f "$cargo_toml" ]]; then
    if grep -Eq 'license\s*=\s*"Apache-2\.0"' "$cargo_toml"; then
      pass "Cargo.toml has Apache-2.0 license"
    elif grep -qi 'license.*MIT' "$cargo_toml"; then
      fail "Cargo.toml still has MIT license"
    else
      pass "Cargo.toml has no MIT reference"
    fi
  fi

  # Check Dockerfiles for OCI label (if exists)
  for dockerfile in "$repo/Dockerfile"*; do
    if [[ -f "$dockerfile" ]]; then
      if grep -q 'org.opencontainers.image.licenses' "$dockerfile"; then
        pass "$(basename "$dockerfile") has OCI license label"
      else
        fail "$(basename "$dockerfile") missing OCI license label"
      fi
    fi
  done

  echo ""
done

echo "=== Verification Summary ==="
if [[ "$FAILURES" -eq 0 ]]; then
  echo "All checks passed!"
  exit 0
else
  echo "Found $FAILURES issues."
  exit 1
fi
