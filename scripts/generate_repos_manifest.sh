#!/usr/bin/env bash
# generate_repos_manifest.sh
# Generates and validates the repos manifest for relicensing.
# Uses relative paths for portability across environments.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPOS_DIR="$ROOT_DIR/deploy/repos"
MANIFEST_FILE="$SCRIPT_DIR/repos_manifest.txt"
GENERATED_FILE="$SCRIPT_DIR/repos_manifest.generated.txt"

# Single source of truth for expected count
EXPECTED_REPO_COUNT=17

fail() { echo "ERROR: $*" >&2; exit 1; }
warn() { echo "WARN: $*" >&2; }

echo "Generating repos manifest..."

# Use relative paths for portability
# Start with root (represented as ".")
repos=(".")

# Add deploy/repos/* children that are git repos (as relative paths)
if [[ -d "$REPOS_DIR" ]]; then
  while IFS= read -r -d '' dir; do
    if [[ -d "$dir/.git" ]] || git -C "$dir" rev-parse --git-dir &>/dev/null 2>&1; then
      # Convert to relative path from ROOT_DIR
      rel_path="${dir#$ROOT_DIR/}"
      repos+=("$rel_path")
    else
      warn "Skipping non-git directory: $dir"
    fi
  done < <(find "$REPOS_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
fi

# Write generated manifest
printf '%s\n' "${repos[@]}" > "$GENERATED_FILE"

# Validation: no duplicates
sorted_repos=$(printf '%s\n' "${repos[@]}" | sort)
unique_repos=$(printf '%s\n' "${repos[@]}" | sort -u)
if [[ "$sorted_repos" != "$unique_repos" ]]; then
  fail "Duplicate entries detected in manifest"
fi

# Validation: all paths exist (resolve relative to ROOT_DIR)
for repo in "${repos[@]}"; do
  if [[ "$repo" == "." ]]; then
    [[ -d "$ROOT_DIR" ]] || fail "Root path does not exist: $ROOT_DIR"
  else
    [[ -d "$ROOT_DIR/$repo" ]] || fail "Path does not exist: $repo"
  fi
done

# Validation: count
actual_count=${#repos[@]}
if [[ "$actual_count" -ne "$EXPECTED_REPO_COUNT" ]]; then
  fail "Expected $EXPECTED_REPO_COUNT repos, found $actual_count"
fi

echo "Generated manifest with $actual_count repos:"
cat "$GENERATED_FILE"

# Check if committed manifest exists and differs
if [[ -f "$MANIFEST_FILE" ]]; then
  if ! diff -q "$MANIFEST_FILE" "$GENERATED_FILE" &>/dev/null; then
    echo ""
    echo "WARNING: Committed manifest differs from generated!"
    echo "Diff:"
    diff "$MANIFEST_FILE" "$GENERATED_FILE" || true
    echo ""
    echo "To update, run: cp $GENERATED_FILE $MANIFEST_FILE"
    exit 1
  else
    echo "Manifest is up to date."
  fi
else
  echo "No committed manifest found. Creating..."
  cp "$GENERATED_FILE" "$MANIFEST_FILE"
  echo "Created: $MANIFEST_FILE"
fi

echo "Done."
