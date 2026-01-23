import os
import re
from pathlib import Path

def check_wikilinks(docs_dir):
    files = list(Path(docs_dir).glob("*.md"))
    file_bases = {f.stem for f in files}
    
    broken = []
    
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    for f in files:
        content = f.read_text()
        links = link_pattern.findall(content)
        for label, target in links:
            # Skip http/https links
            if target.startswith('http'):
                continue
            
            # Skip fragment only
            if target.startswith('#'):
                continue
            
            # Remove fragment for check
            target_base = target.split('#')[0]
            
            if not target_base:
                continue
                
            # Check if target exists as a file or stem
            if target_base not in file_bases and not (f.parent / target_base).exists():
                broken.append((f.name, label, target))
                
    return broken

if __name__ == "__main__":
    broken_links = check_wikilinks("docs/wiki")
    if broken_links:
        print("Found broken links:")
        for source, label, target in broken_links:
            print(f"{source}: [{label}]({target})")
    else:
        print("No broken internal links found.")
