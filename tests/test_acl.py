"""
Tests for the ACL (Access Control List) System.

Tests cover:
- Permission patterns (wildcards, exact match)
- Allow/Deny precedence
- Rate limiting
- Resource access control
- Audit logging
"""

import pytest
import time
import tempfile
from pathlib import Path

from src.mcp_bridge.acl import (
    ACLManager,
    PeerPermissions,
    RateLimit,
    Permission,
    load_acl_from_file,
    save_acl_to_file,
)


class TestPeerPermissions:
    """Tests for PeerPermissions pattern matching."""
    
    def test_exact_tool_match(self):
        """Test exact tool name matching."""
        perms = PeerPermissions(
            peer_id="test",
            allow_tools=["file_read", "git_status"],
        )
        
        assert perms.matches_tool("file_read", "allow")
        assert perms.matches_tool("git_status", "allow")
        assert not perms.matches_tool("file_write", "allow")
    
    def test_wildcard_tool_match(self):
        """Test wildcard tool patterns."""
        perms = PeerPermissions(
            peer_id="test",
            allow_tools=["git_*", "*_read"],
            deny_tools=["rm_*"],
        )
        
        assert perms.matches_tool("git_status", "allow")
        assert perms.matches_tool("git_diff", "allow")
        assert perms.matches_tool("file_read", "allow")
        assert perms.matches_tool("rm_file", "deny")
        assert not perms.matches_tool("file_write", "allow")
    
    def test_resource_patterns(self):
        """Test resource path patterns."""
        perms = PeerPermissions(
            peer_id="test",
            allow_resources=["//localhost/repo/**", "//localhost/*.txt"],
            deny_resources=["**/.git/**"],
        )
        
        assert perms.matches_resource("//localhost/repo/src/main.py", "allow")
        assert perms.matches_resource("//localhost/file.txt", "allow")
        assert perms.matches_resource("//localhost/repo/.git/config", "deny")


class TestACLManager:
    """Tests for ACLManager."""
    
    @pytest.fixture
    def acl(self):
        """Create ACL with test permissions."""
        acl = ACLManager(default_allow=False)
        acl.add_peer(PeerPermissions(
            peer_id="allowed_peer",
            allow_tools=["file_read", "git_*"],
            deny_tools=["rm_*", "delete_*"],
            allow_resources=["//localhost/repo/**"],
        ))
        acl.add_peer(PeerPermissions(
            peer_id="disabled_peer",
            allow_tools=["*"],
            enabled=False,
        ))
        return acl
    
    def test_allow_tool(self, acl):
        """Test allowed tool access."""
        result = acl.check("allowed_peer", "tools/call", {"name": "file_read"})
        
        assert result.allowed
        assert result.permission == Permission.ALLOW
    
    def test_allow_wildcard_tool(self, acl):
        """Test wildcard tool pattern."""
        result = acl.check("allowed_peer", "tools/call", {"name": "git_status"})
        
        assert result.allowed
    
    def test_deny_tool(self, acl):
        """Test denied tool (deny takes precedence)."""
        result = acl.check("allowed_peer", "tools/call", {"name": "rm_file"})
        
        assert not result.allowed
        assert result.permission == Permission.DENY
        assert "deny pattern" in result.reason
    
    def test_unknown_peer_denied(self, acl):
        """Test unknown peer is denied by default."""
        result = acl.check("unknown_peer", "tools/call", {"name": "anything"})
        
        assert not result.allowed
        assert "not in ACL" in result.reason
    
    def test_disabled_peer_denied(self, acl):
        """Test disabled peer is denied."""
        result = acl.check("disabled_peer", "tools/call", {"name": "anything"})
        
        assert not result.allowed
        assert "disabled" in result.reason
    
    def test_resource_access(self, acl):
        """Test resource access control."""
        result = acl.check(
            "allowed_peer",
            "resources/read",
            {"uri": "//localhost/repo/src/main.py"}
        )
        
        assert result.allowed
    
    def test_resource_denied(self, acl):
        """Test resource access denied when no match."""
        result = acl.check(
            "allowed_peer",
            "resources/read",
            {"uri": "//localhost/secrets/key.pem"}
        )
        
        assert not result.allowed
    
    def test_default_allow_mode(self):
        """Test default allow mode."""
        acl = ACLManager(default_allow=True)
        
        result = acl.check("any_peer", "tools/call", {"name": "anything"})
        
        assert result.allowed
    
    def test_audit_log(self, acl):
        """Test audit logging."""
        acl.check("allowed_peer", "tools/call", {"name": "file_read"})
        acl.check("allowed_peer", "tools/call", {"name": "rm_file"})
        
        log = acl.get_audit_log()
        
        assert len(log) >= 2
        assert log[-1]["allowed"] == False  # rm_file denied
        assert log[-2]["allowed"] == True   # file_read allowed


class TestRateLimiting:
    """Tests for rate limiting."""
    
    def test_requests_per_minute_limit(self):
        """Test request rate limiting."""
        acl = ACLManager()
        acl.add_peer(PeerPermissions(
            peer_id="rate_limited",
            allow_tools=["*"],
            rate_limit=RateLimit(requests_per_minute=3),
        ))
        
        # First 3 requests should succeed
        for i in range(3):
            result = acl.check("rate_limited", "tools/call", {"name": "test"})
            assert result.allowed, f"Request {i+1} should be allowed"
        
        # 4th request should be rate limited
        result = acl.check("rate_limited", "tools/call", {"name": "test"})
        assert not result.allowed
        assert result.permission == Permission.RATE_LIMITED


class TestACLPersistence:
    """Tests for ACL file loading/saving."""
    
    def test_save_and_load(self):
        """Test saving and loading ACL config."""
        # Create ACL
        acl = ACLManager(default_allow=False)
        acl.add_peer(PeerPermissions(
            peer_id="test_peer",
            allow_tools=["file_*"],
            deny_tools=["rm_*"],
            rate_limit=RateLimit(requests_per_minute=30),
        ))
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        
        try:
            save_acl_to_file(acl, temp_path)
            
            # Load it back
            loaded_acl = load_acl_from_file(temp_path)
            
            assert "test_peer" in loaded_acl.peers
            perms = loaded_acl.peers["test_peer"]
            assert "file_*" in perms.allow_tools
            assert "rm_*" in perms.deny_tools
            assert perms.rate_limit.requests_per_minute == 30
        finally:
            Path(temp_path).unlink()
    
    def test_load_example_config(self):
        """Test loading the example config file."""
        config_path = Path("config/permissions.example.yaml")
        if config_path.exists():
            acl = load_acl_from_file(config_path)
            assert len(acl.peers) > 0


class TestACLIntegration:
    """Integration tests for ACL with proxy."""
    
    def test_export_to_dict(self):
        """Test exporting ACL configuration."""
        acl = ACLManager()
        acl.add_peer(PeerPermissions(
            peer_id="peer1",
            allow_tools=["tool1", "tool2"],
        ))
        
        config = acl.to_dict()
        
        assert "peers" in config
        assert "peer1" in config["peers"]
        assert config["peers"]["peer1"]["allow_tools"] == ["tool1", "tool2"]
