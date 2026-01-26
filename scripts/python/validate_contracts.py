
import json
import yaml
import sys
import jsonschema
from pathlib import Path
from contracts.jcs import canonicalize
import hashlib

def validate_examples():
    schema_path = Path("contracts/schemas/config/v1/talos.config.schema.json")
    examples_dir = Path("contracts/examples/config/v1")
    
    with open(schema_path) as f:
        schema = json.load(f)
        
    print(f"Validating examples against {schema_path}...")
    
    has_error = False
    for example_file in examples_dir.glob("*.yaml"):
        print(f"Checking {example_file}...")
        try:
            with open(example_file) as f:
                config = yaml.safe_load(f)
            
            jsonschema.validate(instance=config, schema=schema)
            
            # Test Canonicalization
            canonical = canonicalize(config)
            digest = hashlib.sha256(canonical).hexdigest()
            print(f"  ✅ Valid. Digest: {digest}")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            has_error = True
            
    if has_error:
        sys.exit(1)
    else:
        print("All examples passed schema validation.")

if __name__ == "__main__":
    validate_examples()
