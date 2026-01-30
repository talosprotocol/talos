#!/usr/bin/env python3
import os
import shutil
import re
from pathlib import Path

# Paths
ROOT_DIR = Path("/Users/nileshchakraborty/workspace/talos")
DOCS_DIR = ROOT_DIR / "docs"
WIKI_REPO_DIR = ROOT_DIR / "temp_wiki_sync"
WIKI_PAGES_DIR = WIKI_REPO_DIR / "wiki"

# Ensure wiki pages dir exists
WIKI_PAGES_DIR.mkdir(parents=True, exist_ok=True)

def to_wiki_filename(path_obj: Path) -> str:
    """
    Transforms a relative path like 'getting-started/quickstart.md'
    into 'Quickstart.md' or similar Pascal-Case-With-Hyphens.
    """
    # Special cases
    if path_obj.name == "README-Home.md":
        return "Home.md"
    if path_obj.name == "README.md" and path_obj.parent.name == "docs":
        return "_Footer.md" # Or mapping to another name
    
    # Generic transformation: PascalCase the name parts
    stem = path_obj.stem
    # Replace separators with spaces, capitalize, then put hyphens back
    # But usually wikis prefer simple names if possible.
    # Looking at existing wiki: Architecture.md, A2A-Channels.md
    
    # Simple rule: replace '-' with ' ' for title case, then put '-' back
    parts = stem.replace('-', ' ').split()
    pascal_parts = [p.capitalize() for p in parts]
    return "-".join(pascal_parts) + ".md"

def sync_docs():
    print(f"Syncing docs from {DOCS_DIR} to {WIKI_PAGES_DIR}...")
    
    # 1. Walk through docs/
    for root, dirs, files in os.walk(DOCS_DIR):
        # Skip hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if not file.endswith(".md"):
                continue
                
            src_path = Path(root) / file
            rel_path = src_path.relative_to(DOCS_DIR)
            
            # Skip templates or internal docs if necessary
            if "templates" in str(rel_path) or ".agent" in str(rel_path):
                continue
                
            wiki_name = to_wiki_filename(rel_path)
            dest_path = WIKI_PAGES_DIR / wiki_name
            
            print(f"  Mapping {rel_path} -> {wiki_name}")
            shutil.copy2(src_path, dest_path)

    # 2. Sync Root Files
    root_mappings = {
        "docs/research/whitepaper.md": "WHITEPAPER.md",
        "docs/research/roadmap.md": "ROADMAP_v2.md",
        "AGENTS.md": "AGENTS.md",
        "LICENSE": "LICENSE",
        "NOTICE": "NOTICE"
    }
    
    for src_rel, dest_name in root_mappings.items():
        src_path = ROOT_DIR / src_rel
        dest_path = WIKI_REPO_DIR / dest_name
        if src_path.exists():
            print(f"  Syncing root file {src_rel} -> {dest_name}")
            shutil.copy2(src_path, dest_path)
        else:
            print(f"  Warning: Root file {src_rel} not found")

    # 3. Handle specific transformations inside files (link updating)
    # This is complex, but for now we rely on the fact that GitHub Wiki
    # handles [[Page-Name]] or [Link](Page-Name) correctly in a flattened space.

if __name__ == "__main__":
    sync_docs()
    print("Done.")
