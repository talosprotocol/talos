"""
Tests for the Talos SDK TalosClient.
"""

import pytest

from talos_sdk import TalosClient, TalosTransportError, Wallet


class TestTalosClient:
    """Tests for TalosClient facade."""

    def test_client_creation(self):
        """TalosClient should be creatable with wallet."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)
        assert client.wallet is wallet

    def test_protocol_version(self):
        """protocol_version should return version string."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)
        version = client.protocol_version()
        assert version == "1.0"

    def test_supported_protocol_range(self):
        """supported_protocol_range should return min/max tuple."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)
        min_v, max_v = client.supported_protocol_range()
        assert min_v == "1.0"
        assert max_v == "1.0"

    @pytest.mark.asyncio
    async def test_connect_and_close(self):
        """connect and close should work."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)

        await client.connect()
        await client.close()

    def test_sign_mcp_request_without_connect_fails(self):
        """sign_mcp_request should fail if not connected."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)

        with pytest.raises(TalosTransportError):
            client.sign_mcp_request({"method": "test"}, "tool", "action")

    @pytest.mark.asyncio
    async def test_sign_mcp_request_after_connect(self):
        """sign_mcp_request should work after connect."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)

        await client.connect()
        frame = client.sign_mcp_request({"method": "test"}, "tool", "action")

        assert frame.correlation_id.startswith("corr-")
        assert len(frame.signature) == 64

        await client.close()

    @pytest.mark.asyncio
    async def test_sign_and_send_mcp(self):
        """sign_and_send_mcp should return response."""
        wallet = Wallet.generate()
        client = TalosClient("wss://example.com", wallet)

        await client.connect()
        response = await client.sign_and_send_mcp({"method": "test"}, "tool", "action")

        assert response["status"] == "ok"
        assert "correlation_id" in response

        await client.close()

    def test_sign_http_request(self):
        """sign_http_request should produce strict output."""
        from unittest.mock import Mock, patch
        import base64
        import json
        
        # Mock wallet to capture signing input
        wallet = Mock()
        wallet.key_id = "key-test"
        wallet.sign.return_value = b"mock_signature_bytes"
        
        client = TalosClient("wss://example.com", wallet)
        
        # Fixed time and nonce
        with patch('time.time', return_value=1700000000), \
             patch('os.urandom', return_value=b'123456789012'):
            
            headers = client.sign_http_request(
                method="POST",
                path="/v1/chat",
                query="k=v",
                body={"foo": "bar"},
                opcode="test.op"
            )
            
            assert headers["X-Talos-Key-ID"] == "key-test"
            assert headers["X-Talos-Timestamp"] == "1700000000"
            assert headers["X-Talos-Sig-Alg"] == "ed25519"
            
            # Nonce check: base64url of b'123456789012'
            # MTIzNDU2Nzg5MDEy -> MTIzNDU2Nzg5MDEy (unpadded?)
            # b'123456789012' is 12 bytes.
            expected_nonce = base64.urlsafe_b64encode(b'123456789012').decode('ascii').rstrip('=')
            assert headers["X-Talos-Nonce"] == expected_nonce
            
            # Signature check: base64url of b"mock_signature_bytes"
            expected_sig = base64.urlsafe_b64encode(b"mock_signature_bytes").decode('ascii').rstrip('=')
            assert headers["X-Talos-Signature"] == expected_sig
            
            # Strict Signing Input Check
            wallet.sign.assert_called_once()
            args = wallet.sign.call_args[0]
            signed_bytes = args[0]
            
            # Expected items
            # body: canonical({"foo":"bar"}) -> b'{"foo":"bar"}'
            # method: POST
            # path_query: /v1/chat?k=v
            # nonce: ...
            # timestamp: 1700000000
            # opcode: test.op
            
            expected_input = (
                b'{"foo":"bar"}' + b"\n" +
                b"POST" + b"\n" +
                b"/v1/chat?k=v" + b"\n" +
                expected_nonce.encode('ascii') + b"\n" +
                b"1700000000" + b"\n" +
                b"test.op"
            )
            
            assert signed_bytes == expected_input

    def test_sign_http_request_empty_body(self):
        """sign_http_request should handle empty body correctly."""
        from unittest.mock import Mock, patch
        wallet = Mock()
        wallet.key_id = "key-test"
        wallet.sign.return_value = b"sig"
        client = TalosClient("wss://example.com", wallet)
        
        with patch('time.time', return_value=1), patch('os.urandom', return_value=b'x'*12):
             client.sign_http_request("GET", "/test", body=None)
             
             signed_bytes = wallet.sign.call_args[0][0]
             assert signed_bytes.startswith(b"\n") # Empty body -> b""
