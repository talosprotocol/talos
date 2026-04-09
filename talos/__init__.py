"""
Talos Protocol SDK - Consolidated Namespace.

This package provides access to all Talos core, client, and network logic.
"""

__version__ = "0.1.0"

from .core.crypto import KeyPair, Wallet
from .core.session import Session, SessionManager, PrekeyBundle
from .core.blockchain import Blockchain
from .core.capability import Capability, CapabilityManager

from .client.client import Client, ClientConfig
from .network.p2p import P2PNode, P2PConfig

__all__ = [
    "KeyPair",
    "Wallet",
    "Session",
    "SessionManager",
    "PrekeyBundle",
    "Blockchain",
    "Capability",
    "CapabilityManager",
    "Client",
    "ClientConfig",
    "P2PNode",
    "P2PConfig",
]
