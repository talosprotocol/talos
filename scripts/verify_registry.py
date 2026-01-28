
import json
import sys
from pathlib import Path

def verify_registry(registry_path: str):
    print(f"Verifying Registry: {registry_path}")
    with open(registry_path, "r") as f:
        data = json.load(f)
    
    tools = data.get("tools", [])
    errors = []
    
    for t in tools:
        server = t.get("tool_server")
        name = t.get("tool_name")
        t_class = t.get("tool_class")
        req_idem = t.get("requires_idempotency_key", False)
        
        # CI Gate 5.2: requires_idempotency_key=true for all write tools
        if t_class == "write" and not req_idem:
            errors.append(f"ERROR: Tool {server}:{name} is 'write' but missing 'requires_idempotency_key=true'")
            
    if errors:
        for err in errors:
            print(err)
        sys.exit(1)
    
    print(f"✅ Registry Validated: {len(tools)} tools checked.")

if __name__ == "__main__":
    registry_file = "contracts/data/tools_registry.json"
    if not Path(registry_file).exists():
        print(f"Registry file not found: {registry_file}")
        sys.exit(1)
    verify_registry(registry_file)
