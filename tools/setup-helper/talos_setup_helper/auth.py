import json
import base64
from pathlib import Path
from typing import Optional, Dict

class AuthError(Exception):
    """Authentication or Pairing failure"""
    pass

class AuthManager:
    """
    Manages agent identity and authentication.
    - Stores the agent_id and agent_secret securely (for now in a local file).
    - Handles the initial pairing exchange.
    """
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.auth_file = config_dir / "auth.json"
        self._identity: Optional[Dict[str, str]] = self._load_identity()
        
    def _load_identity(self) -> Optional[Dict[str, str]]:
        if not self.auth_file.exists():
            return None
        try:
            with open(self.auth_file, "r") as f:
                return json.load(f)
        except Exception:
            return None
            
    def _save_identity(self, agent_id: str, agent_secret: str, dashboard_url: str):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "agent_id": agent_id,
            "agent_secret": agent_secret,
            "dashboard_url": dashboard_url
        }
        # Secure the file (rw-------)
        with open(self.auth_file, "w") as f:
            json.dump(data, f)
        self.auth_file.chmod(0o600)
        self._identity = data

    def is_paired(self) -> bool:
        return self._identity is not None

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if not self._identity:
            raise AuthError("Agent is not paired")
        
        # Using Bearer token scheme
        return {
            "Authorization": f"Bearer {self._identity['agent_secret']}",
            "X-Talos-Agent-ID": self._identity['agent_id']
        }
        
    def get_dashboard_url(self) -> str:
        if not self._identity:
            raise AuthError("Agent is not paired")
        return self._identity["dashboard_url"]

    def pair(self, dashboard_url: str, pairing_token: str):
        """
        Exchange pairing token for permanent credentials.
        """
        import requests
        
        url = f"{dashboard_url}/api/setup/agents/register"
        payload = {
            "pairing_token": pairing_token,
            "hostname": "localhost", # simplified
            "version": "0.1.0"
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            self._save_identity(
                agent_id=data["agent_id"],
                agent_secret=data["agent_secret"],
                dashboard_url=dashboard_url
            )
        except Exception as e:
            raise AuthError(f"Pairing failed: {str(e)}")
