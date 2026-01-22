import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any

class ManifestError(Exception):
    """Base class for manifest verification errors"""
    pass

class ManifestManager:
    """
    Manages the local, pinned recipe manifest.
    Enforces that execution only proceeds for recipes explicitly allowlisted
    in the bundled manifest.json.
    """
    def __init__(self):
        self._manifest_path = Path(__file__).parent / "resources" / "manifest.json"
        self._manifest = self._load_manifest()
        
    def _load_manifest(self) -> Dict[str, Any]:
        if not self._manifest_path.exists():
            raise ManifestError(f"Pinned manifest not found at {self._manifest_path}")
            
        try:
            with open(self._manifest_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ManifestError(f"Corrupt manifest file: {str(e)}")
            
        # Basic schema validation (in a real scenario, use jsonschema)
        if "recipes" not in data or not isinstance(data["recipes"], list):
            raise ManifestError("Invalid manifest structure: missing 'recipes' list")
            
        return data

    def get_recipe(self, recipe_id: str) -> Dict[str, Any]:
        """
        Retrieve a recipe definition by ID.
        Raises ManifestError if not found.
        """
        for recipe in self._manifest["recipes"]:
            if recipe["id"] == recipe_id:
                return recipe
                
        raise ManifestError(f"Recipe '{recipe_id}' not found in pinned manifest")

    def verify_recipe_digest(self, recipe_id: str, content: str) -> bool:
        """
        Verify that a recipe's content matches the pinned digest.
        (Note: In this Phase 0 implementation, recipes are fully defined in the manifest 
        or strictly code-bound, so this might check external file integrity eventually).
        """
        recipe = self.get_recipe(recipe_id)
        expected_digest = recipe.get("digest")
        
        if not expected_digest:
            raise ManifestError(f"Recipe '{recipe_id}' has no pinned digest")
            
        # Calculate SHA-256
        actual_digest = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
        
        return actual_digest == expected_digest
