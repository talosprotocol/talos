#!/usr/bin/env python3
"""
Check for contract logic duplication in consumer repos.
Ensures consumers import logic from talos-contracts instead of re-implementing.
"""

import sys
import re
from pathlib import Path

# Patterns that indicate potential re-implementation of contract logic
DRIFT_PATTERNS = {
    "strip_nulls": r"def strip_nulls\(|function stripNulls\(",
    "base64url": r"base64\.urlsafe_b64encode\(.*\.rstrip\('='\)|btoa\(.*\.replace\('\+', '-'\)\.replace\('/', '_'\)",
    "uuidv7": r"uuidv7\(|018[a-f0-9]{1}\-",
    "cursor_encoding": r"encode_cursor\(|decode_cursor\(",
}

# Directories to exclude from drift check (mostly the contract repo itself)
EXCLUDE_DIRS = [
    "contracts",
    "node_modules",
    "__pycache__",
    ".git",
    "artifacts",
]

def check_drift(root_dir: Path):
    found_drift = False
    
    for path in root_dir.rglob("*"):
        if any(ex in path.parts for ex in EXCLUDE_DIRS):
            continue
            
        if path.is_file() and path.suffix in [".py", ".ts", ".tsx"]:
            try:
                content = path.read_text()
                # If the file imports the logic from talos_contracts, it's not a drift/duplication
                is_importing_contracts = "from talos_contracts" in content or "import talos_contracts" in content or "import { stripNulls } from" in content
                
                for name, pattern in DRIFT_PATTERNS.items():
                    if re.search(pattern, content):
                        if is_importing_contracts and name in ["strip_nulls", "cursor_encoding", "base64url"]:
                             # Check if it's just the import or an actual re-implementation
                             # This is a bit coarse but helps reduce false positives
                             if "def " + name not in content and "function " + name not in content:
                                 continue

                        # Simple heuristic: if it's a test file, it's often okay to have mocks
                        if "test" in path.name:
                            continue
                            
                        # If it's the implementation in the SDK itself (core), we might allow it
                        # but we should generally prefer the contract lib even there.
                        
                        print(f"Potential Contract Drift Detected: '{name}' in {path}")
                        found_drift = True
            except Exception:
                continue
                
    return found_drift

def main():
    root = Path(__file__).resolve().parents[2]
    print(f"Scanning for contract drift in {root}...")
    
    if check_drift(root):
        print("\nFAILURE: Contract logic duplication detected.")
        print("Please import canonical logic from 'talos-contracts' instead of re-implementing.")
        sys.exit(1)
    
    print("\nSUCCESS: No contract drift detected.")
    sys.exit(0)

if __name__ == "__main__":
    main()
