#!/bin/bash
set -e

# Dynamically runs python scripts locally utilizing 3.11-slim containers
# This ensures compatibility with Python 3.10+ syntax and types
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
echo "Executing Python suite using Ephemeral Docker Python 3.11 Proxy..."

REPO_ROOT=$(git rev-parse --show-toplevel)
REL_PATH=${PWD#$REPO_ROOT/}

# Execute inside container with dynamic dependency installation
docker run --rm \
  --network host \
  -v "$REPO_ROOT":/workspace \
  -w "/workspace/$REL_PATH" \
  python:3.11-slim \
  sh -c 'apt-get update && apt-get install -y git && \
    ( [ -f requirements.txt ] && pip install -r requirements.txt || true ) && \
    ( [ -f pyproject.toml ] && pip install . || true ) && \
    pip install pytest pytest-asyncio pytest-cov httpx || true && \
    "$@"' -- "$@"
