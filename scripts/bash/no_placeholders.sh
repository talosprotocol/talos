#!/bin/bash
# scripts/no_placeholders.sh
# Fails if "placeholder", "TODO(STOPSHIP)", or "FIXME(STOPSHIP)" are found in non-excluded files.

echo "🔍 Scanning for placeholders and stop-ship markers..."

# Define excluded directories/patterns
# We use recursive wildcards to be safe
EXCLUDES=(
    "docs/**" 
    "node_modules/**" 
    "dist/**" 
    "build/**" 
    ".venv/**" 
    "__pycache__/**" 
    "**/tests/**"
    ".git/**"
    ".gemini/**"
    "site/**"
    "examples/**"
    "services/ai-gateway/**"
    "tools/**"
    "tests/**"
    "src/core/**"
    "scripts/**"
    "**/*.md"
    "**/*.json"
    "**/*.yaml"
    "**/*.yml"
)

# Construct rg exclude flags
EXCLUDE_FLAGS=""
for dir in "${EXCLUDES[@]}"; do
    EXCLUDE_FLAGS+=" --glob !${dir}"
done

# Run search
# We search for:
# - placeholder (case insensitive) -> but exclude lines starting with # or //
# - TODO(STOPSHIP)
# - FIXME(STOPSHIP)

# We pipe rg to grep -v to filter out comments and the script itself.
if rg -i -n "placeholder|TODO\(STOPSHIP\)|FIXME\(STOPSHIP\)" . $EXCLUDE_FLAGS | grep -v -E "scripts/no_placeholders.sh" | grep -v -E ":\s*[#//]"; then
    echo "❌ FAILED: Found placeholders or stop-ship markers in codebase (excluding comments)."
    exit 1
else
    echo "✅ SUCCESS: No placeholders found (excluding comments)."
    exit 0
fi
