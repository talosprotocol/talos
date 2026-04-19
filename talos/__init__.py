"""
Talos Protocol SDK - Consolidated Namespace.

This package provides access to all Talos core, client, and network logic.
"""

__version__ = "0.1.0"

# Core protocol primitives
from .core.crypto import KeyPair, Wallet
from .core.session import Session, SessionManager, PrekeyBundle
from .core.blockchain import Blockchain
from .core.capability import Capability, CapabilityManager

# Network components
from .network.p2p import P2PNode, P2PConfig

# SDK abstractions (Legacy and current)
from .config import TalosConfig
from .identity import Identity
from .channel import SecureChannel, ChannelPool
from .legacy_client import TalosClient

# New consolidated client
from .client.client import Client, ClientConfig

__all__ = [
    "KeyPair",
    "Wallet",
    "Session",
    "SessionManager",
    "PrekeyBundle",
    "Blockchain",
    "Capability",
    "CapabilityManager",
    "TalosConfig",
    "Identity",
    "SecureChannel",
    "ChannelPool",
    "TalosClient",
    "Client",
    "ClientConfig",
    "P2PNode",
    "P2PConfig",
]
