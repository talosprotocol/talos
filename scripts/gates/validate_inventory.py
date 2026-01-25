
import json
import os
import sys
from jsonschema import validate

INVENTORY_PATH = "contracts/inventory/gateway_surface.json"
SCHEMA_PATH = "contracts/schemas/inventory/surface_inventory.schema.json"

def main():
    if not os.path.exists(INVENTORY_PATH):
        print(f"Inventory not found at {INVENTORY_PATH}")
        sys.exit(1)
        
    with open(INVENTORY_PATH) as f:
        data = json.load(f)
        
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
        
    print(f"Validating {INVENTORY_PATH} against schema...")
    try:
        validate(instance=data, schema=schema)
        print("Schema validation passed.")
    except Exception as e:
        print(f"Schema Validation Failed: {e}")
        sys.exit(1)
        
    # Extra Logic: Audit Meta Allowlist Check
    print("Checking Audit Integrity rules...")
    errors = []
    for item in data.get("items", []):
        if "audit_meta_allowlist" not in item:
            errors.append(f"Item {item['id']} missing 'audit_meta_allowlist'")
        elif not isinstance(item["audit_meta_allowlist"], list):
             errors.append(f"Item {item['id']} 'audit_meta_allowlist' is not a list")
             
        if "audit_action" not in item:
            errors.append(f"Item {item['id']} missing 'audit_action'")
            
        if "data_classification" not in item:
            errors.append(f"Item {item['id']} missing 'data_classification'")
            
    if errors:
        print("Audit Integrity Check Failed:")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
        
    print("All checks passed.")

if __name__ == "__main__":
    main()
