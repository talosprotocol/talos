#!/bin/bash
set -e

# Dynamically runs npm node scripts locally utilizing vanilla alpine containers to supply NPM runtime across mapped workspace
# This prevents pollution on host OS where NPM/Node isn't maintained natively
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
echo "Executing Javascript/UI suite using Ephemeral Docker Node Proxy..."

# Mount entire workspace logic so that local symlinks (like @talosprotocol/contracts -> file:../../) remain valid.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REL_PATH=${PWD#$REPO_ROOT/}

CMD="$@"
if [ -z "$CMD" ]; then
    CMD="npm install && npm test"
else
    # If custom command, still ensure dependencies are installed unless already specified
    if [[ ! "$CMD" == *"npm install"* ]] && [ -f "package.json" ]; then
        CMD="npm install && $CMD"
    fi
fi

IMAGE="node:20"
if [[ "$CMD" == *"playwright"* ]]; then
    IMAGE="mcr.microsoft.com/playwright:v1.49.1-jammy"
fi

docker run --rm \
  --network host \
  -v "$REPO_ROOT":/workspace \
  -w "/workspace/$REL_PATH" \
  $IMAGE \
  sh -c "$CMD" -- "$@"
