"""
Talos SDK - Python SDK for Secure AI Agent Communication.

This SDK provides a clean, developer-friendly interface to the Talos Protocol
for building secure, decentralized AI agent communication systems.

Quick Start:
    from talos import TalosClient, SecureChannel
    
    # Create client
    client = TalosClient.create("my-agent")
    
    # Connect to peer
    async with SecureChannel(client, peer_id) as channel:
        await channel.send(b"Hello, World!")
        response = await channel.receive()

Features:
    - End-to-end encryption with forward secrecy
    - Blockchain-backed message integrity
    - Peer-to-peer networking
    - MCP tunneling for AI tool access
    - Fine-grained access control
"""

from .client import TalosClient
from .channel import SecureChannel
from .identity import Identity
from .config import TalosConfig
from .exceptions import (
    TalosError,
    ConnectionError,
    EncryptionError,
    AuthenticationError,
    RateLimitError,
)

__version__ = "2.0.0"

__all__ = [
    # Core
    "TalosClient",
    "SecureChannel",
    "Identity",
    "TalosConfig",
    # Exceptions
    "TalosError",
    "ConnectionError",
    "EncryptionError",
    "AuthenticationError",
    "RateLimitError",
    # Version
    "__version__",
]
