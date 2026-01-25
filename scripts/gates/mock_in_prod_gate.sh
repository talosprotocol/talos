#!/bin/bash
# Talos Security Gate: Mock-in-Prod Detector
# Usage: ./mock_in_prod_gate.sh [path]

TARGET_DIR=${1:-"."}
EXIT_CODE=0

echo "Running Mock-in-Prod Gate in $TARGET_DIR..."

# Define restricted patterns (Definitions or Imports of Mocks/Fakes)
# We look for "class Mock", "def mock", "class Fake", "import Mock", etc.
FAIL_PATTERNS=(
    "class Mock"
    "class Fake"
    "def mock_"
    "def fake_"
    "import .*Mock"
    "from .* import .*Mock"
    "MOCK_[A-Z0-9_]+"
)

# Define directories/files that ARE ALLOWED to have mocks
ALLOWED_PATHS=(
    "*/tests/*"
    "*/test/*"
    "*_test.py"
    "*.test.ts"
    "*.spec.ts"
    "*/__mocks__/*"
    "*/conftest.py"
    "*/scripts/*"
    "*/conformance/*"
)

# 1. Mandatory Graph Check for known entrypoints
ENTRYPOINTS=(
    "services/ai-gateway/app/main.py"
    "services/mcp-connector/src/main.py"
    "services/audit/src/main.py"
)

GATE_DIR=$(dirname "$0")

for ep in "${ENTRYPOINTS[@]}"; do
    if [ -f "$ep" ]; then
        python3 "$GATE_DIR/check_import_graph.py" "$ep" "$TARGET_DIR"
        if [ $? -ne 0 ]; then
            EXIT_CODE=1
        fi
    fi
done

# 2. General Static Check (Grep) for Definitions in Production Paths
for pattern in "${FAIL_PATTERNS[@]}"; do
    matches=$(grep -rEi "$pattern" "$TARGET_DIR" \
        --exclude-dir=".git" \
        --exclude-dir="node_modules" \
        --exclude-dir="venv" \
        --exclude-dir="__pycache__" \
        --exclude-dir="tests" \
        --exclude-dir="test" \
        --exclude-dir="reports" \
        --exclude-dir="docs" \
        --exclude-dir="scripts" \
        --exclude-dir="wiki" \
        --exclude-dir="examples" \
        --exclude-dir="talos-examples" \
        --exclude-dir="talos-dashboard" \
        --exclude-dir="conformance" \
        --exclude-dir="submodules" \
        --exclude="*_test.py" \
        --exclude="*.test.ts" \
        --exclude="*.spec.ts" \
        --exclude="*.md")
    
    if [ -n "$matches" ]; then
        echo "❌ Potential Mock/Fake definition detected in production path:"
        echo "$matches"
        EXIT_CODE=1
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No mocks detected in production paths."
else
    echo "❌ Mock-in-Prod Gate Failed."
    echo "Rule: Mocks/Fakes are ONLY allowed in tests/ or test directories."
fi

exit $EXIT_CODE
