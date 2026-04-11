#!/bin/bash
# scripts/bash/pull_all_changes.sh
# Pulls latest changes for the root repository and all submodules recursively.

set -e

echo "---------------------------------------------------"
echo "Starting Recursive Pull: Root -> Submodules"
echo "---------------------------------------------------"

# 1. Pull root directory
echo "Processing root directory..."
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" == "HEAD" ]]; then
    echo "  - Warning: Detached HEAD state. Skipping root pull."
else
    echo "  - Pulling root from origin/$BRANCH..."
    git pull origin "$BRANCH"
fi

# 2. Sync and Update submodules to pinned versions
echo "Syncing and updating submodules..."
git submodule sync --recursive
git submodule update --init --recursive

# 3. Pull latest for submodules that are on tracking branches
# This ensures submodules are not just updated to root pointers, but actually 
# get the latest commits from their respective origin branches.
echo "---------------------------------------------------"
echo "Pulling latest for submodules..."
git submodule foreach --recursive '
    echo "Processing submodule: $name ($path)"
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$BRANCH" == "HEAD" ]]; then
        echo "  - Detached HEAD. Updating to pinned remote commit..."
        git fetch origin
        # Note: we dont pull if detached, as pull requires a branch.
        # But submodule update above already handled pinned alignment.
    else
        echo "  - On branch: $BRANCH. Pulling latest from origin..."
        git pull origin "$BRANCH"
    fi
    echo "---------------------------------------------------"
'

echo "All Done!"
