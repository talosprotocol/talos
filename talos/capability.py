"""
Talos SDK - Capability Module.

High-level API for capability management.

Usage:
    from talos import TalosClient
    
    async with TalosClient.create("my-agent") as client:
        # Grant capability to another agent
        cap = await client.grant_capability(
            subject="did:talos:other",
            scope="tools/read",
            expires_in=3600
        )
        
        # Verify a capability
        is_valid = await client.verify_capability(cap)
        
        # Revoke if needed
        await client.revoke_capability(cap.id, reason="no longer needed")
"""

import logging
from typing import Any, Optional

from src.core.capability import (
    Capability,
    CapabilityManager,
    CapabilityError,
    CapabilityExpired,
    CapabilityRevoked,
    CapabilityInvalid,
    ScopeViolation,
)

logger = logging.getLogger(__name__)

# Re-export exceptions for SDK users
__all__ = [
    "Capability",
    "CapabilityError",
    "CapabilityExpired",
    "CapabilityRevoked",
    "CapabilityInvalid",
    "ScopeViolation",
    "CapabilityMixin",
]


class CapabilityMixin:
    """
    Mixin for TalosClient to add capability management.
    
    This mixin is included in TalosClient to provide
    capability-based authorization methods.
    """
    
    _capability_manager: Optional[CapabilityManager] = None
    
    def _ensure_capability_manager(self) -> CapabilityManager:
        """Ensure capability manager is initialized."""
        if self._capability_manager is None:
            # Lazy initialization
            from src.core.capability import CapabilityManager
            self._capability_manager = CapabilityManager(
                issuer_id=self.address,
                private_key=self.identity._signing_key,
                public_key=self.identity._verify_key,
            )
        return self._capability_manager
    
    def grant_capability(
        self,
        subject: str,
        scope: str,
        constraints: Optional[dict[str, Any]] = None,
        expires_in: int = 3600,
        delegatable: bool = False,
    ) -> Capability:
        """
        Grant a capability to another agent.
        
        Args:
            subject: DID of the recipient agent
            scope: Permission scope (e.g., "tools/filesystem/read")
            constraints: Additional restrictions (paths, rate limits, etc.)
            expires_in: Seconds until expiry (default: 1 hour)
            delegatable: Whether recipient can delegate to others
            
        Returns:
            Signed Capability token
            
        Example:
            cap = client.grant_capability(
                subject="did:talos:agent2",
                scope="tools/database/read",
                constraints={"tables": ["users", "products"]},
                expires_in=1800
            )
        """
        manager = self._ensure_capability_manager()
        return manager.grant(
            subject=subject,
            scope=scope,
            constraints=constraints,
            expires_in=expires_in,
            delegatable=delegatable,
        )
    
    def verify_capability(
        self,
        capability: Capability,
        requested_scope: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Verify a capability is valid.
        
        Checks signature, expiry, revocation, scope, and constraints.
        
        Args:
            capability: Capability to verify
            requested_scope: Specific scope being requested (optional)
            params: Request parameters for constraint checking (optional)
            
        Returns:
            True if valid
            
        Raises:
            CapabilityExpired: If capability has expired
            CapabilityRevoked: If capability was revoked
            CapabilityInvalid: If signature is invalid
            ScopeViolation: If scope/constraints don't match
        """
        manager = self._ensure_capability_manager()
        return manager.verify(
            capability=capability,
            requested_scope=requested_scope,
            params=params,
        )
    
    def revoke_capability(self, capability_id: str, reason: str) -> None:
        """
        Revoke a capability.
        
        Args:
            capability_id: ID of capability to revoke
            reason: Reason for revocation (for audit)
        """
        manager = self._ensure_capability_manager()
        manager.revoke(capability_id, reason)
    
    def delegate_capability(
        self,
        parent_capability: Capability,
        new_subject: str,
        narrowed_scope: Optional[str] = None,
        narrowed_constraints: Optional[dict[str, Any]] = None,
        expires_in: Optional[int] = None,
    ) -> Capability:
        """
        Delegate a capability to another subject with narrowing.
        
        The delegated capability can only have equal or narrower
        scope/constraints/expiry than the parent.
        
        Args:
            parent_capability: Capability to delegate from
            new_subject: DID of new recipient
            narrowed_scope: More specific scope (optional)
            narrowed_constraints: Additional constraints (optional)
            expires_in: Seconds until expiry (capped by parent)
            
        Returns:
            New delegated Capability
            
        Raises:
            CapabilityError: If parent is not delegatable
            ScopeViolation: If trying to broaden scope
        """
        manager = self._ensure_capability_manager()
        return manager.delegate(
            parent_capability=parent_capability,
            new_subject=new_subject,
            narrowed_scope=narrowed_scope,
            narrowed_constraints=narrowed_constraints,
            expires_in=expires_in,
        )
    
    def is_capability_revoked(self, capability_id: str) -> bool:
        """Check if a capability is revoked."""
        manager = self._ensure_capability_manager()
        return manager.is_revoked(capability_id)
    
    def list_granted_capabilities(self) -> list[Capability]:
        """List all capabilities this client has granted."""
        manager = self._ensure_capability_manager()
        return manager.list_issued()
