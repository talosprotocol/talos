"""
Gateway for Talos Protocol (Phase 3).

Central enforcement proxy for multi-tenant capability routing.
Protocol usable without it - this is an optional enterprise feature.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from .capability import CapabilityManager, AuthorizationResult
from .audit_plane import AuditAggregator
from .rate_limiter import SessionRateLimiter, RateLimitConfig


logger = logging.getLogger(__name__)


class GatewayStatus(Enum):
    """Gateway operational status."""
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


@dataclass
class TenantConfig:
    """Configuration for a tenant in the gateway."""
    tenant_id: str
    capability_manager: CapabilityManager
    rate_limit_config: Optional[RateLimitConfig] = None
    max_concurrent_sessions: int = 1000
    allowed_tools: Optional[list[str]] = None  # None = all tools allowed


@dataclass
class GatewayRequest:
    """Request passing through the gateway."""
    request_id: str
    tenant_id: str
    session_id: bytes
    tool: str
    method: str
    params: Optional[dict] = None
    capability_data: Optional[dict] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GatewayResponse:
    """Response from the gateway."""
    request_id: str
    allowed: bool
    result: Optional[AuthorizationResult] = None
    error: Optional[str] = None
    latency_us: int = 0


class Gateway:
    """
    Central enforcement proxy for multi-tenant capability routing.
    
    Features:
    - Multi-tenant isolation
    - Per-tenant rate limiting
    - Centralized audit aggregation
    - Health monitoring
    """

    def __init__(
        self,
        audit_aggregator: Optional[AuditAggregator] = None,
        default_rate_config: Optional[RateLimitConfig] = None,
    ):
        self._tenants: dict[str, TenantConfig] = {}
        self._rate_limiters: dict[str, SessionRateLimiter] = {}
        self._audit = audit_aggregator or AuditAggregator()
        self._default_rate_config = default_rate_config or RateLimitConfig()
        self._status = GatewayStatus.STOPPED
        self._requests_processed = 0
        self._started_at: Optional[datetime] = None

    def register_tenant(self, config: TenantConfig) -> None:
        """Register a tenant with the gateway."""
        if config.tenant_id in self._tenants:
            raise ValueError(f"Tenant {config.tenant_id} already registered")
        
        self._tenants[config.tenant_id] = config
        
        # Create rate limiter for tenant
        rate_config = config.rate_limit_config or self._default_rate_config
        self._rate_limiters[config.tenant_id] = SessionRateLimiter(rate_config)
        
        logger.info(f"Registered tenant: {config.tenant_id}")

    def unregister_tenant(self, tenant_id: str) -> bool:
        """Unregister a tenant."""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            if tenant_id in self._rate_limiters:
                del self._rate_limiters[tenant_id]
            logger.info(f"Unregistered tenant: {tenant_id}")
            return True
        return False

    def start(self) -> None:
        """Start the gateway."""
        self._status = GatewayStatus.RUNNING
        self._started_at = datetime.now(timezone.utc)
        logger.info("Gateway started")

    def stop(self) -> None:
        """Stop the gateway."""
        self._status = GatewayStatus.STOPPED
        logger.info("Gateway stopped")

    def authorize(self, request: GatewayRequest) -> GatewayResponse:
        """
        Authorize a request through the gateway.
        
        Performs:
        1. Tenant lookup
        2. Rate limit check
        3. Tool allowlist check
        4. Capability authorization
        5. Audit recording
        """
        import time
        start_time = time.perf_counter_ns()

        # Check gateway status
        if self._status != GatewayStatus.RUNNING:
            return GatewayResponse(
                request_id=request.request_id,
                allowed=False,
                error=f"Gateway not running: {self._status.value}",
            )

        # Tenant lookup
        tenant = self._tenants.get(request.tenant_id)
        if not tenant:
            return GatewayResponse(
                request_id=request.request_id,
                allowed=False,
                error=f"Unknown tenant: {request.tenant_id}",
            )

        # Rate limit check
        rate_limiter = self._rate_limiters.get(request.tenant_id)
        if rate_limiter and not rate_limiter.allow(request.session_id):
            latency_us = (time.perf_counter_ns() - start_time) // 1000
            self._audit.record_authorization(
                agent_id=request.tenant_id,
                tool=request.tool,
                method=request.method,
                capability_id=None,
                allowed=False,
                denial_reason="RATE_LIMITED",
                latency_us=latency_us,
            )
            return GatewayResponse(
                request_id=request.request_id,
                allowed=False,
                error="Rate limit exceeded",
                latency_us=latency_us,
            )

        # Tool allowlist check
        if tenant.allowed_tools and request.tool not in tenant.allowed_tools:
            latency_us = (time.perf_counter_ns() - start_time) // 1000
            self._audit.record_authorization(
                agent_id=request.tenant_id,
                tool=request.tool,
                method=request.method,
                capability_id=None,
                allowed=False,
                denial_reason="TOOL_NOT_ALLOWED",
                latency_us=latency_us,
            )
            return GatewayResponse(
                request_id=request.request_id,
                allowed=False,
                error=f"Tool not allowed: {request.tool}",
                latency_us=latency_us,
            )

        # Try fast path first
        result = tenant.capability_manager.authorize_fast(
            session_id=request.session_id,
            tool=request.tool,
            method=request.method,
            params=request.params,
        )

        latency_us = (time.perf_counter_ns() - start_time) // 1000
        self._requests_processed += 1

        # Record audit event
        self._audit.record_authorization(
            agent_id=request.tenant_id,
            tool=request.tool,
            method=request.method,
            capability_id=result.capability_id,
            allowed=result.allowed,
            denial_reason=result.reason.value if result.reason else None,
            latency_us=latency_us,
            session_id=request.session_id.hex(),
        )

        return GatewayResponse(
            request_id=request.request_id,
            allowed=result.allowed,
            result=result,
            latency_us=latency_us,
        )

    def get_health(self) -> dict:
        """Get gateway health status."""
        return {
            "status": self._status.value,
            "tenants": len(self._tenants),
            "requests_processed": self._requests_processed,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "uptime_seconds": (
                (datetime.now(timezone.utc) - self._started_at).total_seconds()
                if self._started_at and self._status == GatewayStatus.RUNNING
                else 0
            ),
        }

    def get_tenant_stats(self, tenant_id: str) -> Optional[dict]:
        """Get statistics for a specific tenant."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None

        rate_limiter = self._rate_limiters.get(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "allowed_tools": tenant.allowed_tools,
            "max_concurrent_sessions": tenant.max_concurrent_sessions,
            "rate_limiter": rate_limiter.get_stats() if rate_limiter else None,
        }

    @property
    def status(self) -> GatewayStatus:
        return self._status

    @property
    def tenant_count(self) -> int:
        return len(self._tenants)
