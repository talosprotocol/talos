"""
Talos SDK Configuration.

Provides sensible defaults with override capability.
"""

from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from typing import Any, Optional
import json
import os


class TalosConfig(BaseModel):
    """
    Configuration for Talos SDK.
    
    All paths default to ~/.talos/ directory.
    Environment variables override defaults (TALOS_* prefix).
    """
    
    # Identity
    name: str = "talos-agent"
    
    # Storage paths
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".talos")
    keys_file: str = "keys.json"
    sessions_file: str = "sessions.json"
    blockchain_file: str = "chain.json"
    
    # Network
    registry_url: str = "ws://localhost:8765"
    listen_port: int = 0  # 0 = auto-assign
    max_peers: int = 50
    connection_timeout: float = 10.0
    
    # Blockchain
    difficulty: int = 2
    max_block_size: int = 1_000_000  # 1MB
    
    # Encryption
    forward_secrecy: bool = True  # Use Double Ratchet
    
    # Rate limiting
    max_requests_per_minute: int = 60
    max_data_per_day: int = 100_000_000  # 100MB
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def model_post_init(self, __context):
        """Apply environment variable overrides."""
        self._apply_env_overrides()
        self._ensure_directories()
    
    def _apply_env_overrides(self):
        """Override config from environment variables."""
        env_map = {
            "TALOS_NAME": ("name", str),
            "TALOS_DATA_DIR": ("data_dir", Path),
            "TALOS_REGISTRY_URL": ("registry_url", str),
            "TALOS_LISTEN_PORT": ("listen_port", int),
            "TALOS_DIFFICULTY": ("difficulty", int),
            "TALOS_LOG_LEVEL": ("log_level", str),
        }
        
        for env_var, (attr, type_fn) in env_map.items():
            value = os.environ.get(env_var)
            if value is not None:
                setattr(self, attr, type_fn(value))
    
    def _ensure_directories(self):
        """Create data directory if needed."""
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def keys_path(self) -> Path:
        """Full path to keys file."""
        filename = f"{self.name}.{self.keys_file}" if self.keys_file == "keys.json" else self.keys_file
        return self.data_dir / filename
    
    @property
    def sessions_path(self) -> Path:
        """Full path to sessions file."""
        filename = f"{self.name}.{self.sessions_file}" if self.sessions_file == "sessions.json" else self.sessions_file
        return self.data_dir / filename
    
    @property
    def blockchain_path(self) -> Path:
        """Full path to blockchain file."""
        # Blockchain is shared by default in simulation, but strictly should be per-node.
        # For 'client' usage, let's keep it per-node to avoid locking issues.
        filename = f"{self.name}.{self.blockchain_file}" if self.blockchain_file == "chain.json" else self.blockchain_file
        return self.data_dir / filename
    
    def to_dict(self) -> dict[str, Any]:
        """Export config to dictionary."""
        return {
            "name": self.name,
            "data_dir": str(self.data_dir),
            "registry_url": self.registry_url,
            "listen_port": self.listen_port,
            "difficulty": self.difficulty,
            "forward_secrecy": self.forward_secrecy,
            "log_level": self.log_level,
        }
    
    def save(self, path: Optional[Path] = None):
        """Save config to file."""
        path = path or (self.data_dir / "config.json")
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> "TalosConfig":
        """Load config from file."""
        with open(path) as f:
            data = json.load(f)
        
        return cls(
            name=data.get("name", "talos-agent"),
            data_dir=Path(data.get("data_dir", Path.home() / ".talos")),
            registry_url=data.get("registry_url", "ws://localhost:8765"),
            listen_port=data.get("listen_port", 0),
            difficulty=data.get("difficulty", 2),
            forward_secrecy=data.get("forward_secrecy", True),
            log_level=data.get("log_level", "INFO"),
        )
    
    @classmethod
    def development(cls) -> "TalosConfig":
        """Create development config with relaxed settings."""
        return cls(
            name="dev-agent",
            data_dir=Path.home() / ".talos-dev",
            difficulty=1,
            log_level="DEBUG",
        )
    
    @classmethod
    def production(cls) -> "TalosConfig":
        """Create production config with strict settings."""
        return cls(
            name="prod-agent",
            difficulty=4,
            log_level="WARNING",
            forward_secrecy=True,
        )
