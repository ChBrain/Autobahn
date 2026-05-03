#!/bin/bash
# Setup pre-commit hook for version bump validation

set -e

HOOK_SOURCE=".githooks/pre-commit"
HOOK_TARGET=".git/hooks/pre-commit"

if [ ! -f "$HOOK_SOURCE" ]; then
    echo "✗ Hook source not found: $HOOK_SOURCE"
    exit 1
fi

echo "Installing pre-commit hook..."

# Create hooks directory if needed
mkdir -p .git/hooks

# Copy hook and make executable
cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

echo "✓ Pre-commit hook installed at $HOOK_TARGET"
echo ""
echo "Now run:"
echo "  git config core.hooksPath .githooks"
echo ""
echo "And read: VERSIONING.md for the full workflow"
