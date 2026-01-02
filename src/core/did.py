"""
Decentralized Identifier (DID) Implementation.

This module implements W3C DID Core specification for self-sovereign identity:
https://www.w3.org/TR/did-core/

Features:
- DID generation (did:talos:<pubkey>)
- DID document creation
- Service endpoint management
- Verification method support
- Serialization to JSON/JSON-LD

Usage:
    from src.core.did import DIDDocument, DIDManager
    
    # Create DID from signing keys
    manager = DIDManager(signing_keys)
    did = manager.create_did()
    
    # Create DID document
    doc = manager.create_document()
    doc.add_service("messaging", "TalosEndpoint", "wss://example.com:8765")
"""

import hashlib
import json
import logging
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# DID method for Talos Protocol
DID_METHOD = "talos"
DID_CONTEXT = [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1",
    "https://w3id.org/security/suites/x25519-2020/v1",
]


class VerificationMethod(BaseModel):
    """
    A verification method in a DID document.
    
    Used for authentication, assertion, key agreement, etc.
    """

    id: str
    type: str
    controller: str
    public_key_multibase: str

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "controller": self.controller,
            "publicKeyMultibase": self.public_key_multibase,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerificationMethod":
        return cls(
            id=data["id"],
            type=data["type"],
            controller=data["controller"],
            public_key_multibase=data["publicKeyMultibase"],
        )


class ServiceEndpoint(BaseModel):
    """
    A service endpoint in a DID document.
    
    Describes how to interact with the DID subject.
    """

    id: str
    type: str
    service_endpoint: str
    description: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "id": self.id,
            "type": self.type,
            "serviceEndpoint": self.service_endpoint,
        }
        if self.description:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServiceEndpoint":
        return cls(
            id=data["id"],
            type=data["type"],
            service_endpoint=data["serviceEndpoint"],
            description=data.get("description"),
        )


class DIDDocument(BaseModel):
    """
    W3C DID Document implementation.
    
    Contains the DID subject's public keys, authentication methods,
    and service endpoints.
    """

    id: str  # The DID itself
    controller: Optional[str] = None
    also_known_as: list[str] = Field(default_factory=list)
    verification_method: list[VerificationMethod] = Field(default_factory=list)
    authentication: list[str] = Field(default_factory=list)
    assertion_method: list[str] = Field(default_factory=list)
    key_agreement: list[str] = Field(default_factory=list)
    capability_invocation: list[str] = Field(default_factory=list)
    capability_delegation: list[str] = Field(default_factory=list)
    service: list[ServiceEndpoint] = Field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_verification_method(
        self,
        key_id: str,
        key_type: str,
        public_key: bytes,
        purposes: list[str],
    ) -> None:
        """
        Add a verification method with specified purposes.
        
        Args:
            key_id: Unique key identifier (e.g., "#key-1")
            key_type: Key type (e.g., "Ed25519VerificationKey2020")
            public_key: Raw public key bytes
            purposes: List of purposes ("authentication", "assertionMethod", etc.)
        """
        full_id = f"{self.id}{key_id}"

        # Multibase encode (z = base58btc prefix)
        import base64
        multibase = "z" + base64.b64encode(public_key).decode().replace("+", "A").replace("/", "B")

        method = VerificationMethod(
            id=full_id,
            type=key_type,
            controller=self.id,
            public_key_multibase=multibase,
        )
        self.verification_method.append(method)

        # Add to purpose lists
        for purpose in purposes:
            if purpose == "authentication":
                self.authentication.append(full_id)
            elif purpose == "assertionMethod":
                self.assertion_method.append(full_id)
            elif purpose == "keyAgreement":
                self.key_agreement.append(full_id)
            elif purpose == "capabilityInvocation":
                self.capability_invocation.append(full_id)
            elif purpose == "capabilityDelegation":
                self.capability_delegation.append(full_id)

    def add_service(
        self,
        service_id: str,
        service_type: str,
        endpoint: str,
        description: Optional[str] = None,
    ) -> None:
        """
        Add a service endpoint.
        
        Args:
            service_id: Unique service identifier (e.g., "#messaging")
            service_type: Service type (e.g., "TalosMessaging")
            endpoint: Service URL
            description: Optional description
        """
        service = ServiceEndpoint(
            id=f"{self.id}{service_id}",
            type=service_type,
            service_endpoint=endpoint,
            description=description,
        )
        self.service.append(service)

    def get_verification_method(self, key_id: str) -> Optional[VerificationMethod]:
        """Get verification method by ID."""
        for method in self.verification_method:
            if method.id.endswith(key_id) or method.id == key_id:
                return method
        return None

    def get_service(self, service_id: str) -> Optional[ServiceEndpoint]:
        """Get service by ID."""
        for svc in self.service:
            if svc.id.endswith(service_id) or svc.id == service_id:
                return svc
        return None

    def _add_optional_field(self, result: dict, key: str, value: Any, transform=None) -> None:
        """Add field to result dict if value is truthy."""
        if value:
            result[key] = transform(value) if transform else value

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result: dict[str, Any] = {"@context": DID_CONTEXT, "id": self.id}

        # Optional scalar fields
        self._add_optional_field(result, "controller", self.controller)
        self._add_optional_field(result, "alsoKnownAs", self.also_known_as)
        self._add_optional_field(result, "authentication", self.authentication)
        self._add_optional_field(result, "assertionMethod", self.assertion_method)
        self._add_optional_field(result, "keyAgreement", self.key_agreement)
        self._add_optional_field(result, "capabilityInvocation", self.capability_invocation)
        self._add_optional_field(result, "capabilityDelegation", self.capability_delegation)
        self._add_optional_field(result, "created", self.created)
        self._add_optional_field(result, "updated", self.updated)

        # Optional list fields with transformation
        self._add_optional_field(result, "verificationMethod", self.verification_method,
                                  lambda v: [m.to_dict() for m in v])
        self._add_optional_field(result, "service", self.service,
                                  lambda s: [svc.to_dict() for svc in s])

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DIDDocument":
        """Create from dictionary."""
        doc = cls(id=data["id"])

        doc.controller = data.get("controller")
        doc.also_known_as = data.get("alsoKnownAs", [])

        if "verificationMethod" in data:
            doc.verification_method = [
                VerificationMethod.from_dict(m) for m in data["verificationMethod"]
            ]

        doc.authentication = data.get("authentication", [])
        doc.assertion_method = data.get("assertionMethod", [])
        doc.key_agreement = data.get("keyAgreement", [])
        doc.capability_invocation = data.get("capabilityInvocation", [])
        doc.capability_delegation = data.get("capabilityDelegation", [])

        if "service" in data:
            doc.service = [ServiceEndpoint.from_dict(s) for s in data["service"]]

        doc.created = data.get("created")
        doc.updated = data.get("updated")

        return doc

    @classmethod
    def from_json(cls, json_str: str) -> "DIDDocument":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


class DIDManager:
    """
    Manager for creating and managing DIDs.
    
    Handles DID generation, document creation, and resolution.
    """

    def __init__(
        self,
        signing_keypair: Any,
        encryption_keypair: Optional[Any] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize DID manager.
        
        Args:
            signing_keypair: Ed25519 signing keypair
            encryption_keypair: Optional X25519 encryption keypair
            storage_path: Optional path for DID document persistence
        """
        self.signing_keypair = signing_keypair
        self.encryption_keypair = encryption_keypair
        self.storage_path = storage_path

        self._did: Optional[str] = None
        self._document: Optional[DIDDocument] = None

    @property
    def did(self) -> str:
        """Get or create the DID."""
        if self._did is None:
            self._did = self.create_did()
        return self._did

    def create_did(self) -> str:
        """
        Create a DID from the signing public key.
        
        Format: did:talos:<base58-encoded-pubkey>
        
        Returns:
            The DID string
        """

        # Use base58-like encoding (simplified)
        self.signing_keypair.public_key.hex()

        # Create DID with pubkey hash for shorter identifier
        pubkey_hash = hashlib.sha256(self.signing_keypair.public_key).hexdigest()[:32]

        return f"did:{DID_METHOD}:{pubkey_hash}"

    def create_document(
        self,
        service_endpoint: Optional[str] = None,
    ) -> DIDDocument:
        """
        Create a DID document.
        
        Args:
            service_endpoint: Optional messaging service endpoint
            
        Returns:
            Complete DID document
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        doc = DIDDocument(
            id=self.did,
            created=now,
            updated=now,
        )

        # Add signing key
        doc.add_verification_method(
            key_id="#key-1",
            key_type="Ed25519VerificationKey2020",
            public_key=self.signing_keypair.public_key,
            purposes=["authentication", "assertionMethod", "capabilityInvocation"],
        )

        # Add encryption key if available
        if self.encryption_keypair:
            doc.add_verification_method(
                key_id="#key-2",
                key_type="X25519KeyAgreementKey2020",
                public_key=self.encryption_keypair.public_key,
                purposes=["keyAgreement"],
            )

        # Add messaging service endpoint
        if service_endpoint:
            doc.add_service(
                service_id="#messaging",
                service_type="TalosMessaging",
                endpoint=service_endpoint,
                description="Talos Protocol secure messaging endpoint",
            )

        self._document = doc
        return doc

    @property
    def document(self) -> DIDDocument:
        """Get or create the DID document."""
        if self._document is None:
            self._document = self.create_document()
        return self._document

    def update_service_endpoint(self, endpoint: str) -> None:
        """Update the messaging service endpoint."""
        doc = self.document

        # Remove existing messaging service
        doc.service = [s for s in doc.service if not s.id.endswith("#messaging")]

        # Add new endpoint
        doc.add_service(
            service_id="#messaging",
            service_type="TalosMessaging",
            endpoint=endpoint,
        )

        # Update timestamp
        from datetime import datetime, timezone
        doc.updated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def save(self, path: Optional[Path] = None) -> None:
        """Save DID document to disk."""
        save_path = path or self.storage_path
        if not save_path:
            raise ValueError("No storage path specified")

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            f.write(self.document.to_json())

        logger.debug(f"Saved DID document to {save_path}")

    def load(self, path: Optional[Path] = None) -> DIDDocument:
        """Load DID document from disk."""
        load_path = path or self.storage_path
        if not load_path:
            raise ValueError("No storage path specified")

        load_path = Path(load_path)

        with open(load_path) as f:
            self._document = DIDDocument.from_json(f.read())

        self._did = self._document.id

        logger.debug(f"Loaded DID document from {load_path}")
        return self._document

    def to_dict(self) -> dict[str, Any]:
        """Get DID document as dictionary."""
        return self.document.to_dict()


def resolve_did(did: str) -> Optional[dict[str, Any]]:
    """
    Resolve a DID to its document.
    
    This is a placeholder that will be implemented with DHT lookup.
    
    Args:
        did: The DID to resolve
        
    Returns:
        DID document dict if found, None otherwise
    """
    # TODO: Implement DHT lookup
    logger.debug(f"Resolving DID: {did}")
    return None


def validate_did(did: str) -> bool:
    """
    Validate DID format.
    
    Args:
        did: DID string to validate
        
    Returns:
        True if valid format
    """
    if not did.startswith("did:"):
        return False

    parts = did.split(":")
    if len(parts) < 3:
        return False

    # Check method
    if parts[1] != DID_METHOD:
        return False

    # Check identifier is hex (32 chars)
    identifier = parts[2]
    if len(identifier) != 32:
        return False

    try:
        int(identifier, 16)
    except ValueError:
        return False

    return True
