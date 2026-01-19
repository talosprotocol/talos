#!/usr/bin/env python3
"""Check README version matches pyproject.toml.

Validates the version marker in README.md:
    <!-- TALOS_SDK_PY_VERSION: x.y.z -->

Compares against the version in pyproject.toml.
Exits non-zero on mismatch.

Usage: python scripts/check_readme_version.py
"""

import re
import sys
from pathlib import Path


def get_pyproject_version() -> str:
    """Extract version from pyproject.toml."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def get_readme_version() -> str:
    """Extract version marker from README.md."""
    readme = Path(__file__).parent.parent / "README.md"
    if not readme.exists():
        raise FileNotFoundError("README.md not found")
    
    content = readme.read_text(encoding="utf-8")
    # Match: <!-- TALOS_SDK_PY_VERSION: x.y.z -->
    match = re.search(r'<!--\s*TALOS_SDK_PY_VERSION:\s*([^\s]+)\s*-->', content)
    if not match:
        raise ValueError("Version marker not found in README.md")
    
    return match.group(1)


def main() -> int:
    """Compare versions and exit with status."""
    try:
        pyproject_ver = get_pyproject_version()
        readme_ver = get_readme_version()
        
        print(f"pyproject.toml version: {pyproject_ver}")
        print(f"README.md version:      {readme_ver}")
        
        if pyproject_ver == readme_ver:
            print("✅ Versions match")
            return 0
        else:
            print("❌ VERSION MISMATCH!")
            print(f"   Expected (pyproject.toml): {pyproject_ver}")
            print(f"   Found (README.md):         {readme_ver}")
            print("\nTo fix: Update README.md version marker to match pyproject.toml")
            return 1
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except ValueError as e:
        print(f"❌ Parse error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
