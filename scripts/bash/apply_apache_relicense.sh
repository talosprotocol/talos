#!/usr/bin/env bash
# apply_apache_relicense.sh
# Deterministic script to apply Apache 2.0 license to all repos in the manifest.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST_FILE="$SCRIPT_DIR/repos_manifest.txt"
LICENSE_FILE="$ROOT_DIR/LICENSE"
NOTICE_FILE="$ROOT_DIR/NOTICE"
THIRD_PARTY_DIRS_FILE="$SCRIPT_DIR/third_party_dirs.txt"
SUMMARY_FILE="$SCRIPT_DIR/relicense_summary.md"

DRY_RUN=false

usage() {
  echo "Usage: $0 [--dry-run | --apply]"
  echo "  --dry-run: Show what would be changed without making changes"
  echo "  --apply:   Apply all changes"
  exit 1
}

[[ $# -eq 1 ]] || usage
case "$1" in
  --dry-run) DRY_RUN=true ;;
  --apply) DRY_RUN=false ;;
  *) usage ;;
esac

fail() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[INFO] $*"; }

[[ -f "$MANIFEST_FILE" ]] || fail "Manifest not found: $MANIFEST_FILE"
[[ -f "$LICENSE_FILE" ]] || fail "Root LICENSE not found: $LICENSE_FILE"
[[ -f "$NOTICE_FILE" ]] || fail "Root NOTICE not found: $NOTICE_FILE"

# Load third-party dirs to skip
third_party_dirs=()
if [[ -f "$THIRD_PARTY_DIRS_FILE" ]]; then
  while IFS= read -r line; do
    # Extract path from the line (format: "  [THIRD-PARTY] /path/to/dir")
    dir=$(echo "$line" | sed 's/.*\[THIRD-PARTY\] //')
    [[ -n "$dir" ]] && third_party_dirs+=("$dir")
  done < "$THIRD_PARTY_DIRS_FILE"
fi

is_third_party() {
  local path="$1"
  for tp in "${third_party_dirs[@]:-}"; do
    [[ -n "$tp" && "$path" == "$tp"* ]] && return 0
  done
  return 1
}

# Initialize summary
echo "# Relicense Summary" > "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"
echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$SUMMARY_FILE"
echo "Mode: $([[ "$DRY_RUN" == true ]] && echo "DRY-RUN" || echo "APPLY")" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

# Read repos
repos=()
while IFS= read -r line; do
  [[ -n "$line" ]] && repos+=("$line")
done < "$MANIFEST_FILE"

for rel_repo in "${repos[@]}"; do
  # Resolve relative path to absolute
  if [[ "$rel_repo" == "." ]]; then
    repo="$ROOT_DIR"
  else
    repo="$ROOT_DIR/$rel_repo"
  fi

  log "Processing: $rel_repo"
  echo "## $rel_repo" >> "$SUMMARY_FILE"

  # Skip root (already handled)
  if [[ "$repo" == "$ROOT_DIR" ]]; then
    echo "- Skipped (root already updated)" >> "$SUMMARY_FILE"
    continue
  fi

  # Copy LICENSE
  target_license="$repo/LICENSE"
  if [[ "$DRY_RUN" == true ]]; then
    echo "- [DRY-RUN] Would create/update: LICENSE" >> "$SUMMARY_FILE"
  else
    cp "$LICENSE_FILE" "$target_license"
    echo "- Created/updated: LICENSE" >> "$SUMMARY_FILE"
  fi

  # Copy NOTICE
  target_notice="$repo/NOTICE"
  if [[ "$DRY_RUN" == true ]]; then
    echo "- [DRY-RUN] Would create/update: NOTICE" >> "$SUMMARY_FILE"
  else
    cp "$NOTICE_FILE" "$target_notice"
    echo "- Created/updated: NOTICE" >> "$SUMMARY_FILE"
  fi

  # Update README.md
  for readme in "$repo/README.md" "$repo/README.MD"; do
    if [[ -f "$readme" ]]; then
      if [[ "$DRY_RUN" == true ]]; then
        echo "- [DRY-RUN] Would update LICENSE section in: $(basename "$readme")" >> "$SUMMARY_FILE"
      else
        # Check if ## License section exists
        if grep -q "^## License" "$readme"; then
          # Replace license section (everything from "## License" to next "##" or end)
          # Use sed to replace the license section
          sed -i '' '/^## License$/,/^## [^L]/{ /^## License$/{ N; s|## License.*|## License\n\nLicensed under the Apache License 2.0. See [LICENSE](LICENSE).\n|; }; }' "$readme" 2>/dev/null || \
          sed -i '/^## License$/,/^## [^L]/{ /^## License$/{ N; s|## License.*|## License\n\nLicensed under the Apache License 2.0. See [LICENSE](LICENSE).\n|; }; }' "$readme" 2>/dev/null || true
        else
          # Append license section
          echo "" >> "$readme"
          echo "## License" >> "$readme"
          echo "" >> "$readme"
          echo "Licensed under the Apache License 2.0. See [LICENSE](LICENSE)." >> "$readme"
        fi
        echo "- Updated: $(basename "$readme")" >> "$SUMMARY_FILE"
      fi
    fi
  done

  echo "" >> "$SUMMARY_FILE"
done

log "Summary written to: $SUMMARY_FILE"
if [[ "$DRY_RUN" == true ]]; then
  log "DRY-RUN complete. No changes made."
else
  log "APPLY complete. Changes applied."
fi
