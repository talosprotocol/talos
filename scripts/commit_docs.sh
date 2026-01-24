#!/bin/bash

# Commit CLAUDE.md files in all submodules
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR/.."
cd "$ROOT_DIR"

submodules=(
  "contracts"
  "core"
  "sdks/python"
  "sdks/typescript"
  "sdks/go"
  "sdks/rust"
  "sdks/java"
  "services/ai-gateway"
  "services/audit"
  "services/mcp-connector"
  "site/dashboard"
  "site/marketing"
  "examples"
  "docs"
  "services/gateway"
  "services/ai-chat-agent"
  "services/aiops"
  "services/governance-agent"
  "services/ucp-connector"
)

echo "Adding and committing CLAUDE.md files in submodules..."

for submodule in "${submodules[@]}"; do
  if [[ -d "$submodule" ]]; then
    echo "Processing $submodule..."
    cd "$submodule"
    if [[ -f "CLAUDE.md" ]]; then
      git add CLAUDE.md AGENTS.md
      git commit -m "Add CLAUDE.md guidance file for Claude Code instances

Provides essential context for Claude Code when working with this submodule:
- Repository purpose and architecture
- Common development commands
- Key components and integration points
- Language-specific patterns
- Testing procedures" 2>/dev/null || echo "No changes to commit in $submodule"
    else
      echo "No CLAUDE.md found in $submodule"
    fi
    cd ..
  else
    echo "Directory $submodule not found"
  fi
done

echo "Done processing submodules."
