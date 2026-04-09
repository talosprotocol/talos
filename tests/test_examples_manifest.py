import json
import os
from pathlib import Path

def test_examples_manifest_exists():
    assert os.path.exists("examples/examples_manifest.json")

def test_examples_manifest_valid_json():
    with open("examples/examples_manifest.json", "r") as f:
        data = json.load(f)
    assert "examples" in data
    assert isinstance(data["examples"], list)

def test_examples_manifest_parity():
    with open("examples/examples_manifest.json", "r") as f:
        data = json.load(f)
    
    for example in data["examples"]:
        assert "id" in example
        assert "route" in example
        
        # Check if corresponding site/dashboard/src/app/api/examples/ exists
        route_path = example["route"].replace("/examples/", "")
        api_dir = Path(f"site/dashboard/src/app/api/examples/{route_path}")
        assert api_dir.exists(), f"API directory for example {example['id']} missing: {api_dir}"

def test_manifest_route_exists():
    assert os.path.exists("site/dashboard/src/app/api/examples/manifest/route.ts")
