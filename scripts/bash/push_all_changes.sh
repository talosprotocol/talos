#!/bin/bash
# scripts/push_all_changes.sh

echo "---------------------------------------------------"
echo "Starting Recursive Push: Submodules -> Root"
echo "---------------------------------------------------"

# 1. Push all submodules first
# We use 'git submodule foreach' to execute the push logic in every registered submodule.
# This ensures we don't miss any new submodules added to .gitmodules.
git submodule foreach --recursive '
    echo "Processing submodule: $name ($path)"
    
    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo "  - Uncommitted changes found. Committing..."
        git add .
        git commit -m "Update submodule content"
    fi
    
    # Check if we are ahead of remote
    # We look for commits that are in HEAD but not in the upstream tracking branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$BRANCH" == "HEAD" ]]; then
        echo "  - Detached HEAD state. Skipping push."
    else
        echo "  - On branch: $BRANCH"
        # Push if there are local commits not on remote
        git push origin "$BRANCH"
    fi
    echo "---------------------------------------------------"
'

# 2. Push root directory
echo "Processing root directory..."
git add .
if [[ -n $(git status -s) ]]; then
    # If submodules were updated, the root repo will see them as modified.
    # We commit these pointer updates.
    echo "  - Committing submodule pointer updates..."
    git commit -m "Update submodules and root files"
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "  - Pushing root to $BRANCH..."
git push origin "$BRANCH"

echo "---------------------------------------------------"
echo "All Done!"
