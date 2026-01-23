#!/bin/bash
# scripts/push_all_changes.sh

# List of submodules/directories to check
DIRS=(
"contracts"
"core"
"docs"
"examples"
"sdks/go"
"sdks/java"
"sdks/python"
"sdks/rust"
"sdks/typescript"
"services/ai-chat-agent"
"services/ai-gateway"
"services/aiops"
"services/audit"
"services/gateway"
"services/governance-agent"
"services/mcp-connector"
"services/ucp-connector"
"site/dashboard"
"site/marketing"
)

ROOT_DIR=$(pwd)

for dir in "${DIRS[@]}"; do
  echo "---------------------------------------------------"
  echo "Processing $dir..."
  if [ -d "$dir" ]; then
    cd "$dir"
    
    # Get current branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "Current branch: $BRANCH"

    # Check for changes
    if [[ -n $(git status -s) ]]; then
      echo "Changes found in $dir. Committing and pushing..."
      git add .
      git commit -m "Update $dir content"
      git push origin "$BRANCH"
    elif [[ -n $(git status | grep "ahead of") ]]; then
       echo "Local commits found in $dir. Pushing..."
       git push origin "$BRANCH"
    else
      echo "No changes in $dir."
    fi
    cd "$ROOT_DIR"
  else
    echo "Directory $dir does not exist."
  fi
done

echo "---------------------------------------------------"
echo "Processing root directory..."
git add .
if [[ -n $(git status -s) ]]; then
    git commit -m "Update submodules and root files"
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    git push origin "$BRANCH"
else
    echo "No changes in root directory to commit."
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    git push origin "$BRANCH"
fi
