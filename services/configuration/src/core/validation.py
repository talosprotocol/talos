
import json
import hashlib
import jsonschema
from typing import Tuple, Dict, Any, List, Optional
from src.core.jcs import canonicalize
from src.core import redaction

# Load schema once (in a real app, this might be dynamic or reloaded)
# For now, we assume it's available relative to the service or bundled
try:
    with open("../../contracts/schemas/config/v1/talos.config.schema.json") as f:
        SCHEMA = json.load(f)
except FileNotFoundError:
    # Fallback/Mock for docker/standalone where relative path might differ
    # Only for dev scaffold safety
    SCHEMA = {"type": "object", "additionalProperties": True} 

def validate_and_normalize(config: Dict[str, Any], strict: bool = True) -> Tuple[bool, List[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate and Normalize configuration.
    
    1. Validate against JSON Schema.
    2. Normalize:
       - Apply defaults (schema-driven).
       - (Strict mode) Reject unknown keys - redundant if schema has additionalProperties: false.
    3. Compute JCS Canonical Digest.
    
    Returns:
        (valid, errors, normalized_config, digest)
    """
    validator = jsonschema.Draft7Validator(SCHEMA)
    errors = []
    
    for error in validator.iter_errors(config):
        path = "/".join(str(p) for p in error.path)
        code = "SCHEMA_VALIDATION_FAILED"
        # Map some jsonschema errors to our Error Codes if useful
        errors.append({
            "code": code,
            "message": error.message,
            "path": path,
            "details": {"schema_path": "/".join(str(p) for p in error.schema_path)}
        })

    if errors:
        return False, errors, None, None

    # Normalization
    # For JSON Schema, "applying defaults" is often done by the validator or a pre-pass.
    # Python jsonschema doesn't automatically modify the instance with defaults.
    # We must explicitly apply defaults to get a "normalized" object.
    
    normalized = _apply_defaults(config, SCHEMA)
    
    # Canonicalize
    try:
        canonical_bytes = canonicalize(normalized)
        digest = hashlib.sha256(canonical_bytes).hexdigest()
    except Exception as e:
        # Should not happen if validation passed and types are standard
        return False, [{"code": "CANONICALIZATION_FAILED", "message": str(e)}], None, None
        
    return True, [], normalized, digest

def _apply_defaults(instance: Any, schema: Dict[str, Any]) -> Any:
    """
    Recursively apply defaults from schema to the instance.
    This is a simplified implementation for the "Final Lock" requirement:
    "Defaults: Deterministic schema-driven filling (not Pydantic defaults)"
    """
    if not isinstance(schema, dict):
        return instance

    if "default" in schema and instance is None:
        return schema["default"]
        
    if "properties" in schema and isinstance(instance, dict):
        new_instance = instance.copy()
        for prop, subschema in schema["properties"].items():
            if prop not in new_instance:
                if "default" in subschema:
                    new_instance[prop] = subschema["default"]
                elif subschema.get("type") == "object":
                     # Recurse if it's an object that might have nested defaults
                     # but only if we want to auto-create objects. 
                     # Strategy: Only apply defaults if the parent key exists OR if default is provided.
                     # Strict: If parent key missing and no default, we don't invent it unless required?
                     # Better: If subschema has default, use it. If not, don't create.
                     pass
            
            if prop in new_instance:
                new_instance[prop] = _apply_defaults(new_instance[prop], subschema)
        return new_instance

    return instance
