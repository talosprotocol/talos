#!/bin/bash
# Talos Security Gate: Canonicalization Detector
# Usage: ./canonicalization_gate.sh [repo_root]

REPO_ROOT=${1:-"."}
REPO_NAME=$(basename "$REPO_ROOT")
EXIT_CODE=0

echo "Running Canonicalization Gate in $REPO_ROOT ($REPO_NAME)..."

# Skip check if we are in the source-of-truth repos
if [[ "$REPO_NAME" == "talos-contracts" || "$REPO_NAME" == "talos-core-rs" ]]; then
    echo "✅ Repo is source-of-truth for canonicalization. Skipping check."
    exit 0
fi

# Patterns that suggest re-implementation of protocol rules
# 1. Manual base64url replacements
# 2. Manual JSON sorting (often used for canonical signatures)
# 3. Direct Ed25519 library imports (without using Talos SDK/Core)
RISKY_PATTERNS=(
    "\.replace(['\"]-['\"], ['\"]_['\"])\.replace(['\"]/['\"], ['\"]_['\"])" # base64 -> base64url manual
    "urllib\.parse\.quote" # Potential manual encoding
    "sort_keys=True" # Manual JSON sorting instead of using Talos canonical lib
    "sorted\(.*\.keys\(\)\)" # Manual key sorting
    "ed25519\." # Direct Ed25519 usage (should use Talos primitives)
    "nacl\.signing" # Direct Libsodium usage
)

# Exception paths
ALLOWED_PATHS=(
    "*/tests/*"
    "*/scripts/*"
    "*/crypto/*"
    "*/core/*"
    "*/encoding/*"
    "*/src/index.ts"
)

for pattern in "${RISKY_PATTERNS[@]}"; do
    matches=$(grep -rIE "$pattern" "$REPO_ROOT" \
        --exclude-dir=".git" \
        --exclude-dir="node_modules" \
        --exclude-dir="venv" \
        --exclude-dir="__pycache__" \
        --exclude-dir="reports" \
        --exclude-dir="docs" \
        --exclude-dir="scripts" \
        --exclude-dir="wiki" \
        --exclude-dir="dist" \
        --exclude-dir="bin" \
        --exclude-dir="out" \
        --exclude-dir="pkg" \
        --exclude-dir="src" \
        --exclude-dir="legacy" \
        --exclude-dir="examples" \
        --exclude-dir="talos-examples" \
        --exclude-dir=".next" \
        --exclude-dir=".segments" \
        --exclude="*.md" \
        --exclude="*.log" \
        --exclude="*.json" \
        --exclude="*.txt" \
        --exclude="*.rsc" \
        --exclude="*.html" \
        --exclude="*.tsbuildinfo")
    if [ -n "$matches" ]; then
        while IFS= read -r line; do
            file_path=$(echo "$line" | cut -d: -f1)
            is_allowed=false
            for allowed in "${ALLOWED_PATHS[@]}"; do
                [[ "$file_path" == $allowed ]] && is_allowed=true && break
            done
            if [ "$is_allowed" = false ]; then
                echo "⚠️  Possible protocol re-implementation detected: $line"
                echo "   -> Please use official canonicalization from talos-contracts or talos-core-rs."
                EXIT_CODE=1
            fi
        done <<< "$matches"
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No protocol re-implementations detected."
else
    echo "❌ Canonicalization Gate Failed."
fi

exit $EXIT_CODE
