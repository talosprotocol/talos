#!/bin/bash
# scripts/bash/push_all_changes.sh

export COMMIT_MSG="Fix dead documentation and wiki links

- Transitioned documentation links to point to the dedicated 'talos-docs' repository.
- Ensured all Wiki references correctly target the GitHub Wiki surface.
- Updated root README, CHANGELOG, and internal workflows for consistency."

echo "---------------------------------------------------"
echo "Starting Recursive Push: Submodules -> Root"
echo "---------------------------------------------------"

# 1. Push all submodules first
git submodule foreach --recursive '
    echo "Processing submodule: $name ($path)"
    
    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo "  - Uncommitted changes found. Committing..."
        git add .
        git commit -s -m "$COMMIT_MSG"
    fi
    
    # Check if we are ahead of remote
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$BRANCH" == "HEAD" ]]; then
        echo "  - Detached HEAD state. Skipping push."
    else
        echo "  - On branch: $BRANCH"
        git push origin "$BRANCH"
    fi
    echo "---------------------------------------------------"
'

# 2. Push root directory
echo "Processing root directory..."
git add -u
if [[ -n $(git status -s) ]]; then
    echo "  - Committing root files and submodule pointers..."
    git commit -s -m "$COMMIT_MSG"
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "  - Pushing root to $BRANCH..."
git push origin "$BRANCH"

echo "---------------------------------------------------"
echo "All Done!"
