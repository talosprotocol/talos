#!/bin/bash
# Talos Security Gate: Secret Leak Detector
# Usage: ./secret_leak_gate.sh [path]

TARGET_DIR=${1:-"."}
EXIT_CODE=0

echo "Running Secret Leak Gate in $TARGET_DIR..."

# Patterns to fail on
FAIL_PATTERNS=(
    "(sk-[a-zA-Z0-9]{20,})"
    "(Bearer\s+[a-zA-Z0-9]{20,})"
    "BEGIN (RSA|EC|OPENSSH|ANY)? ?PRIVATE KEY"
    "(AKIA|ASIA)[0-9A-Z]{16}" # AWS Access Key
    "AIza[0-9A-Za-z\\-_]{35}" # Google API Key
    "(TOKEN|KEY|SECRET|PASSWORD)\s*[:=]\s*['\"][a-zA-Z0-9]{15,}['\"]" # Generic high entropy assignments
)

# Exception patterns (allowed)
ALLOWED_PREFIXES=("sk-test-" "Bearer test-")

for pattern in "${FAIL_PATTERNS[@]}"; do
    # Search and filter out allowed prefixes
    matches=$(grep -rIE "$pattern" "$TARGET_DIR" \
        --exclude-dir=".git" \
        --exclude-dir="node_modules" \
        --exclude-dir="venv" \
        --exclude-dir="__pycache__" \
        --exclude="*.log" \
        --exclude="*.example" \
        --exclude="*.md" \
        --exclude=".env*")
    
    if [ -n "$matches" ]; then
        while IFS= read -r line; do
            file_path=$(echo "$line" | cut -d: -f1)
            
            is_allowed=false
            # 1. MUST be in test_vectors/**
            if [[ "$file_path" == *"test_vectors/"* ]]; then
                # 2. MUST match an allowed placeholder prefix
                for prefix in "${ALLOWED_PREFIXES[@]}"; do
                    if [[ "$line" == *"$prefix"* ]]; then
                        is_allowed=true
                        break
                    fi
                done
            fi
            
            if [ "$is_allowed" = false ]; then
                echo "❌ Secret Leak Detected in $file_path: $line"
                EXIT_CODE=1
            fi
        done <<< "$matches"
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No real secrets detected."
else
    echo "❌ Secret Leak Gate Failed."
fi

exit $EXIT_CODE
