"""
Tests for the Talos SDK MCP module.
"""

from talos_sdk import Wallet, sign_mcp_request, verify_mcp_response


class TestMCPSigning:
    """Tests for MCP signing functions."""

    def test_sign_mcp_request_creates_frame(self):
        """sign_mcp_request should create a valid SignedFrame."""
        wallet = Wallet.generate()
        request = {"method": "read", "params": {"path": "/data"}}

        frame = sign_mcp_request(
            wallet=wallet,
            request=request,
            session_id="session-123",
            correlation_id="corr-456",
            tool="filesystem",
            action="read",
            timestamp=1767500000,
        )

        assert frame.correlation_id == "corr-456"
        assert frame.signer_did == wallet.to_did()
        assert len(frame.signature) == 64
        assert len(frame.payload) > 0

    def test_sign_mcp_is_deterministic(self):
        """Same inputs should produce same signature."""
        seed = bytes(32)
        wallet = Wallet.from_seed(seed)
        request = {"method": "test"}

        frame1 = sign_mcp_request(
            wallet, request, "s1", "c1", "tool", "action", timestamp=1000
        )
        frame2 = sign_mcp_request(
            wallet, request, "s1", "c1", "tool", "action", timestamp=1000
        )

        assert frame1.signature == frame2.signature
        assert frame1.payload == frame2.payload

    def test_verify_mcp_response_valid(self):
        """verify_mcp_response should pass for valid frame."""
        wallet = Wallet.generate()
        frame = sign_mcp_request(wallet, {"method": "test"}, "s", "c", "t", "a")

        is_valid = verify_mcp_response(frame, "c", wallet.public_key)
        assert is_valid is True

    def test_verify_mcp_response_wrong_correlation(self):
        """Wrong correlation ID should fail verification."""
        wallet = Wallet.generate()
        frame = sign_mcp_request(wallet, {"method": "test"}, "s", "correct", "t", "a")

        is_valid = verify_mcp_response(frame, "wrong", wallet.public_key)
        assert is_valid is False

    def test_verify_mcp_response_wrong_key(self):
        """Wrong public key should fail verification."""
        wallet1 = Wallet.generate()
        wallet2 = Wallet.generate()
        frame = sign_mcp_request(wallet1, {"method": "test"}, "s", "c", "t", "a")

        is_valid = verify_mcp_response(frame, "c", wallet2.public_key)
        assert is_valid is False
