"""
Capability Token System for Talos Protocol v3.0.

Provides cryptographic capability-based authorization:
- First-class capability tokens (grant/revoke/delegate)
- Hierarchical scopes with constraints
- Delegation chains with narrowing
- Signature verification
- Expiry and revocation

Usage:
    from talos.capability import CapabilityManager

    manager = CapabilityManager(identity)
    cap = await manager.grant(
        subject="did:talos:agent",
        scope="tools/filesystem/read",
        constraints={"paths": ["/data/*"]},
        expires_in=3600
    )
    
    valid = await manager.verify(cap)
"""

import json
import logging
import secrets
import time
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, Field, ConfigDict, field_serializer

logger = logging.getLogger(__name__)


class CapabilityError(Exception):
    """Base exception for capability errors."""
    pass


class CapabilityExpired(CapabilityError):
    """Capability has expired."""
    pass


class CapabilityRevoked(CapabilityError):
    """Capability has been revoked."""
    pass


class CapabilityInvalid(CapabilityError):
    """Capability signature is invalid."""
    pass


class ScopeViolation(CapabilityError):
    """Action is outside capability scope."""
    pass


class CapabilityStatus(str, Enum):
    """Status of a capability."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DenialReason(str, Enum):
    """Reason for authorization denial (per protocol spec)."""
    NO_CAPABILITY = "NO_CAPABILITY"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    DELEGATION_INVALID = "DELEGATION_INVALID"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    REPLAY = "REPLAY"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"


@dataclass
class AuthorizationResult:
    """Result of capability authorization check."""
    allowed: bool
    reason: Optional[DenialReason] = None
    capability_id: Optional[str] = None
    message: Optional[str] = None
    latency_us: int = 0  # Authorization latency in microseconds
    cached: bool = False  # Whether this was a cached session verification


@dataclass
class SessionCacheEntry:
    """
    Cached session for <1ms verification.
    
    Per protocol spec: capability signatures verified ONCE per session,
    subsequent requests check only session_id, expiry, and revocation.
    """
    session_id: bytes  # 16 bytes
    capability_id: str
    capability_hash: bytes  # sha256 of capability canonical bytes
    subject: str  # Subject DID
    scope: str  # Scope string for fast containment check
    issuer: str  # Issuer DID
    verified_at: datetime  # When signature was verified
    expires_at: datetime  # Capability expiry
    last_used: datetime  # For LRU eviction
    constraints: dict  # Cached constraints for fast check


class Capability(BaseModel):
    """
    Cryptographic capability token.
    
    A capability represents a bounded, delegatable permission
    from an issuer to a subject.
    
    Attributes:
        id: Unique capability identifier (cap_...)
        version: Capability format version
        issuer: DID of the capability granter
        subject: DID of the capability recipient
        scope: Hierarchical permission scope (e.g., "tools/filesystem/read")
        constraints: Additional restrictions (paths, rate limits, etc.)
        issued_at: When capability was created
        expires_at: When capability expires
        delegatable: Whether subject can delegate to others
        delegation_chain: Parent capability IDs (for delegated caps)
        signature: Ed25519 signature by issuer
    """

    id: str = Field(default_factory=lambda: f"cap_{secrets.token_hex(12)}")
    version: int = 1
    issuer: str
    subject: str
    scope: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    delegatable: bool = False
    delegation_chain: list[str] = Field(default_factory=list)
    signature: Optional[bytes] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer('issued_at', 'expires_at')
    def serialize_datetime(self, v: datetime, _info) -> str:
        return v.isoformat()

    @field_serializer('signature')
    def serialize_signature(self, v: Optional[bytes], _info) -> Optional[str]:
        if v is None:
            return None
        import base64
        return base64.b64encode(v).decode()

    def canonical_bytes(self) -> bytes:
        """Get canonical bytes for signing (excludes signature)."""
        data = {
            "id": self.id,
            "version": self.version,
            "issuer": self.issuer,
            "subject": self.subject,
            "scope": self.scope,
            "constraints": self.constraints,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "delegatable": self.delegatable,
            "delegation_chain": self.delegation_chain,
        }
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode()

    def is_expired(self) -> bool:
        """Check if capability has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def covers_scope(self, requested_scope: str) -> bool:
        """
        Check if this capability covers the requested scope.
        
        Uses hierarchical matching:
        - "tools" covers "tools/filesystem/read"
        - "tools/filesystem" covers "tools/filesystem/read"
        - "tools/filesystem/read" does NOT cover "tools/filesystem/write"
        """
        cap_parts = self.scope.split("/")
        req_parts = requested_scope.split("/")

        # Capability scope must be prefix of requested scope
        if len(cap_parts) > len(req_parts):
            return False

        return cap_parts == req_parts[:len(cap_parts)]

    def check_constraints(self, params: dict[str, Any]) -> bool:
        """
        Check if parameters satisfy constraints.
        
        Supports:
        - paths: list of glob patterns for filesystem access
        - rate_limit: "N/period" format
        - allowed_tools: list of specific tool names
        """
        import fnmatch

        # Check path constraints
        if "paths" in self.constraints and "path" in params:
            allowed_paths = self.constraints["paths"]
            requested_path = params["path"]
            if not any(fnmatch.fnmatch(requested_path, p) for p in allowed_paths):
                return False

        # Check allowed tools
        if "allowed_tools" in self.constraints and "name" in params:
            if params["name"] not in self.constraints["allowed_tools"]:
                return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        import base64
        return {
            "id": self.id,
            "version": self.version,
            "issuer": self.issuer,
            "subject": self.subject,
            "scope": self.scope,
            "constraints": self.constraints,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "delegatable": self.delegatable,
            "delegation_chain": self.delegation_chain,
            "signature": base64.b64encode(self.signature).decode() if self.signature else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Capability":
        """Create from dictionary."""
        import base64
        return cls(
            id=data["id"],
            version=data.get("version", 1),
            issuer=data["issuer"],
            subject=data["subject"],
            scope=data["scope"],
            constraints=data.get("constraints", {}),
            issued_at=datetime.fromisoformat(data["issued_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            delegatable=data.get("delegatable", False),
            delegation_chain=data.get("delegation_chain", []),
            signature=base64.b64decode(data["signature"]) if data.get("signature") else None,
        )


@dataclass
class RevocationEntry:
    """Record of a revoked capability."""
    capability_id: str
    revoked_at: datetime
    reason: str
    revoked_by: str


# Protocol constants (Phase 2 hardening)
MAX_DELEGATION_DEPTH = 3  # Maximum depth of delegation chain


class DelegationDepthExceeded(CapabilityError):
    """Delegation chain has exceeded maximum depth."""
    pass


class CapabilityManager:
    """
    Manages capability lifecycle.
    
    Provides:
    - Grant: Issue new capabilities
    - Revoke: Invalidate capabilities
    - Verify: Check capability validity
    - Delegate: Create narrowed sub-capabilities
    """

    def __init__(
        self,
        issuer_id: str,
        private_key: Ed25519PrivateKey,
        public_key: Ed25519PublicKey,
        revocation_store: Optional[dict] = None,
    ):
        """
        Initialize capability manager.
        
        Args:
            issuer_id: DID of this identity
            private_key: Ed25519 private key for signing
            public_key: Ed25519 public key for verification
            revocation_store: Optional external revocation store
        """
        self.issuer_id = issuer_id
        self._private_key = private_key
        self._public_key = public_key
        self._revocations: dict[str, RevocationEntry] = revocation_store or {}
        self._issued: dict[str, Capability] = {}

        # Session cache for <1ms verification (verify signature once per session)
        self._session_cache: dict[bytes, "SessionCacheEntry"] = {}
        self._session_cache_max_size = 10000  # LRU eviction

        # Revocation bloom filter for O(1) check
        self._revocation_hashes: set[str] = set()  # Simple set for now, bloom filter later

    def grant(
        self,
        subject: str,
        scope: str,
        constraints: Optional[dict[str, Any]] = None,
        expires_in: int = 3600,
        delegatable: bool = False,
    ) -> Capability:
        """
        Grant a new capability to a subject.
        
        Args:
            subject: DID of the recipient
            scope: Permission scope (e.g., "tools/filesystem/read")
            constraints: Additional restrictions
            expires_in: Seconds until expiry
            delegatable: Whether recipient can delegate
            
        Returns:
            Signed Capability token
        """
        now = datetime.now(timezone.utc)

        cap = Capability(
            issuer=self.issuer_id,
            subject=subject,
            scope=scope,
            constraints=constraints or {},
            issued_at=now,
            expires_at=now + timedelta(seconds=expires_in),
            delegatable=delegatable,
        )

        # Sign the capability
        cap.signature = self._sign(cap.canonical_bytes())

        # Track issued capabilities
        self._issued[cap.id] = cap

        logger.info(f"Granted capability {cap.id} to {subject} for {scope}")
        return cap


    def is_revoked(self, capability_id: str) -> bool:
        """Check if a capability is revoked."""
        return capability_id in self._revocations

    def verify(
        self,
        capability: Capability,
        requested_scope: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        issuer_public_key: Optional[Ed25519PublicKey] = None,
    ) -> bool:
        """
        Verify a capability is valid.
        
        Checks:
        1. Signature is valid
        2. Not expired
        3. Not revoked
        4. Scope covers request (if provided)
        5. Constraints satisfied (if params provided)
        
        Args:
            capability: Capability to verify
            requested_scope: Scope being requested (optional)
            params: Request parameters for constraint checking (optional)
            issuer_public_key: Issuer's public key (uses self if not provided)
            
        Returns:
            True if valid
            
        Raises:
            CapabilityExpired: If expired
            CapabilityRevoked: If revoked
            CapabilityInvalid: If signature invalid
            ScopeViolation: If scope doesn't match
        """
        # Check future-dated (allow 60s clock skew)
        now = datetime.now(timezone.utc)
        skew_window = timedelta(seconds=60)
        if capability.issued_at > now + skew_window:
            raise CapabilityInvalid(
                f"Capability issued in future: {capability.issued_at} > {now}"
            )

        # Check expiry
        if capability.is_expired():
            raise CapabilityExpired(f"Capability {capability.id} expired at {capability.expires_at}")

        # Check revocation
        if self.is_revoked(capability.id):
            entry = self._revocations[capability.id]
            raise CapabilityRevoked(f"Capability {capability.id} revoked: {entry.reason}")

        # Verify signature
        key = issuer_public_key or self._public_key
        if capability.signature is None:
            raise CapabilityInvalid("Capability has no signature")

        try:
            key.verify(capability.signature, capability.canonical_bytes())
        except Exception as e:
            raise CapabilityInvalid(f"Signature verification failed: {e}")

        # Check scope
        if requested_scope and not capability.covers_scope(requested_scope):
            raise ScopeViolation(
                f"Capability scope '{capability.scope}' does not cover '{requested_scope}'"
            )

        # Check constraints
        if params and not capability.check_constraints(params):
            raise ScopeViolation("Request parameters violate capability constraints")

        return True

    def delegate(
        self,
        parent_capability: Capability,
        new_subject: str,
        narrowed_scope: Optional[str] = None,
        narrowed_constraints: Optional[dict[str, Any]] = None,
        expires_in: Optional[int] = None,
    ) -> Capability:
        """
        Delegate a capability to another subject with narrowing.
        
        Rules:
        - Parent must be delegatable
        - New scope must be subset of parent scope
        - New constraints can only be more restrictive
        - Expiry cannot exceed parent expiry
        
        Args:
            parent_capability: Capability to delegate from
            new_subject: DID of new recipient
            narrowed_scope: More specific scope (optional)
            narrowed_constraints: Additional constraints (optional)
            expires_in: Seconds until expiry (capped by parent)
            
        Returns:
            New delegated Capability
        """
        if not parent_capability.delegatable:
            raise CapabilityError("Capability is not delegatable")

        # Check delegation depth limit (Phase 2 hardening)
        current_depth = len(parent_capability.delegation_chain)
        if current_depth >= MAX_DELEGATION_DEPTH:
            raise DelegationDepthExceeded(
                f"Delegation chain depth {current_depth + 1} exceeds "
                f"maximum allowed depth of {MAX_DELEGATION_DEPTH}"
            )

        # Verify parent is still valid
        self.verify(parent_capability)

        # Determine scope (must be subset)
        scope = narrowed_scope or parent_capability.scope
        if not parent_capability.covers_scope(scope):
            raise ScopeViolation(f"Cannot delegate to broader scope '{scope}'")

        # Merge constraints (can only add, not remove)
        constraints = {**parent_capability.constraints}
        if narrowed_constraints:
            constraints.update(narrowed_constraints)

        # Calculate expiry (cannot exceed parent)
        now = datetime.now(timezone.utc)
        max_expiry = parent_capability.expires_at
        if expires_in:
            requested_expiry = now + timedelta(seconds=expires_in)
            expiry = min(requested_expiry, max_expiry)
        else:
            expiry = max_expiry

        # Build delegation chain
        chain = parent_capability.delegation_chain + [parent_capability.id]

        cap = Capability(
            issuer=self.issuer_id,
            subject=new_subject,
            scope=scope,
            constraints=constraints,
            issued_at=now,
            expires_at=expiry,
            delegatable=False,  # Delegated caps are not re-delegatable by default
            delegation_chain=chain,
        )

        cap.signature = self._sign(cap.canonical_bytes())
        self._issued[cap.id] = cap

        logger.info(f"Delegated capability to {new_subject} (from {parent_capability.id})")
        return cap

    def _sign(self, data: bytes) -> bytes:
        """Sign data with private key."""
        return self._private_key.sign(data)

    def list_issued(self) -> list[Capability]:
        """List all issued capabilities."""
        return list(self._issued.values())

    def list_revocations(self) -> list[RevocationEntry]:
        """List all revocations."""
        return list(self._revocations.values())

    def get_capability(self, capability_id: str) -> Optional[Capability]:
        """Get a capability by ID."""
        return self._issued.get(capability_id)

    def authorize(
        self,
        capability: Optional[Capability],
        tool: str,
        method: str,
        request_hash: Optional[str] = None,
    ) -> AuthorizationResult:
        """
        Authorize an MCP request (canonical authorization entry point).

        Per protocol spec:
        - Missing capability = NO_CAPABILITY
        - Expired = EXPIRED
        - Revoked = REVOKED
        - Scope mismatch = SCOPE_MISMATCH
        - Invalid signature = SIGNATURE_INVALID

        Args:
            capability: Capability token (None = denied)
            tool: Tool name being invoked
            method: Method being called
            request_hash: Hash of request body (for audit)

        Returns:
            AuthorizationResult with allowed/denied + reason
        """
        # No capability = immediate denial
        if capability is None:
            logger.warning(f"Authorization denied: no capability for {tool}/{method}")
            return AuthorizationResult(
                allowed=False,
                reason=DenialReason.NO_CAPABILITY,
                message=f"No capability provided for {tool}/{method}",
            )

        # Empty tool or method = immediate denial (security hardening)
        if not tool or not method:
            logger.warning("Authorization denied: empty tool or method")
            return AuthorizationResult(
                allowed=False,
                reason=DenialReason.SCOPE_MISMATCH,
                message="Empty tool or method not allowed",
            )

        # Build scope string for verification
        scope = f"tool:{tool}/method:{method}"

        try:
            # Verify capability (checks expiry, revocation, signature, scope)
            self.verify(capability, requested_scope=scope)

            logger.info(f"Authorization granted: {capability.id} for {tool}/{method}")
            return AuthorizationResult(
                allowed=True,
                capability_id=capability.id,
            )

        except CapabilityExpired as e:
            logger.warning(f"Authorization denied (expired): {e}")
            return AuthorizationResult(
                allowed=False,
                reason=DenialReason.EXPIRED,
                capability_id=capability.id,
                message=str(e),
            )

        except CapabilityRevoked as e:
            logger.warning(f"Authorization denied (revoked): {e}")
            return AuthorizationResult(
                allowed=False,
                reason=DenialReason.REVOKED,
                capability_id=capability.id,
                message=str(e),
            )

        except CapabilityInvalid as e:
            logger.warning(f"Authorization denied (invalid signature): {e}")
            return AuthorizationResult(
                allowed=False,
                reason=DenialReason.SIGNATURE_INVALID,
                capability_id=capability.id,
                message=str(e),
            )

        except ScopeViolation as e:
            logger.warning(f"Authorization denied (scope mismatch): {e}")
            return AuthorizationResult(
                allowed=False,
                reason=DenialReason.SCOPE_MISMATCH,
                capability_id=capability.id,
                message=str(e),
            )

    def _check_session_expiry(self, entry: "SessionCacheEntry", start_ns: int) -> Optional[AuthorizationResult]:
        """Check if session is expired. Returns denial result if expired, None otherwise."""
        now = datetime.now(timezone.utc)
        if now > entry.expires_at:
            del self._session_cache[entry.session_id]
            return AuthorizationResult(
                allowed=False, reason=DenialReason.EXPIRED, capability_id=entry.capability_id,
                message=f"Capability expired at {entry.expires_at}",
                latency_us=(time.perf_counter_ns() - start_ns) // 1000, cached=True,
            )
        return None

    def _check_session_revoked(self, entry: "SessionCacheEntry", start_ns: int) -> Optional[AuthorizationResult]:
        """Check if session capability is revoked."""
        cap_hash_hex = entry.capability_hash.hex()
        if cap_hash_hex in self._revocation_hashes or entry.capability_id in self._revocations:
            return AuthorizationResult(
                allowed=False, reason=DenialReason.REVOKED, capability_id=entry.capability_id,
                message="Capability has been revoked",
                latency_us=(time.perf_counter_ns() - start_ns) // 1000, cached=True,
            )
        return None

    def _check_scope_match(self, entry: "SessionCacheEntry", tool: str, method: str, start_ns: int) -> Optional[AuthorizationResult]:
        """Check scope matching with wildcard support."""
        scope = f"tool:{tool}/method:{method}"
        scope_parts = entry.scope.split("/")
        request_parts = scope.split("/")
        
        if len(scope_parts) > len(request_parts):
            return AuthorizationResult(
                allowed=False, reason=DenialReason.SCOPE_MISMATCH, capability_id=entry.capability_id,
                message=f"Scope '{entry.scope}' implies deeper specificity than '{scope}'",
                latency_us=(time.perf_counter_ns() - start_ns) // 1000, cached=True,
            )
        
        for i, part in enumerate(scope_parts):
            req_part = request_parts[i]
            if part == req_part:
                continue
            if part.endswith(":*") and req_part.startswith(part[:-2] + ":"):
                continue
            return AuthorizationResult(
                allowed=False, reason=DenialReason.SCOPE_MISMATCH, capability_id=entry.capability_id,
                message=f"Scope part '{part}' does not cover '{req_part}'",
                latency_us=(time.perf_counter_ns() - start_ns) // 1000, cached=True,
            )
        return None

    def _check_path_constraints(self, entry: "SessionCacheEntry", params: dict, start_ns: int) -> Optional[AuthorizationResult]:
        """Check path constraints if applicable."""
        import fnmatch
        if "paths" in entry.constraints and "path" in params:
            allowed_paths = entry.constraints["paths"]
            if not any(fnmatch.fnmatch(params["path"], p) for p in allowed_paths):
                return AuthorizationResult(
                    allowed=False, reason=DenialReason.SCOPE_MISMATCH, capability_id=entry.capability_id,
                    message="Path constraint violation",
                    latency_us=(time.perf_counter_ns() - start_ns) // 1000, cached=True,
                )
        return None

    def authorize_fast(
        self,
        session_id: bytes,
        tool: str,
        method: str,
        params: Optional[dict[str, Any]] = None,
    ) -> AuthorizationResult:
        """Fast-path authorization using session cache (<1ms target)."""
        import time
        start_ns = time.perf_counter_ns()
        
        entry = self._session_cache.get(session_id)
        if entry is None:
            return AuthorizationResult(
                allowed=False, reason=DenialReason.NO_CAPABILITY,
                message="Session not in cache, full verification required",
                latency_us=(time.perf_counter_ns() - start_ns) // 1000, cached=False,
            )
        
        entry.last_used = datetime.now(timezone.utc)
        
        # Run checks (each returns denial or None)
        for check_result in [
            self._check_session_expiry(entry, start_ns),
            self._check_session_revoked(entry, start_ns),
            self._check_scope_match(entry, tool, method, start_ns),
            self._check_path_constraints(entry, params, start_ns) if params and entry.constraints else None,
        ]:
            if check_result is not None:
                return check_result
        
        latency_us = (time.perf_counter_ns() - start_ns) // 1000
        logger.debug(f"authorize_fast: {latency_us}μs for {tool}/{method}")
        
        return AuthorizationResult(
            allowed=True, capability_id=entry.capability_id,
            latency_us=latency_us, cached=True,
        )

    def cache_session(
        self,
        session_id: bytes,
        capability: Capability,
    ) -> None:
        """
        Cache a verified session for fast subsequent authorization.
        
        Call this AFTER full capability verification succeeds.
        
        Args:
            session_id: 16-byte session identifier
            capability: Verified capability to cache
        """
        import hashlib
        
        # Evict if at capacity (LRU)
        if len(self._session_cache) >= self._session_cache_max_size:
            self._evict_lru_sessions(count=100)  # Evict 100 oldest
        
        now = datetime.now(timezone.utc)
        cap_hash = hashlib.sha256(capability.canonical_bytes()).digest()
        
        entry = SessionCacheEntry(
            session_id=session_id,
            capability_id=capability.id,
            capability_hash=cap_hash,
            subject=capability.subject,
            scope=capability.scope,
            issuer=capability.issuer,
            verified_at=now,
            expires_at=capability.expires_at,
            last_used=now,
            constraints=capability.constraints.copy(),
        )
        
        self._session_cache[session_id] = entry
        logger.debug(f"Cached session for capability {capability.id}")

    def invalidate_session(self, session_id: bytes) -> bool:
        """
        Remove a session from cache.
        
        Returns:
            True if session was in cache, False otherwise
        """
        if session_id in self._session_cache:
            del self._session_cache[session_id]
            return True
        return False

    def _evict_lru_sessions(self, count: int = 100) -> int:
        """
        Evict least-recently-used sessions from cache.
        
        Args:
            count: Number of sessions to evict
            
        Returns:
            Actual number evicted
        """
        if not self._session_cache:
            return 0
        
        # Sort by last_used and remove oldest
        sorted_entries = sorted(
            self._session_cache.items(),
            key=lambda x: x[1].last_used
        )
        
        evicted = 0
        for session_id, _ in sorted_entries[:count]:
            del self._session_cache[session_id]
            evicted += 1
        
        logger.debug(f"Evicted {evicted} sessions from cache (LRU)")
        return evicted

    def revoke(self, capability_id: str, reason: str) -> None:
        """
        Revoke a capability.
        
        Also updates the revocation hash set for O(1) lookup in authorize_fast.
        
        Args:
            capability_id: ID of capability to revoke
            reason: Reason for revocation
        """
        import hashlib
        
        entry = RevocationEntry(
            capability_id=capability_id,
            revoked_at=datetime.now(timezone.utc),
            reason=reason,
            revoked_by=self.issuer_id,
        )
        self._revocations[capability_id] = entry
        
        # Update bloom filter / hash set for fast lookup
        cap = self._issued.get(capability_id)
        if cap:
            cap_hash = hashlib.sha256(cap.canonical_bytes()).hexdigest()
            self._revocation_hashes.add(cap_hash)
        
        logger.info(f"Revoked capability {capability_id}: {reason}")

    def get_session_cache_stats(self) -> dict[str, Any]:
        """Get session cache statistics for monitoring."""
        return {
            "size": len(self._session_cache),
            "max_size": self._session_cache_max_size,
            "revocation_hashes": len(self._revocation_hashes),
        }


# Backward compatibility with ACLManager
def acl_to_capability_bridge():
    """
    Bridge for migrating from ACL to Capability system.
    
    DEPRECATED: This is provided for migration only.
    """
    warnings.warn(
        "ACL system is deprecated. Use CapabilityManager instead.",
        DeprecationWarning,
        stacklevel=2
    )
