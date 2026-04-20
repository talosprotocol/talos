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
    "cursor_encoding": r"^\s*(?:def|function)\s+(?:encode_cursor|decode_cursor|encodeCursor|decodeCursor)\s*\(",
}

# Directories to exclude from drift check (mostly source-of-truth, dependencies,
# generated outputs, and local tool caches).
EXCLUDE_DIRS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".turbo",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "contracts",
    "coverage",
    "dist",
    "env",
    "node_modules",
    "site-packages",
    "target",
    "venv",
}

SOURCE_SUFFIXES = {".py", ".ts", ".tsx"}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def is_test_file(path: Path) -> bool:
    return (
        "tests" in path.parts
        or "__tests__" in path.parts
        or path.name.startswith("test_")
        or path.name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))
    )


def imports_contracts(content: str) -> bool:
    return (
        "from talos_contracts" in content
        or "import talos_contracts" in content
        or "import { stripNulls } from" in content
    )


def is_import_only_match(content: str, name: str) -> bool:
    if name not in {"strip_nulls", "cursor_encoding", "base64url"}:
        return False
    return "def " + name not in content and "function " + name not in content


def iter_source_files(root_dir: Path):
    for path in root_dir.rglob("*"):
        if is_excluded(path):
            continue
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            yield path


def check_drift(root_dir: Path) -> bool:
    found_drift = False

    for path in iter_source_files(root_dir):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if is_test_file(path):
            continue

        is_importing_contracts = imports_contracts(content)
        for name, pattern in DRIFT_PATTERNS.items():
            if not re.search(pattern, content, flags=re.MULTILINE):
                continue
            if is_importing_contracts and is_import_only_match(content, name):
                continue

            print(f"Potential Contract Drift Detected: '{name}' in {path}")
            found_drift = True

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
