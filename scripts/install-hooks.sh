#!/usr/bin/env bash
# =============================================================================
# Install Git Hooks
# =============================================================================
# Installs pre-commit and pre-push validation hooks.
#
# USAGE:
#   bash scripts/install-hooks.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$ROOT_DIR/.git/hooks"

echo "Installing Talos Git Hooks..."
echo ""

# Make scripts executable
chmod +x "$SCRIPT_DIR/pre-commit-validate.sh"
chmod +x "$SCRIPT_DIR/pre-push-validate.sh"

# Install pre-commit hook
if [[ -f "$HOOKS_DIR/pre-commit" ]]; then
    echo "⚠️  Existing pre-commit hook found, backing up..."
    mv "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-commit.backup.$(date +%s)"
fi
ln -sf "../../scripts/pre-commit-validate.sh" "$HOOKS_DIR/pre-commit"
echo "✅ Installed pre-commit hook"

# Install pre-push hook  
if [[ -f "$HOOKS_DIR/pre-push" ]] && [[ ! -L "$HOOKS_DIR/pre-push" ]]; then
    echo "⚠️  Existing pre-push hook found, backing up..."
    mv "$HOOKS_DIR/pre-push" "$HOOKS_DIR/pre-push.backup.$(date +%s)"
fi
ln -sf "../../scripts/pre-push-validate.sh" "$HOOKS_DIR/pre-push"
echo "✅ Installed pre-push hook"

echo ""
echo "=========================================="
echo "Git hooks installed successfully!"
echo ""
echo "Hooks will run automatically on:"
echo "  - git commit  → pre-commit-validate.sh"
echo "  - git push    → pre-push-validate.sh"
echo ""
echo "To skip hooks (emergency only):"
echo "  git commit --no-verify"
echo "  git push --no-verify"
echo "=========================================="
