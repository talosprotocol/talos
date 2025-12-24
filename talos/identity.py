"""
Talos Identity Management.

Manages cryptographic keys and prekey bundles for secure communication.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from src.core.crypto import (
    KeyPair,
    generate_signing_keypair,
    generate_encryption_keypair,
    sign_message,
    verify_signature,
)
from src.core.session import PrekeyBundle, SessionManager

logger = logging.getLogger(__name__)


class Identity:
    """
    Represents a Talos identity with cryptographic keys.
    
    An identity consists of:
    - Signing keypair (Ed25519): For authentication and signatures
    - Encryption keypair (X25519): For key exchange
    - Prekey bundle: For others to establish sessions
    
    Usage:
        # Create new identity
        identity = Identity.create("my-agent")
        
        # Save to disk
        identity.save(Path("~/.talos/keys.json"))
        
        # Load existing
        identity = Identity.load(Path("~/.talos/keys.json"))
        
        # Get shareable address
        print(f"My address: {identity.address}")
    """
    
    def __init__(
        self,
        name: str,
        signing_keys: KeyPair,
        encryption_keys: KeyPair,
    ):
        self.name = name
        self.signing_keys = signing_keys
        self.encryption_keys = encryption_keys
        
        # Session manager for Double Ratchet
        self._session_manager: Optional[SessionManager] = None
    
    @classmethod
    def create(cls, name: str = "talos-agent") -> "Identity":
        """
        Create a new identity with fresh key pairs.
        
        Args:
            name: Human-readable name for this identity
            
        Returns:
            New Identity instance
        """
        signing = generate_signing_keypair()
        encryption = generate_encryption_keypair()
        
        logger.info(f"Created identity: {name} ({signing.public_key_short})")
        return cls(name, signing, encryption)
    
    @property
    def address(self) -> str:
        """
        Get the public address (signing public key as hex).
        
        This is the identifier that others use to send messages to you.
        """
        return self.signing_keys.public_key_hex
    
    @property
    def address_short(self) -> str:
        """Get shortened address for display."""
        return self.signing_keys.public_key_short
    
    def sign(self, data: bytes) -> bytes:
        """Sign data with this identity's signing key."""
        return sign_message(data, self.signing_keys.private_key)
    
    def verify(self, data: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify a signature from another identity."""
        return verify_signature(data, signature, public_key)
    
    def get_prekey_bundle(self) -> PrekeyBundle:
        """
        Get prekey bundle for session establishment.
        
        This should be published to the registry so others can
        establish secure sessions with you.
        """
        if self._session_manager is None:
            self._session_manager = SessionManager(self.signing_keys)
        return self._session_manager.get_prekey_bundle()
    
    def get_session_manager(self) -> SessionManager:
        """Get or create session manager for this identity."""
        if self._session_manager is None:
            self._session_manager = SessionManager(self.signing_keys)
        return self._session_manager
    
    def to_dict(self) -> dict:
        """Serialize identity to dictionary."""
        return {
            "name": self.name,
            "signing_keys": self.signing_keys.to_dict(),
            "encryption_keys": self.encryption_keys.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Identity":
        """Deserialize identity from dictionary."""
        return cls(
            name=data["name"],
            signing_keys=KeyPair.from_dict(data["signing_keys"]),
            encryption_keys=KeyPair.from_dict(data["encryption_keys"]),
        )
    
    def save(self, path: Path) -> None:
        """
        Save identity to a file.
        
        SECURITY: This file contains private keys! Protect accordingly.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        # Set restrictive permissions (owner read/write only)
        path.chmod(0o600)
        
        logger.info(f"Saved identity to {path}")
    
    @classmethod
    def load(cls, path: Path) -> "Identity":
        """Load identity from a file."""
        path = Path(path)
        
        with open(path) as f:
            data = json.load(f)
        
        identity = cls.from_dict(data)
        logger.info(f"Loaded identity: {identity.name} ({identity.address_short})")
        return identity
    
    @classmethod
    def load_or_create(cls, path: Path, name: str = "talos-agent") -> "Identity":
        """
        Load identity from file, or create new if doesn't exist.
        
        This is the recommended way to initialize an identity.
        """
        path = Path(path)
        
        if path.exists():
            return cls.load(path)
        else:
            identity = cls.create(name)
            identity.save(path)
            return identity
    
    def __repr__(self) -> str:
        return f"Identity(name={self.name!r}, address={self.address_short})"
