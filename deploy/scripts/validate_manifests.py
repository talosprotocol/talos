#!/usr/bin/env python3
"""
Talos SDK Manifest Validator

Enforces the Manifest Boundary by:
1. Validating SDK manifests against sdk_manifest.schema.json
2. Verifying that declared hashes match the actual local contracts/schedule artifacts.
"""

import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Try using stdlib tomllib (Python 3.11+), fallback to toml
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import toml as tomllib
    except ImportError:
        print("Error: 'toml' package is required for Python < 3.11")
        sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("Error: 'jsonschema' package is required")
    sys.exit(1)



SDK_MANIFEST_FILES = {
    "talos-sdk-py": "pyproject.toml",
    "talos-sdk-ts": "package.json",
    "talos-sdk-java": "talos.json",
    "talos-sdk-go": "talos.json",
    "talos-core-rs": "Cargo.toml",
}

def load_submodules_manifest(root_dir: Path) -> list[dict]:
    manifest_path = root_dir / "deploy/submodules.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Submodules manifest not found at {manifest_path}")
    with open(manifest_path, "r") as f:
        return json.load(f)

def compute_hash(path: Path) -> str:
    """Compute SHA256 hash of CANONICAL JSON bytes encoded as Base64URL (no padding)."""
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")

    # Load and Canonicalize
    if path.name.endswith(".json"):
        with open(path, "rb") as f:
            data = json.load(f)
        # RFC 8785 (JCS) style canonicalization
        canonical_bytes = json.dumps(
            data,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=False
        ).encode("utf-8")
    else:
        # Fallback for non-JSON files (raw bytes)
        canonical_bytes = path.read_bytes()
    
    digest = hashlib.sha256(canonical_bytes).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

def extract_metadata(repo_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract talos_compatibility metadata from different manifest formats."""
    if repo_type == "python": # pyproject.toml
        return data.get("tool", {}).get("talos", {}).get("talos_compatibility", {})
    elif repo_type == "typescript": # package.json
        return data.get("talos", {}).get("talos_compatibility", {})
    elif repo_type == "rust": # Cargo.toml
        return data.get("package", {}).get("metadata", {}).get("talos", {})
    elif repo_type in ("go", "java"): # talos.json
        return data.get("talos_compatibility", {})
    return {}

def verify_hashes(metadata: Dict[str, Any], truth: Dict[str, str]) -> bool:
    """Verify declared hashes against the ground truth."""
    declared_contract = metadata.get("contract_hash")
    declared_schedule = metadata.get("schedule_hash")
    features = metadata.get("features", [])

    valid = True

    # 1. Contract Hash (Always Required)
    if declared_contract != truth["contract_hash"]:
        print("  ❌ CONTRACT_HASH mismatch!")
        print(f"     Declared: {declared_contract}")
        print(f"     Actual:   {truth['contract_hash']}")
        valid = False
    else:
        print("  ✅ CONTRACT_HASH Verified")

    # 2. Schedule Hash (Required if Ratchet feature present)
    ratchet_required = "ratchet" in features

    if ratchet_required:
        if not declared_schedule:
            print("  ❌ Missing SCHEDULE_HASH (Required by 'ratchet' feature)")
            valid = False
        elif declared_schedule != truth["schedule_hash"]:
            print("  ❌ SCHEDULE_HASH mismatch!")
            print(f"     Declared: {declared_schedule}")
            print(f"     Actual:   {truth['schedule_hash']}")
            valid = False
        else:
            print("  ✅ SCHEDULE_HASH Verified")
    elif declared_schedule:
        # Optional check if present but not required
        if declared_schedule != truth["schedule_hash"]:
            print("  ❌ SCHEDULE_HASH mismatch! (Optional but present)")
            print(f"     Declared: {declared_schedule}")
            print(f"     Actual:   {truth['schedule_hash']}")
            valid = False
        else:
            print("  ✅ SCHEDULE_HASH Verified (Optional)")

    return valid

def load_truth(root_dir: Path) -> Dict[str, str]:
    """Load the source of truth hashes from contracts."""
    contracts_dir = root_dir / "contracts" / "sdk"
    
    contract_manifest = contracts_dir / "contract_manifest.json"
    schedule_file = contracts_dir / "ratchet_kdf_schedule.json"
    
    print(f"Loading Truth from: {contracts_dir}")
    
    try:
        truth = {
            "contract_hash": compute_hash(contract_manifest),
            "schedule_hash": compute_hash(schedule_file),
        }
    except Exception as e:
        print(f"❌ Failed to compute truth hashes: {e}")
        sys.exit(1)
    
    print(f"  Truth CONTRACT_HASH: {truth['contract_hash']}")
    print(f"  Truth SCHEDULE_HASH: {truth['schedule_hash']}")
    
    return truth

def validate_repo(repo_entry: dict, root_dir: Path, schema: Dict[str, Any], truth: Dict[str, str]) -> bool:
    """Validate a single SDK repository."""
    repo_name = repo_entry["name"]
    manifest_name = SDK_MANIFEST_FILES.get(repo_name)
    if not manifest_name:
        return True # Skip non-SDKs or unknown

    repo_path = root_dir / repo_entry["new_path"]
    manifest_path = repo_path / manifest_name
    
    if not manifest_path.exists():
        print(f"❌ {repo_name}: Manifest missing at {manifest_path}")
        return False

    print(f"Checking {repo_name}...")

    try:
        # Parse Manifest
        if manifest_name.endswith(".toml"):
            if sys.version_info >= (3, 11):
                with open(manifest_path, "rb") as f:
                    data = tomllib.load(f)
            else:
                with open(manifest_path, "r") as f:
                    data = tomllib.load(f)
        else:
            with open(manifest_path, "rb") as f:
                data = json.load(f)
        
        # Determine repo_type for extraction
        if "py" in repo_name: repo_type = "python"
        elif "ts" in repo_name: repo_type = "typescript"
        elif "rs" in repo_name: repo_type = "rust"
        elif "go" in repo_name: repo_type = "go"
        elif "java" in repo_name: repo_type = "java"
        else: repo_type = "unknown"

        # Extract Metadata
        metadata = extract_metadata(repo_type, data)
        if not metadata:
            print("  ❌ Missing 'talos_compatibility' metadata")
            return False

        # Synthetic object for schema validation
        display_obj = {
            "name": f"synthetic-{repo_name}",
            "version": "0.0.0",
            "license": "Apache-2.0",
            "homepage": "http://example.com",
            "repository": "http://example.com",
            "authors": ["validator"],
            "talos_compatibility": metadata
        }

        # Schema Validation
        try:
            jsonschema.validate(instance=display_obj, schema=schema)
            print("  ✅ Schema Validation Passed")
        except jsonschema.ValidationError as e:
            print(f"  ❌ Schema Validation Failed: {e.message}")
            print(f"     Path: {e.json_path}")
            return False

        # Validate Hashes
        return verify_hashes(metadata, truth)

    except Exception as e:
        print(f"  ❌ Error processing {manifest_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate Talos SDK Manifests")
    parser.add_argument("--root-dir", type=Path, default=Path.cwd(), help="Path to repository root")
    args = parser.parse_args()

    root_dir = args.root_dir.resolve()
    if not root_dir.exists():
        print(f"Error: Root directory not found at {root_dir}")
        sys.exit(1)

    # Load Schema
    schema_path = root_dir / "contracts" / "sdk" / "sdk_manifest.schema.json"
    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}")
        sys.exit(1)
        
    with open(schema_path, "r") as f:
        schema = json.load(f)

    # Load Truth
    try:
        truth = load_truth(root_dir)
    except Exception as e:
        print(f"Error loading truth: {e}")
        sys.exit(1)
    
    # Load Submodules
    try:
        submodules = load_submodules_manifest(root_dir)
    except Exception as e:
        print(f"Error loading submodules manifest: {e}")
        sys.exit(1)

    # Validate All
    success = True
    print("\n--- Starting Validation ---\n")
    
    for entry in submodules:
        if entry["name"] in SDK_MANIFEST_FILES:
            if not validate_repo(entry, root_dir, schema, truth):
                success = False
            print("")

    if success:
        print("🎉 All SDK Manifests Validated Successfully!")
        sys.exit(0)
    else:
        print("🔥 Validation Failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
