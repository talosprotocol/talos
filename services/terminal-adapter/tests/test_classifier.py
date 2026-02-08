"""Tests for the CommandClassifier."""

import pytest
from terminal_adapter.domain import (
    CommandClassifier,
    RiskLevel,
    PolicyManifest,
)


class TestCommandClassifier:
    """Test command classification logic."""
    
    @pytest.fixture
    def classifier(self):
        """Create a default classifier."""
        return CommandClassifier()
    
    # ========================================================================
    # READ Commands
    # ========================================================================
    
    def test_ls_is_read(self, classifier):
        result = classifier.classify("ls", ["-la"])
        assert result.risk_level == RiskLevel.READ
        assert not result.is_blocked
    
    def test_cat_is_read(self, classifier):
        result = classifier.classify("cat", ["file.txt"])
        assert result.risk_level == RiskLevel.READ
        assert not result.is_blocked
    
    def test_git_status_is_read(self, classifier):
        result = classifier.classify("git", ["status"])
        assert result.risk_level == RiskLevel.READ
        assert not result.is_blocked
    
    def test_git_log_is_read(self, classifier):
        result = classifier.classify("git", ["log", "-n", "10"])
        assert result.risk_level == RiskLevel.READ
        assert not result.is_blocked
    
    def test_grep_is_read(self, classifier):
        result = classifier.classify("grep", ["-r", "pattern", "."])
        assert result.risk_level == RiskLevel.READ
        assert not result.is_blocked
    
    # ========================================================================
    # WRITE Commands
    # ========================================================================
    
    def test_mkdir_is_write(self, classifier):
        result = classifier.classify("mkdir", ["-p", "new_dir"])
        assert result.risk_level == RiskLevel.WRITE
        assert not result.is_blocked
    
    def test_touch_is_write(self, classifier):
        result = classifier.classify("touch", ["newfile.txt"])
        assert result.risk_level == RiskLevel.WRITE
        assert not result.is_blocked
    
    def test_git_add_is_write(self, classifier):
        result = classifier.classify("git", ["add", "."])
        assert result.risk_level == RiskLevel.WRITE
        assert not result.is_blocked
    
    def test_git_commit_is_write(self, classifier):
        result = classifier.classify("git", ["commit", "-m", "test"])
        assert result.risk_level == RiskLevel.WRITE
        assert not result.is_blocked
    
    def test_npm_install_is_write(self, classifier):
        result = classifier.classify("npm", ["install"])
        assert result.risk_level == RiskLevel.WRITE
        assert not result.is_blocked
    
    # ========================================================================
    # HIGH_RISK Commands
    # ========================================================================
    
    def test_rm_is_high_risk(self, classifier):
        result = classifier.classify("rm", ["file.txt"])
        assert result.risk_level == RiskLevel.HIGH_RISK
        assert not result.is_blocked  # Not blocked, just HIGH_RISK
    
    def test_git_push_is_high_risk(self, classifier):
        result = classifier.classify("git", ["push", "origin", "main"])
        assert result.risk_level == RiskLevel.HIGH_RISK
        assert not result.is_blocked
    
    def test_curl_is_high_risk(self, classifier):
        result = classifier.classify("curl", ["https://example.com"])
        assert result.risk_level == RiskLevel.HIGH_RISK
        assert not result.is_blocked
    
    def test_sudo_is_high_risk(self, classifier):
        result = classifier.classify("sudo", ["ls"])
        assert result.risk_level == RiskLevel.HIGH_RISK
        assert not result.is_blocked
    
    def test_redirection_is_high_risk(self, classifier):
        result = classifier.classify("echo", ["test", ">", "file.txt"])
        assert result.risk_level == RiskLevel.HIGH_RISK
        assert not result.is_blocked
    
    # ========================================================================
    # Blocklist (Always Denied)
    # ========================================================================
    
    def test_rm_rf_root_is_blocked(self, classifier):
        result = classifier.classify("rm", ["-rf", "/"])
        assert result.is_blocked
        assert "blocklist" in result.block_reason.lower()
    
    def test_rm_rf_slash_is_blocked(self, classifier):
        result = classifier.classify("rm", ["-rf", "/var"])
        # This should match the pattern r"^rm\s+-rf\s+/"
        result = classifier.classify("rm", ["-rf /"])
        assert result.is_blocked
    
    def test_unknown_command_is_high_risk(self, classifier):
        result = classifier.classify("my_custom_binary", ["--dangerous"])
        assert result.risk_level == RiskLevel.HIGH_RISK
        assert not result.is_blocked
    
    # ========================================================================
    # Paranoid Mode
    # ========================================================================
    
    def test_paranoid_mode_makes_everything_high_risk(self):
        classifier = CommandClassifier(paranoid_mode=True)
        
        # Even safe commands become HIGH_RISK
        result = classifier.classify("ls", ["-la"])
        assert result.risk_level == RiskLevel.HIGH_RISK


class TestPolicyManifest:
    """Test policy manifest loading and classification."""
    
    def test_manifest_based_classification(self, tmp_path):
        """Test that manifest overrides default patterns."""
        import json
        
        manifest_data = {
            "version": "1.0",
            "safe_commands": ["custom_read_tool"],
            "write_commands": ["custom_write_tool"],
            "blocked_patterns": [],
            "signature": "valid"
        }
        
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))
        
        manifest = PolicyManifest.load(str(manifest_path))
        classifier = CommandClassifier(manifest=manifest)
        
        # Custom tool should be classified as READ
        result = classifier.classify("custom_read_tool", [])
        assert result.risk_level == RiskLevel.READ
        
        # Custom write tool should be WRITE
        result = classifier.classify("custom_write_tool", [])
        assert result.risk_level == RiskLevel.WRITE
