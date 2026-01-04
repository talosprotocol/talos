#!/usr/bin/env python3
import sys
import re
from pathlib import Path

REQUIRED_SECTIONS = [
    r"^# .+",
    r"^\*\*Repo Role\*\*: .+",
    r"^## Abstract",
    r"^## Introduction",
    r"^## System Architecture",
    r"^## Technical Design",
    r"^## Evaluation",
    r"^## Usage",
    r"^## Operational Interface",
    r"^## Security Considerations",
    r"^## References"
]

def check_readme(path):
    print(f"Checking {path}...")
    try:
        content = Path(path).read_text()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    errors = []
    
    # Check sections
    for pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"Missing section matching: '{pattern}'")

    # Check References format (simple check for numbered list)
    if "## References" in content:
        ref_section = content.split("## References")[1]
        if not re.search(r"^\d+\.", ref_section.strip(), re.MULTILINE):
             errors.append("References must be a numbered list (1., 2., ...)")

    # Check System Architecture Mermaid
    if "## System Architecture" in content:
        arch_section = content.split("## System Architecture")[1].split("##")[0]
        if "```mermaid" not in arch_section:
            errors.append("System Architecture must contain a Mermaid diagram")

    if errors:
        for e in errors:
            print(f"  ❌ {e}")
        return False
    else:
        print("  ✅ Passed")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: check_readme.py <path_to_readme>")
        sys.exit(1)
    
    success = True
    for f in sys.argv[1:]:
        if not check_readme(f):
            success = False
            
    sys.exit(0 if success else 1)
