#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Submodules list as defined in the plan
SUBMODULE_PATHS = [
    "contracts",
    "core",
    "sdks/python",
    "sdks/typescript",
    "services/ai-gateway",
    "services/audit",
    "services/mcp-connector",
    "site/dashboard",
    "examples",
    "docs",
    "sdks/go",
    "sdks/java",
    "site/marketing",
    "services/gateway",
    "services/ai-chat-agent",
    "services/aiops",
    "services/governance-agent",
    "services/ucp-connector",
    "sdks/rust",
    "tools/talos-tui",
    "site/configuration-dashboard",
]

# Required files/directories in each .agent folder
REQUIRED_FILES = [
    ".agent/README.md",
    ".agent/task.md",
    ".agent/context.md",
    ".agent/agents/.gitkeep",
    ".agent/planning/.gitkeep",
    ".agent/workflows/.gitkeep",
]

def main() -> int:
    root = Path.cwd()
    missing: list[str] = []
    empty_context: list[str] = []

    print(f"Verifying .agent layout for {len(SUBMODULE_PATHS)} submodules...")

    for rel in SUBMODULE_PATHS:
        base = root / rel
        # If the submodule directory itself doesn't exist, we note it.
        # Ideally, in a fresh checkout, they might be empty directories if not initialized, 
        # but here we expect the directory structure to exist.
        if not base.exists():
            missing.append(f"{rel} (module path missing)")
            continue
            
        for rf in REQUIRED_FILES:
            p = base / rf
            if not p.exists():
                missing.append(f"{rel}/{rf}")
        
        ctx = base / ".agent/context.md"
        # Check if context.md exists and is not empty
        if ctx.exists():
            content = ctx.read_text(encoding="utf-8").strip()
            if not content:
                empty_context.append(str(ctx))
                
    if missing:
        print("ERROR: missing required .agent artifacts:", file=sys.stderr)
        for m in missing:
            print(f"- {m}", file=sys.stderr)
            
    if empty_context:
        print("ERROR: empty context.md:", file=sys.stderr)
        for c in empty_context:
            print(f"- {c}", file=sys.stderr)

    if missing or empty_context:
        print("\nVerification FAILED.")
        return 2

    print("OK: .agent layout verified for all configured modules")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
