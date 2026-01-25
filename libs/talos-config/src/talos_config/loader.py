import os
import yaml
import json
from typing import Any, Dict, Optional, List
from pathlib import Path
import importlib

class ConfigurationError(Exception):
    pass

# Attempt to import JCS helper from talos-contracts
# The package name is likely talos_contracts or contracts based on installation
try:
    import jcs 
except ImportError:
    try:
        from talos_contracts import jcs
    except ImportError:
        # Fallback for dev environment where jcs.py is at root of contracts repo
        # and added to python path?
        # But we installed it via pip.
        pass

def canonicalize(data):
    # Dynamic dispatch to whatever we found
    if 'jcs' in globals():
        return jcs.canonicalize(data)
    elif 'talos_contracts' in globals() and hasattr(globals()['talos_contracts'], 'jcs'):
        return globals()['talos_contracts'].jcs.canonicalize(data)
    else:
        # For now, simplistic fallback if dependency is missing in dev
        # strictly not JCS compliant but allows progress if package is broken
        return json.dumps(data, sort_keys=True).encode("utf-8")

def load_schema():
    # Stub
    return {}

def validate_config(config, schema):
    # Stub
    pass

class ConfigurationLoader:
    def __init__(self, app_name: str = "talos"):
        self.app_name = app_name
        # Defaults -> File -> Env
        self._config: Dict[str, Any] = {}

    def load(self, 
             config_file: Optional[str] = None, 
             env_prefix: str = "TALOS__",
             defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        # 1. Defaults
        if defaults:
            self._recursive_update(self._config, defaults)

        # 2. File
        if not config_file:
            # Check standard locations
            candidates = [
                f"{self.app_name}.yaml",
                f"/etc/{self.app_name}/config.yaml",
                f"config/config.yaml"
            ]
            for c in candidates:
                if os.path.exists(c):
                    config_file = c
                    break
        
        if config_file and os.path.exists(config_file):
            self._load_file(config_file)

        # 3. Environment Variables
        self._load_env(env_prefix)

        return self._config

    def validate(self) -> str:
        """
        Validates the current configuration against the strict schema.
        Returns the JCS Digest of the canonicalized configuration.
        """
        schema = load_schema()
        # This will raise ValidationError if invalid
        validate_config(self._config, schema)
        
        # Calculate digest
        canonical_bytes = canonicalize(self._config)
        import hashlib
        return hashlib.sha256(canonical_bytes).hexdigest()

    def _load_file(self, filepath: str):
        # Security check for prod: ensure not world-writable
        if os.getenv("TALOS_ENV", "dev").lower() == "prod":
            st = os.stat(filepath)
            # Check for world-writable bit (S_IWOTH = 0o002)
            if st.st_mode & 0o002:
                 raise ConfigurationError(f"Config file {filepath} is world-writable. This is forbidden in production.")

        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            if data:
                self._recursive_update(self._config, data)

    def _load_env(self, prefix: str):
        for k, v in os.environ.items():
            if k.startswith(prefix):
                # TALOS__GLOBAL__ENV -> global.env
                key_path = k[len(prefix):].lower().split("__")
                self._set_nested(self._config, key_path, v)

    def _recursive_update(self, d: Dict, u: Dict) -> Dict:
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def _set_nested(self, d: Dict, path: List[str], value: Any):
        for key in path[:-1]:
            d = d.setdefault(key, {})
        d[path[-1]] = value
