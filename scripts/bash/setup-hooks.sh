#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🛠️  Setting up git hooks for talos (root)..."

cd "$REPO_ROOT"
mkdir -p .githooks

# Create pre-commit wrapper
cat > .githooks/pre-commit <<EOF
#!/bin/sh
bash scripts/pre-commit
EOF
chmod +x .githooks/pre-commit

# Create pre-push wrapper (calls existing pre-push-validate.sh)
cat > .githooks/pre-push <<EOF
#!/bin/sh
bash scripts/pre-push-validate.sh
EOF
chmod +x .githooks/pre-push

# Set hooks path
git config core.hooksPath .githooks

echo "✅ Hooks installed! (core.hooksPath set to .githooks)"
echo "   - Pre-commit: scripts/pre-commit"
echo "   - Pre-push: scripts/pre-push-validate.sh"
