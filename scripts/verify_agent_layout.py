#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from agent_sync import load_submodule_entries

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
    
    # 1. Root Precondition Check
    SENTINEL_ROLE = "agents/engineering/backend-architect.md"
    SENTINEL_WORKFLOW = "workflows/README.md"
    
    root_agent = root / ".agent"
    if not (root_agent / SENTINEL_ROLE).exists():
        print(f"ERROR: Root sentinel role missing: .agent/{SENTINEL_ROLE}", file=sys.stderr)
        return 2
    if not (root_agent / SENTINEL_WORKFLOW).exists():
        print(f"ERROR: Root sentinel workflow missing: .agent/{SENTINEL_WORKFLOW}", file=sys.stderr)
        return 2

    missing: list[str] = []
    empty_context: list[str] = []
    missing_sentinels: list[str] = []
    optional_missing: list[str] = []
    submodules = load_submodule_entries()

    print(f"Verifying .agent layout for {len(submodules)} configured submodules...")

    for entry in submodules:
        rel = entry["new_path"]
        base = root / rel
        if not base.exists():
            if entry["required"]:
                missing.append(f"{rel} (module path missing)")
            else:
                optional_missing.append(rel)
            continue
            
        # Check basic layout
        for rf in REQUIRED_FILES:
            p = base / rf
            if not p.exists():
                missing.append(f"{rel}/{rf}")
        
        # Check context
        ctx = base / ".agent/context.md"
        if ctx.exists():
            content = ctx.read_text(encoding="utf-8").strip()
            if not content:
                empty_context.append(str(ctx))

        # Check Sentinels (Proof of sync)
        if not (base / ".agent" / SENTINEL_ROLE).exists():
            missing_sentinels.append(f"{rel}/.agent/{SENTINEL_ROLE}")
        if not (base / ".agent" / SENTINEL_WORKFLOW).exists():
            missing_sentinels.append(f"{rel}/.agent/{SENTINEL_WORKFLOW}")

    if missing:
        print("FAIL: missing required .agent artifacts:", file=sys.stderr)
        for m in missing:
            print(f"- {m}", file=sys.stderr)
            
    if empty_context:
        print("FAIL: empty context.md:", file=sys.stderr)
        for c in empty_context:
            print(f"- {c}", file=sys.stderr)

    if missing_sentinels:
        print("FAIL: missing sentinel files (sync incomplete):", file=sys.stderr)
        for s in missing_sentinels:
            print(f"- {s}", file=sys.stderr)

    if optional_missing:
        print("SKIP: optional module paths not present:", file=sys.stderr)
        for rel in optional_missing:
            print(f"- {rel}", file=sys.stderr)

    if missing or empty_context or missing_sentinels:
        print("\nVerification FAILED.")
        return 2

    print("OK: .agent layout and content verified for all configured modules")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
