"""Talos SDK - Secure Multi-Language SDK for AI Agents.

This package provides the Python implementation of the Talos Protocol v1,
enabling secure identity, capability authorization, and MCP request signing.

Example:
    >>> from talos_sdk import Wallet, TalosClient
    >>> wallet = Wallet.generate("my-agent")
    >>> client = TalosClient("wss://gateway.example.com", wallet)
    >>> await client.connect()
    >>> response = await client.sign_and_send_mcp(
    ...     {"method": "read", "params": {"path": "/data"}},
    ...     "filesystem",
    ...     "read",
    ... )
"""

from .canonical import canonical_json, canonical_json_bytes
from .client import PROTOCOL_VERSION, TalosClient
from .errors import (
    TalosCryptoError,
    TalosDeniedError,
    TalosError,
    TalosFrameInvalidError,
    TalosInvalidCapabilityError,
    TalosInvalidInputError,
    TalosProtocolMismatchError,
    TalosTransportError,
    TalosTransportTimeoutError,
)
from .mcp import SignedFrame, sign_mcp_request, verify_mcp_response
from .mcp_client import McpClient
from .wallet import Wallet

__version__ = "1.0.0"

# SDK Version Exports (required by VERSIONING.md)
SDK_VERSION = __version__
SUPPORTED_PROTOCOL_RANGE = ("1.0", "1.x")
CONTRACT_MANIFEST_HASH = "sha256:pending"  # Updated at build time

__all__ = [
    # Core classes
    "Wallet",
    "TalosClient",
    "McpClient",
    "SignedFrame",
    # Functions
    "sign_mcp_request",
    "verify_mcp_response",
    "canonical_json",
    "canonical_json_bytes",
    # Constants
    "PROTOCOL_VERSION",
    # Errors
    "TalosError",
    "TalosDeniedError",
    "TalosInvalidCapabilityError",
    "TalosProtocolMismatchError",
    "TalosFrameInvalidError",
    "TalosCryptoError",
    "TalosInvalidInputError",
    "TalosTransportTimeoutError",
    "TalosTransportError",
]
