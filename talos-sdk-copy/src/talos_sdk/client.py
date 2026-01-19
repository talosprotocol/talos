"""Talos SDK Client.

High-level TalosClient facade as defined in SDK_CONTRACT.md.
"""

from typing import Any

from .errors import TalosTransportError
from .mcp import SignedFrame, sign_mcp_request
from .wallet import Wallet

# Protocol version supported by this SDK
PROTOCOL_VERSION = "1.0"
PROTOCOL_MIN = "1.0"
PROTOCOL_MAX = "1.0"


class TalosClient:
    """High-level Talos client facade.

    Composes Identity, MCP Security, and Transport modules into
    a simple interface for common operations.

    Example:
        >>> wallet = Wallet.generate("my-agent")
        >>> client = TalosClient("wss://gateway.example.com", wallet)
        >>> await client.connect()
        >>> response = await client.sign_and_send_mcp(
        ...     {"method": "read", "params": {"path": "/data"}},
        ...     "filesystem",
        ...     "read",
        ... )
        >>> await client.close()
    """

    def __init__(self, gateway_url: str, wallet: Wallet):
        """Initialize a TalosClient.

        Args:
            gateway_url: Gateway WebSocket URL
            wallet: Identity wallet for signing
        """
        self._gateway_url = gateway_url
        self._wallet = wallet
        self._connected = False
        self._session_id: str | None = None
        self._correlation_counter = 0

    @property
    def wallet(self) -> Wallet:
        """Get the client's wallet."""
        return self._wallet

    def protocol_version(self) -> str:
        """Get the negotiated protocol version.

        Returns:
            Protocol version string (e.g., "1.0")
        """
        return PROTOCOL_VERSION

    def supported_protocol_range(self) -> tuple[str, str]:
        """Get the SDK's supported protocol range.

        Returns:
            Tuple of (min_version, max_version)
        """
        return (PROTOCOL_MIN, PROTOCOL_MAX)

    async def connect(self) -> None:
        """Connect to the gateway.

        Raises:
            TalosTransportError: If connection fails
            TalosProtocolMismatchError: If protocol version incompatible
        """
        # TODO: Implement actual WebSocket connection
        # For now, mark as connected for facade completeness
        self._connected = True
        self._session_id = f"session-{id(self)}"

    async def close(self) -> None:
        """Gracefully close the connection."""
        self._connected = False
        self._session_id = None

    def _next_correlation_id(self) -> str:
        """Generate the next correlation ID."""
        self._correlation_counter += 1
        return f"corr-{self._correlation_counter}"

    def sign_mcp_request(
        self,
        request: dict[str, Any],
        tool: str,
        action: str,
    ) -> SignedFrame:
        """Sign an MCP request.

        Args:
            request: MCP request object
            tool: Tool name
            action: Action name

        Returns:
            SignedFrame ready to send

        Raises:
            TalosTransportError: If not connected
        """
        if not self._session_id:
            raise TalosTransportError("Not connected - call connect() first")

        correlation_id = self._next_correlation_id()
        return sign_mcp_request(
            self._wallet,
            request,
            self._session_id,
            correlation_id,
            tool,
            action,
        )


    async def sign_and_send_mcp(
        self,
        request: dict[str, Any],
        tool: str,
        action: str,
    ) -> dict[str, Any]:
        """Sign and send an MCP request, returning the response.

        Args:
            request: MCP request object
            tool: Tool name
            action: Action name

        Returns:
            Response from the gateway

        Raises:
            TalosTransportError: If not connected or send fails
        """
        if not self._connected:
            raise TalosTransportError("Not connected - call connect() first")

        frame = self.sign_mcp_request(request, tool, action)

        # TODO: Implement actual send/receive over WebSocket
        # For now, return a placeholder response
        return {
            "status": "ok",
            "correlation_id": frame.correlation_id,
        }

    def sign_http_request(
        self,
        method: str,
        path: str,
        query: str = "",
        body: dict[str, Any] | None = None,
        opcode: str = "http.request"
    ) -> dict[str, str]:
        """Sign an HTTP request for Phase 3 Attestation.

        Args:
            method: HTTP Method (e.g. POST)
            path: Raw path (e.g. /v1/chat)
            query: Raw query string (e.g. k=v&a=b)
            body: Request body dict (or None)
            opcode: Operation code (default: http.request)

        Returns:
            Dict of headers to add to the request:
            - X-Talos-Key-ID
            - X-Talos-Timestamp
            - X-Talos-Nonce
            - X-Talos-Signature
            - X-Talos-Sig-Alg
            - X-Talos-Sig-Version
        """
        import time
        import base64
        import json
        import os
        from .canonical import canonical_json_bytes
        
        # 1. Prepare inputs
        timestamp = int(time.time())
        nonce = base64.urlsafe_b64encode(os.urandom(12)).decode('ascii').rstrip('=')
        
        if body is None:
            body_bytes = b""
        else:
            body_bytes = canonical_json_bytes(body)
            
        method_ascii = method.upper().encode('ascii')
        
        # Path+Query: raw string exactly as sent
        # Expect caller to provide raw path and raw query string
        full_path = path + (f"?{query}" if query else "")
        path_query_ascii = full_path.encode('ascii')
        
        nonce_ascii = nonce.encode('ascii')
        ts_ascii = str(timestamp).encode('ascii')
        opcode_ascii = opcode.encode('ascii')
        
        # 2. Construct Signing Input (Strict Byte-Level)
        signing_input = (
            body_bytes + b"\n" +
            method_ascii + b"\n" +
            path_query_ascii + b"\n" +
            nonce_ascii + b"\n" +
            ts_ascii + b"\n" +
            opcode_ascii
        )
        
        # 3. Sign
        sig_bytes = self._wallet.sign(signing_input)
        sig_b64 = base64.urlsafe_b64encode(sig_bytes).decode('ascii').rstrip('=')
        
        return {
            "X-Talos-Key-ID": self._wallet.key_id,
            "X-Talos-Timestamp": str(timestamp),
            "X-Talos-Nonce": nonce,
            "X-Talos-Signature": sig_b64,
            "X-Talos-Sig-Alg": "ed25519",
            "X-Talos-Sig-Version": "v1"
        }
