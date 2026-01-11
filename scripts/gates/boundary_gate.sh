#!/bin/bash
# Talos Security Gate: Boundary Detector
# Usage: ./boundary_gate.sh [repo_root]

REPO_ROOT=${1:-"."}
EXIT_CODE=0

echo "Running Boundary Gate in $REPO_ROOT..."

# Define sensitive absolute path parts that should never be in production code
# (Except in CI configuration or scripts)
FORBIDDEN_PATH_PARTS=(
    "deploy/repos/"
    "blockchain-mcp-security"
)

# Relative path deep-links (going above the repo root more than necessary)
# Usually, a repo shouldn't need to go up more than its own structure.
# If it's a submodule, it definitely shouldn't go up to sister submodules.
FORBIDDEN_RELATIVE_IMPORTS=(
    "\.\./\.\./talos-"
)

# Exception directories (where these might be okay, like scripts or CI)
ALLOWED_PATHS=(
    "*/scripts/*"
    "*/.github/*"
    "*/tests/*"
)

EXCLUDE_PATTERNS=(
    --exclude-dir=".git"
    --exclude-dir="node_modules"
    --exclude-dir="venv"
    --exclude-dir="__pycache__" \
    --exclude-dir=".idea" \
    --exclude-dir=".next" \
    --exclude-dir=".agent" \
    --exclude-dir="tools" \
    --exclude-dir="legacy" \
    --exclude-dir=".git" \
    --exclude-dir="dist" \
    --exclude-dir="build" \
    --exclude-dir="target" \
    --exclude-dir=".venv" \
    --exclude-dir="reports" \
    --exclude="*.log" \
    --exclude="*.pyc" \
    --exclude="*.md" \
    --exclude="*.txt" \
    --exclude="*.js.map" \
    --exclude="package-lock.json" \
    --exclude="docker-compose.yml" \
    --exclude=".gitmodules" \
    --exclude=".dockerignore" \
    --exclude="run_all.sh" \
    --exclude=".git" \
    --exclude="provenance_report.txt" \
    --exclude="third_party_dirs.txt"
)

# 1. Check for relative deep-links
matches=$(grep -rIE "\.\./\.\./talos-" "$REPO_ROOT" "${EXCLUDE_PATTERNS[@]}")
if [ -n "$matches" ]; then
    while IFS= read -r line; do
        file_path=$(echo "$line" | cut -d: -f1)
        is_allowed=false
        for allowed in "${ALLOWED_PATHS[@]}"; do
            [[ "$file_path" == $allowed ]] && is_allowed=true && break
        done
        if [ "$is_allowed" = false ]; then
            echo "❌ Forbidden cross-repo relative import: $line"
            EXIT_CODE=1
        fi
    done <<< "$matches"
fi

# 2. Check for absolute path references to other repos
for part in "${FORBIDDEN_PATH_PARTS[@]}"; do
    matches=$(grep -rIE "$part" "$REPO_ROOT" "${EXCLUDE_PATTERNS[@]}")
    if [ -n "$matches" ]; then
        while IFS= read -r line; do
            file_path=$(echo "$line" | cut -d: -f1)
            is_allowed=false
            for allowed in "${ALLOWED_PATHS[@]}"; do
                [[ "$file_path" == $allowed ]] && is_allowed=true && break
            done
            if [ "$is_allowed" = false ]; then
                echo "❌ Forbidden cross-repo path reference: $line"
                EXIT_CODE=1
            fi
        done <<< "$matches"
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No cross-repo boundary violations detected."
else
    echo "❌ Boundary Gate Failed."
fi

exit $EXIT_CODE
