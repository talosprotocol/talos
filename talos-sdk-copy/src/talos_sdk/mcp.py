"""Talos SDK MCP Security.

Implements MCP request signing as defined in SDK_CONTRACT.md.
"""

import time
from dataclasses import dataclass
from typing import Any

from .canonical import canonical_json_bytes
from .wallet import Wallet


@dataclass
class SignedFrame:
    """A signed MCP frame."""

    payload: bytes
    signature: bytes
    signer_did: str
    correlation_id: str


def sign_mcp_request(
    wallet: Wallet,
    request: dict[str, Any],
    session_id: str,
    correlation_id: str,
    tool: str,
    action: str,
    timestamp: int | None = None,
) -> SignedFrame:
    """Sign an MCP request with audit bindings.

    Args:
        wallet: Signing identity wallet
        request: MCP request object (will be canonicalized)
        session_id: Session identifier
        correlation_id: Request correlation ID
        tool: Tool name being invoked
        action: Action being performed
        timestamp: Unix epoch timestamp (defaults to current time)

    Returns:
        SignedFrame containing the payload, signature, and metadata

    Note:
        Deterministic - same inputs produce identical signature.
    """
    if timestamp is None:
        timestamp = int(time.time())

    payload = {
        "request": request,
        "session_id": session_id,
        "correlation_id": correlation_id,
        "tool": tool,
        "action": action,
        "timestamp": timestamp,
    }

    payload_bytes = canonical_json_bytes(payload)
    signature = wallet.sign(payload_bytes)

    return SignedFrame(
        payload=payload_bytes,
        signature=signature,
        signer_did=wallet.to_did(),
        correlation_id=correlation_id,
    )


def verify_mcp_response(
    frame: SignedFrame,
    expected_correlation_id: str,
    signer_public_key: bytes,
) -> bool:
    """Verify a signed MCP response.

    Args:
        frame: The signed frame to verify
        expected_correlation_id: Expected correlation ID
        signer_public_key: 32-byte public key of the expected signer

    Returns:
        True if valid, False otherwise
    """
    if frame.correlation_id != expected_correlation_id:
        return False

    return Wallet.verify(frame.payload, frame.signature, signer_public_key)
