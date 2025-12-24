"""
Access Control List (ACL) System for MCP Security.

This module provides fine-grained permission control for MCP tool access:
- Per-peer permissions (tools, resources)
- Pattern-based allow/deny rules
- Rate limiting and quotas
- Audit logging

Usage:
    from src.mcp_bridge.acl import ACLManager, load_acl_from_file
    
    acl = load_acl_from_file("permissions.yaml")
    
    if acl.is_allowed(peer_id, "tools/call", {"name": "file_read"}):
        # Execute the tool
        pass
    else:
        # Reject the request
        pass
"""

import fnmatch
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional
import yaml

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permission types."""
    ALLOW = auto()
    DENY = auto()
    RATE_LIMITED = auto()


@dataclass
class RateLimit:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    data_bytes_per_day: int = 100_000_000  # 100MB
    max_execution_time_seconds: int = 30
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "requests_per_minute": self.requests_per_minute,
            "data_bytes_per_day": self.data_bytes_per_day,
            "max_execution_time_seconds": self.max_execution_time_seconds,
        }


@dataclass
class PeerPermissions:
    """Permissions for a specific peer."""
    peer_id: str
    allow_tools: list[str] = field(default_factory=list)  # Tool patterns to allow
    deny_tools: list[str] = field(default_factory=list)   # Tool patterns to deny
    allow_resources: list[str] = field(default_factory=list)  # Resource patterns
    deny_resources: list[str] = field(default_factory=list)
    rate_limit: Optional[RateLimit] = None
    enabled: bool = True
    
    def matches_tool(self, tool_name: str, action: str = "allow") -> bool:
        """Check if a tool name matches the allow/deny patterns."""
        patterns = self.allow_tools if action == "allow" else self.deny_tools
        return any(fnmatch.fnmatch(tool_name, pattern) for pattern in patterns)
    
    def matches_resource(self, resource_path: str, action: str = "allow") -> bool:
        """Check if a resource path matches the allow/deny patterns."""
        patterns = self.allow_resources if action == "allow" else self.deny_resources
        return any(fnmatch.fnmatch(resource_path, pattern) for pattern in patterns)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "allow_tools": self.allow_tools,
            "deny_tools": self.deny_tools,
            "allow_resources": self.allow_resources,
            "deny_resources": self.deny_resources,
            "rate_limit": self.rate_limit.to_dict() if self.rate_limit else None,
            "enabled": self.enabled,
        }


@dataclass
class ACLCheckResult:
    """Result of an ACL check."""
    allowed: bool
    permission: Permission
    reason: str
    peer_id: str
    method: str
    matched_rule: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "permission": self.permission.name,
            "reason": self.reason,
            "peer_id": self.peer_id,
            "method": self.method,
            "matched_rule": self.matched_rule,
        }


class ACLManager:
    """
    Manages Access Control Lists for MCP peers.
    
    Provides fine-grained access control:
    - Per-peer tool permissions
    - Per-peer resource access
    - Pattern-based rules (wildcards)
    - Rate limiting
    - Audit logging
    
    Rule Evaluation Order:
    1. Check if peer is enabled
    2. Check deny rules (explicit deny wins)
    3. Check allow rules
    4. Default to deny if no match
    
    Usage:
        acl = ACLManager()
        acl.add_peer(PeerPermissions(
            peer_id="abc123",
            allow_tools=["file_read", "git_*"],
            deny_tools=["rm_*", "delete_*"],
        ))
        
        result = acl.check(peer_id, "tools/call", {"name": "file_read"})
        if result.allowed:
            execute_tool()
    """
    
    def __init__(self, default_allow: bool = False):
        """
        Initialize ACL manager.
        
        Args:
            default_allow: If True, allow by default when no rules match.
                          Default is False (deny by default).
        """
        self.default_allow = default_allow
        self.peers: dict[str, PeerPermissions] = {}
        
        # Rate limiting state
        self._request_counts: dict[str, list[float]] = {}  # peer_id -> [timestamps]
        self._data_counts: dict[str, int] = {}  # peer_id -> bytes today
        self._last_reset: float = time.time()
        
        # Audit log
        self._audit_log: list[dict[str, Any]] = []
    
    def add_peer(self, permissions: PeerPermissions) -> None:
        """Add or update peer permissions."""
        self.peers[permissions.peer_id] = permissions
        logger.info(f"ACL: Added permissions for peer {permissions.peer_id[:16]}...")
    
    def remove_peer(self, peer_id: str) -> bool:
        """Remove peer from ACL."""
        if peer_id in self.peers:
            del self.peers[peer_id]
            logger.info(f"ACL: Removed peer {peer_id[:16]}...")
            return True
        return False
    
    def get_peer(self, peer_id: str) -> Optional[PeerPermissions]:
        """Get permissions for a peer."""
        return self.peers.get(peer_id)
    
    def check(
        self,
        peer_id: str,
        method: str,
        params: Optional[dict[str, Any]] = None,
    ) -> ACLCheckResult:
        """
        Check if a peer is allowed to perform an action.
        
        Args:
            peer_id: The peer's ID
            method: The MCP method (e.g., "tools/call", "resources/read")
            params: The method parameters
            
        Returns:
            ACLCheckResult with the decision and reason
        """
        params = params or {}
        
        # Check if peer exists in ACL
        perms = self.peers.get(peer_id)
        if perms is None:
            result = ACLCheckResult(
                allowed=self.default_allow,
                permission=Permission.ALLOW if self.default_allow else Permission.DENY,
                reason="Peer not in ACL" + (" (default allow)" if self.default_allow else " (default deny)"),
                peer_id=peer_id,
                method=method,
            )
            self._log_audit(result, params)
            return result
        
        # Check if peer is enabled
        if not perms.enabled:
            result = ACLCheckResult(
                allowed=False,
                permission=Permission.DENY,
                reason="Peer is disabled",
                peer_id=peer_id,
                method=method,
            )
            self._log_audit(result, params)
            return result
        
        # Check rate limits first
        if perms.rate_limit:
            rate_result = self._check_rate_limit(peer_id, perms.rate_limit)
            if not rate_result.allowed:
                self._log_audit(rate_result, params)
                return rate_result
        
        # Route to appropriate checker based on method
        if method == "tools/call":
            result = self._check_tool_access(perms, params)
        elif method in ("resources/read", "resources/list"):
            result = self._check_resource_access(perms, params)
        else:
            # Unknown method - use default
            result = ACLCheckResult(
                allowed=self.default_allow,
                permission=Permission.ALLOW if self.default_allow else Permission.DENY,
                reason=f"Unknown method: {method}",
                peer_id=peer_id,
                method=method,
            )
        
        result.peer_id = peer_id
        result.method = method
        self._log_audit(result, params)
        
        # Update rate limit counters if allowed
        if result.allowed and perms.rate_limit:
            self._record_request(peer_id)
        
        return result
    
    def _check_tool_access(
        self,
        perms: PeerPermissions,
        params: dict[str, Any],
    ) -> ACLCheckResult:
        """Check if tool access is allowed."""
        tool_name = params.get("name", "")
        
        # Check deny rules first (explicit deny wins)
        if perms.matches_tool(tool_name, "deny"):
            return ACLCheckResult(
                allowed=False,
                permission=Permission.DENY,
                reason=f"Tool '{tool_name}' matches deny pattern",
                peer_id=perms.peer_id,
                method="tools/call",
                matched_rule=f"deny:{tool_name}",
            )
        
        # Check allow rules
        if perms.matches_tool(tool_name, "allow"):
            return ACLCheckResult(
                allowed=True,
                permission=Permission.ALLOW,
                reason=f"Tool '{tool_name}' matches allow pattern",
                peer_id=perms.peer_id,
                method="tools/call",
                matched_rule=f"allow:{tool_name}",
            )
        
        # No match - use default
        return ACLCheckResult(
            allowed=self.default_allow,
            permission=Permission.ALLOW if self.default_allow else Permission.DENY,
            reason=f"No rule matches tool '{tool_name}'",
            peer_id=perms.peer_id,
            method="tools/call",
        )
    
    def _check_resource_access(
        self,
        perms: PeerPermissions,
        params: dict[str, Any],
    ) -> ACLCheckResult:
        """Check if resource access is allowed."""
        resource_uri = params.get("uri", "")
        
        # Check deny rules first
        if perms.matches_resource(resource_uri, "deny"):
            return ACLCheckResult(
                allowed=False,
                permission=Permission.DENY,
                reason=f"Resource '{resource_uri}' matches deny pattern",
                peer_id=perms.peer_id,
                method="resources/read",
                matched_rule=f"deny:{resource_uri}",
            )
        
        # Check allow rules
        if perms.matches_resource(resource_uri, "allow"):
            return ACLCheckResult(
                allowed=True,
                permission=Permission.ALLOW,
                reason=f"Resource '{resource_uri}' matches allow pattern",
                peer_id=perms.peer_id,
                method="resources/read",
                matched_rule=f"allow:{resource_uri}",
            )
        
        # No match - use default
        return ACLCheckResult(
            allowed=self.default_allow,
            permission=Permission.ALLOW if self.default_allow else Permission.DENY,
            reason=f"No rule matches resource '{resource_uri}'",
            peer_id=perms.peer_id,
            method="resources/read",
        )
    
    def _check_rate_limit(
        self,
        peer_id: str,
        rate_limit: RateLimit,
    ) -> ACLCheckResult:
        """Check if peer has exceeded rate limits."""
        now = time.time()
        
        # Reset daily counters if needed
        if now - self._last_reset > 86400:  # 24 hours
            self._data_counts.clear()
            self._last_reset = now
        
        # Check requests per minute
        if peer_id in self._request_counts:
            # Remove old timestamps
            minute_ago = now - 60
            self._request_counts[peer_id] = [
                t for t in self._request_counts[peer_id] if t > minute_ago
            ]
            
            if len(self._request_counts[peer_id]) >= rate_limit.requests_per_minute:
                return ACLCheckResult(
                    allowed=False,
                    permission=Permission.RATE_LIMITED,
                    reason=f"Rate limit exceeded: {rate_limit.requests_per_minute}/min",
                    peer_id=peer_id,
                    method="",
                )
        
        # Check data limit
        if self._data_counts.get(peer_id, 0) >= rate_limit.data_bytes_per_day:
            return ACLCheckResult(
                allowed=False,
                permission=Permission.RATE_LIMITED,
                reason=f"Data limit exceeded: {rate_limit.data_bytes_per_day} bytes/day",
                peer_id=peer_id,
                method="",
            )
        
        # Rate limit passed
        return ACLCheckResult(
            allowed=True,
            permission=Permission.ALLOW,
            reason="Rate limit OK",
            peer_id=peer_id,
            method="",
        )
    
    def _record_request(self, peer_id: str) -> None:
        """Record a request for rate limiting."""
        now = time.time()
        if peer_id not in self._request_counts:
            self._request_counts[peer_id] = []
        self._request_counts[peer_id].append(now)
    
    def record_data(self, peer_id: str, bytes_count: int) -> None:
        """Record data transfer for rate limiting."""
        if peer_id not in self._data_counts:
            self._data_counts[peer_id] = 0
        self._data_counts[peer_id] += bytes_count
    
    def _log_audit(self, result: ACLCheckResult, params: dict[str, Any]) -> None:
        """Log access attempt to audit log."""
        entry = {
            "timestamp": time.time(),
            **result.to_dict(),
            "params": params,
        }
        self._audit_log.append(entry)
        
        # Keep only last 1000 entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
        
        # Log to logger
        level = logging.DEBUG if result.allowed else logging.WARNING
        logger.log(level, f"ACL: {result.peer_id[:16]}... {result.method} -> {result.permission.name}: {result.reason}")
    
    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent audit log entries."""
        return self._audit_log[-limit:]
    
    def to_dict(self) -> dict[str, Any]:
        """Export ACL configuration to dict."""
        return {
            "default_allow": self.default_allow,
            "peers": {pid: p.to_dict() for pid, p in self.peers.items()},
        }


def load_acl_from_file(path: str | Path) -> ACLManager:
    """
    Load ACL configuration from a YAML file.
    
    Expected format:
    ```yaml
    default_allow: false
    peers:
      <PEER_ID>:
        enabled: true
        allow_tools:
          - "file_read"
          - "git_*"
        deny_tools:
          - "rm_*"
          - "delete_*"
        allow_resources:
          - "//localhost/repo/**"
        rate_limit:
          requests_per_minute: 60
          data_bytes_per_day: 100000000
    ```
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Configured ACLManager
    """
    path = Path(path)
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    acl = ACLManager(default_allow=config.get("default_allow", False))
    
    for peer_id, peer_config in config.get("peers", {}).items():
        rate_limit = None
        if "rate_limit" in peer_config:
            rl = peer_config["rate_limit"]
            rate_limit = RateLimit(
                requests_per_minute=rl.get("requests_per_minute", 60),
                data_bytes_per_day=rl.get("data_bytes_per_day", 100_000_000),
                max_execution_time_seconds=rl.get("max_execution_time_seconds", 30),
            )
        
        perms = PeerPermissions(
            peer_id=peer_id,
            allow_tools=peer_config.get("allow_tools", []),
            deny_tools=peer_config.get("deny_tools", []),
            allow_resources=peer_config.get("allow_resources", []),
            deny_resources=peer_config.get("deny_resources", []),
            rate_limit=rate_limit,
            enabled=peer_config.get("enabled", True),
        )
        acl.add_peer(perms)
    
    logger.info(f"Loaded ACL from {path}: {len(acl.peers)} peers")
    return acl


def save_acl_to_file(acl: ACLManager, path: str | Path) -> None:
    """Save ACL configuration to a YAML file."""
    path = Path(path)
    
    config = {
        "default_allow": acl.default_allow,
        "peers": {},
    }
    
    for peer_id, perms in acl.peers.items():
        peer_config = {
            "enabled": perms.enabled,
            "allow_tools": perms.allow_tools,
            "deny_tools": perms.deny_tools,
            "allow_resources": perms.allow_resources,
            "deny_resources": perms.deny_resources,
        }
        if perms.rate_limit:
            peer_config["rate_limit"] = perms.rate_limit.to_dict()
        config["peers"][peer_id] = peer_config
    
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Saved ACL to {path}")
