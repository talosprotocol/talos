"""
Double Ratchet Protocol for Perfect Forward Secrecy.

This module implements the Signal Double Ratchet algorithm for secure
messaging with forward secrecy and break-in recovery:

- **Forward Secrecy**: Compromised keys don't expose past messages
- **Break-in Recovery**: Sessions heal after key compromise
- **Per-Message Keys**: Each message uses a unique encryption key

Based on the Signal Protocol specification:
https://signal.org/docs/specifications/doubleratchet/

Components:
- X3DH: Extended Triple Diffie-Hellman handshake for session init
- KDF Chain: Key derivation chain for symmetric ratcheting
- DH Ratchet: Asymmetric ratcheting with ephemeral keys

Usage:
    from src.core.session import SessionManager, Session
    
    # Initialize session with peer's prekey bundle
    session = await manager.create_session(peer_id, prekey_bundle)
    
    # Encrypt a message (ratchets forward)
    encrypted = session.encrypt(b"Hello, World!")
    
    # Decrypt (ratchets as needed)
    plaintext = session.decrypt(encrypted)
"""

import base64
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .crypto import (
    KeyPair,
    generate_encryption_keypair,
    generate_signing_keypair,
    sign_message,
    verify_signature,
)

logger = logging.getLogger(__name__)

# Protocol constants
MAX_SKIP = 1000  # Max messages to skip in a chain
INFO_ROOT = b"talos-double-ratchet-root"
INFO_CHAIN = b"talos-double-ratchet-chain"
INFO_MESSAGE = b"talos-double-ratchet-message"


class RatchetError(Exception):
    """Error during ratchet operation."""
    pass


@dataclass
class PrekeyBundle:
    """
    Prekey bundle for X3DH key exchange.
    
    Published by users to allow others to establish sessions.
    """
    identity_key: bytes      # Long-term Ed25519 public key
    signed_prekey: bytes     # X25519 public key, signed by identity key
    prekey_signature: bytes  # Signature over signed_prekey
    one_time_prekey: Optional[bytes] = None  # Optional ephemeral X25519 key
    
    def verify(self) -> bool:
        """Verify the prekey signature."""
        return verify_signature(self.signed_prekey, self.prekey_signature, self.identity_key)
    
    def to_dict(self) -> dict[str, str]:
        result = {
            "identity_key": base64.b64encode(self.identity_key).decode(),
            "signed_prekey": base64.b64encode(self.signed_prekey).decode(),
            "prekey_signature": base64.b64encode(self.prekey_signature).decode(),
        }
        if self.one_time_prekey:
            result["one_time_prekey"] = base64.b64encode(self.one_time_prekey).decode()
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "PrekeyBundle":
        return cls(
            identity_key=base64.b64decode(data["identity_key"]),
            signed_prekey=base64.b64decode(data["signed_prekey"]),
            prekey_signature=base64.b64decode(data["prekey_signature"]),
            one_time_prekey=base64.b64decode(data["one_time_prekey"]) if "one_time_prekey" in data else None,
        )


@dataclass
class MessageHeader:
    """
    Header for ratcheted messages.
    
    Contains the sender's current DH public key and chain position.
    """
    dh_public: bytes      # Sender's current DH ratchet public key
    previous_chain_length: int  # Messages in previous sending chain
    message_number: int   # Index in current sending chain
    
    def to_bytes(self) -> bytes:
        return json.dumps({
            "dh": base64.b64encode(self.dh_public).decode(),
            "pn": self.previous_chain_length,
            "n": self.message_number,
        }).encode()
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "MessageHeader":
        d = json.loads(data)
        return cls(
            dh_public=base64.b64decode(d["dh"]),
            previous_chain_length=d["pn"],
            message_number=d["n"],
        )


@dataclass 
class RatchetState:
    """
    State of a Double Ratchet session.
    
    This contains all the keys and counters needed to encrypt
    and decrypt messages with forward secrecy.
    """
    # DH ratchet keys
    dh_keypair: KeyPair             # Our current DH key pair
    dh_remote: Optional[bytes]      # Remote's current DH public key
    
    # Root key (updated on DH ratchet)
    root_key: bytes
    
    # Sending and receiving chain keys
    chain_key_send: Optional[bytes] = None
    chain_key_recv: Optional[bytes] = None
    
    # Message counters
    send_count: int = 0      # Messages sent in current sending chain
    recv_count: int = 0      # Messages received in current receiving chain
    prev_send_count: int = 0 # Messages in previous sending chain
    
    # Skipped message keys (for out-of-order delivery)
    skipped_keys: dict[tuple[bytes, int], bytes] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "dh_keypair": self.dh_keypair.to_dict(),
            "dh_remote": base64.b64encode(self.dh_remote).decode() if self.dh_remote else None,
            "root_key": base64.b64encode(self.root_key).decode(),
            "chain_key_send": base64.b64encode(self.chain_key_send).decode() if self.chain_key_send else None,
            "chain_key_recv": base64.b64encode(self.chain_key_recv).decode() if self.chain_key_recv else None,
            "send_count": self.send_count,
            "recv_count": self.recv_count,
            "prev_send_count": self.prev_send_count,
            # Skipped keys serialized as list
            "skipped": [
                {
                    "dh": base64.b64encode(k[0]).decode(),
                    "n": k[1],
                    "key": base64.b64encode(v).decode(),
                }
                for k, v in self.skipped_keys.items()
            ],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RatchetState":
        skipped = {}
        for item in data.get("skipped", []):
            key = (base64.b64decode(item["dh"]), item["n"])
            skipped[key] = base64.b64decode(item["key"])
        
        return cls(
            dh_keypair=KeyPair.from_dict(data["dh_keypair"]),
            dh_remote=base64.b64decode(data["dh_remote"]) if data.get("dh_remote") else None,
            root_key=base64.b64decode(data["root_key"]),
            chain_key_send=base64.b64decode(data["chain_key_send"]) if data.get("chain_key_send") else None,
            chain_key_recv=base64.b64decode(data["chain_key_recv"]) if data.get("chain_key_recv") else None,
            send_count=data.get("send_count", 0),
            recv_count=data.get("recv_count", 0),
            prev_send_count=data.get("prev_send_count", 0),
            skipped_keys=skipped,
        )


def _hkdf_derive(input_key: bytes, info: bytes, length: int = 32) -> bytes:
    """Derive key using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    )
    return hkdf.derive(input_key)


def _kdf_rk(rk: bytes, dh_out: bytes) -> tuple[bytes, bytes]:
    """
    Root key KDF: derive new root key and chain key.
    
    Returns (new_root_key, new_chain_key)
    """
    # Derive 64 bytes from root key + DH output
    combined = _hkdf_derive(rk + dh_out, INFO_ROOT, length=64)
    return combined[:32], combined[32:]


def _kdf_ck(ck: bytes) -> tuple[bytes, bytes]:
    """
    Chain key KDF: derive message key and next chain key.
    
    Returns (message_key, next_chain_key)
    """
    # Use HMAC-based approach (simplified HKDF)
    message_key = _hkdf_derive(ck, INFO_MESSAGE)
    next_chain_key = _hkdf_derive(ck, INFO_CHAIN)
    return message_key, next_chain_key


def _dh(private: bytes, public: bytes) -> bytes:
    """Perform X25519 Diffie-Hellman exchange."""
    priv = X25519PrivateKey.from_private_bytes(private)
    pub = X25519PublicKey.from_public_bytes(public)
    return priv.exchange(pub)


def _encrypt_aead(key: bytes, plaintext: bytes, ad: bytes) -> bytes:
    """Encrypt with ChaCha20-Poly1305 AEAD."""
    nonce = os.urandom(12)
    cipher = ChaCha20Poly1305(key)
    ciphertext = cipher.encrypt(nonce, plaintext, ad)
    return nonce + ciphertext


def _decrypt_aead(key: bytes, data: bytes, ad: bytes) -> bytes:
    """Decrypt with ChaCha20-Poly1305 AEAD."""
    nonce = data[:12]
    ciphertext = data[12:]
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, ad)


class Session:
    """
    A Double Ratchet session with a single peer.
    
    Provides forward-secure encryption with per-message keys.
    """
    
    def __init__(self, peer_id: str, state: RatchetState):
        self.peer_id = peer_id
        self.state = state
        self.created_at = time.time()
        self.last_activity = time.time()
        self.messages_sent = 0
        self.messages_received = 0
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt a message with the current sending key.
        
        Returns header + ciphertext as bytes.
        """
        # Get message key and advance chain
        if self.state.chain_key_send is None:
            raise RatchetError("No sending chain key - session not fully initialized")
        
        mk, self.state.chain_key_send = _kdf_ck(self.state.chain_key_send)
        
        # Create header
        header = MessageHeader(
            dh_public=self.state.dh_keypair.public_key,
            previous_chain_length=self.state.prev_send_count,
            message_number=self.state.send_count,
        )
        
        # Encrypt with header as associated data
        header_bytes = header.to_bytes()
        ciphertext = _encrypt_aead(mk, plaintext, header_bytes)
        
        # Update counters
        self.state.send_count += 1
        self.messages_sent += 1
        self.last_activity = time.time()
        
        # Return header length + header + ciphertext
        header_len = len(header_bytes).to_bytes(2, "big")
        return header_len + header_bytes + ciphertext
    
    def decrypt(self, message: bytes) -> bytes:
        """
        Decrypt a message, performing DH ratchet if needed.
        """
        # Parse header
        header_len = int.from_bytes(message[:2], "big")
        header_bytes = message[2:2 + header_len]
        ciphertext = message[2 + header_len:]
        header = MessageHeader.from_bytes(header_bytes)
        
        # Try skipped keys first
        plaintext = self._try_skipped_keys(header, ciphertext, header_bytes)
        if plaintext is not None:
            return plaintext
        
        # Check if we need a DH ratchet
        if header.dh_public != self.state.dh_remote:
            # Skip messages in the old receiving chain
            self._skip_message_keys(header.previous_chain_length)
            # Perform DH ratchet
            self._dh_ratchet(header)
        
        # Skip any messages in current receiving chain
        self._skip_message_keys(header.message_number)
        
        # Decrypt with current key
        if self.state.chain_key_recv is None:
            raise RatchetError("No receiving chain key")
        
        mk, self.state.chain_key_recv = _kdf_ck(self.state.chain_key_recv)
        self.state.recv_count += 1
        
        try:
            plaintext = _decrypt_aead(mk, ciphertext, header_bytes)
        except Exception as e:
            raise RatchetError(f"Decryption failed: {e}")
        
        self.messages_received += 1
        self.last_activity = time.time()
        
        return plaintext
    
    def _try_skipped_keys(
        self,
        header: MessageHeader,
        ciphertext: bytes,
        ad: bytes,
    ) -> Optional[bytes]:
        """Try to decrypt with a skipped message key."""
        key_id = (header.dh_public, header.message_number)
        if key_id in self.state.skipped_keys:
            mk = self.state.skipped_keys.pop(key_id)
            return _decrypt_aead(mk, ciphertext, ad)
        return None
    
    def _skip_message_keys(self, until: int) -> None:
        """Store skipped message keys for out-of-order messages."""
        if self.state.chain_key_recv is None:
            return
        
        if self.state.recv_count + MAX_SKIP < until:
            raise RatchetError("Too many skipped messages")
        
        while self.state.recv_count < until:
            mk, self.state.chain_key_recv = _kdf_ck(self.state.chain_key_recv)
            key_id = (self.state.dh_remote, self.state.recv_count)
            self.state.skipped_keys[key_id] = mk
            self.state.recv_count += 1
    
    def _dh_ratchet(self, header: MessageHeader) -> None:
        """Perform a DH ratchet step."""
        self.state.prev_send_count = self.state.send_count
        self.state.send_count = 0
        self.state.recv_count = 0
        self.state.dh_remote = header.dh_public
        
        # Derive new receiving chain
        dh_recv = _dh(self.state.dh_keypair.private_key, self.state.dh_remote)
        self.state.root_key, self.state.chain_key_recv = _kdf_rk(
            self.state.root_key, dh_recv
        )
        
        # Generate new DH key pair
        self.state.dh_keypair = generate_encryption_keypair()
        
        # Derive new sending chain
        dh_send = _dh(self.state.dh_keypair.private_key, self.state.dh_remote)
        self.state.root_key, self.state.chain_key_send = _kdf_rk(
            self.state.root_key, dh_send
        )
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "state": self.state.to_dict(),
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        session = cls(
            peer_id=data["peer_id"],
            state=RatchetState.from_dict(data["state"]),
        )
        session.created_at = data.get("created_at", time.time())
        session.last_activity = data.get("last_activity", time.time())
        session.messages_sent = data.get("messages_sent", 0)
        session.messages_received = data.get("messages_received", 0)
        return session


class SessionManager:
    """
    Manages Double Ratchet sessions with multiple peers.
    
    Handles session creation, storage, and retrieval.
    """
    
    def __init__(self, identity_keypair: KeyPair, storage_path: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            identity_keypair: Our long-term identity key pair
            storage_path: Optional path for session persistence
        """
        self.identity_keypair = identity_keypair
        self.storage_path = storage_path
        self.sessions: dict[str, Session] = {}
        
        # Our prekey for others to contact us
        self._signed_prekey = generate_encryption_keypair()
        self._prekey_signature = sign_message(
            self._signed_prekey.public_key,
            identity_keypair.private_key
        )
    
    def get_prekey_bundle(self) -> PrekeyBundle:
        """Get our prekey bundle for publishing."""
        return PrekeyBundle(
            identity_key=self.identity_keypair.public_key,
            signed_prekey=self._signed_prekey.public_key,
            prekey_signature=self._prekey_signature,
        )
    
    def create_session_as_initiator(
        self,
        peer_id: str,
        peer_bundle: PrekeyBundle,
    ) -> Session:
        """
        Create a new session as the initiator (Alice).
        
        This performs X3DH key agreement and initializes the ratchet.
        The ephemeral key is reused as the first DH ratchet key.
        """
        # Verify peer's prekey signature
        if not peer_bundle.verify():
            raise RatchetError("Invalid prekey signature")
        
        # Generate ephemeral key (will be reused as first ratchet key)
        dh_keypair = generate_encryption_keypair()
        
        # X3DH: Compute shared secret
        # DH(our_ephemeral, their_signed_prekey)
        dh_x3dh = _dh(dh_keypair.private_key, peer_bundle.signed_prekey)
        
        # Derive initial root key
        root_key = _hkdf_derive(dh_x3dh, b"x3dh-init")
        
        # Initialize first sending chain
        # Same DH output since we're reusing ephemeral as ratchet key
        dh_out = _dh(dh_keypair.private_key, peer_bundle.signed_prekey)
        root_key, chain_key_send = _kdf_rk(root_key, dh_out)
        
        state = RatchetState(
            dh_keypair=dh_keypair,
            dh_remote=peer_bundle.signed_prekey,
            root_key=root_key,
            chain_key_send=chain_key_send,
        )
        
        session = Session(peer_id, state)
        self.sessions[peer_id] = session
        
        logger.info(f"Created session as initiator with {peer_id[:16]}...")
        return session
    
    def create_session_as_responder(
        self,
        peer_id: str,
        peer_dh_public: bytes,
        peer_identity: bytes,
    ) -> Session:
        """
        Create a new session as the responder (Bob).
        
        Called when receiving the first message from a peer.
        The peer_dh_public is the sender's DH ratchet public key from
        the message header.
        
        The key derivation must match what the initiator did:
        - Initiator derives: root_key, chain_key_send = KDF(root_key, DH(their_dh, our_spk))
        - Responder derives: root_key, chain_key_recv = KDF(root_key, DH(our_spk, their_dh))
        
        Since DH is symmetric, both get the same chain key.
        """
        # Match what initiator did:
        # 1. Initiator's X3DH: DH(ephemeral, our_signed_prekey)
        # 2. Initiator's root_key from HKDF
        # 3. Initiator's chain_key_send from KDF_RK(root_key, DH(their_dh_keypair, our_signed_prekey))
        
        # We must replicate step 3 for our receiving chain
        # DH(our_signed_prekey, their_dh_public) = DH(their_dh_keypair, our_signed_prekey)
        
        # First, derive same initial root key as initiator
        dh_x3dh = _dh(self._signed_prekey.private_key, peer_dh_public)
        root_key = _hkdf_derive(dh_x3dh, b"x3dh-init")
        
        # Now derive receiving chain matching initiator's sending chain
        dh_recv = _dh(self._signed_prekey.private_key, peer_dh_public)
        root_key, chain_key_recv = _kdf_rk(root_key, dh_recv)
        
        state = RatchetState(
            dh_keypair=self._signed_prekey,
            dh_remote=peer_dh_public,
            root_key=root_key,
            chain_key_recv=chain_key_recv,
        )
        
        session = Session(peer_id, state)
        self.sessions[peer_id] = session
        
        logger.info(f"Created session as responder with {peer_id[:16]}...")
        return session
    
    def get_session(self, peer_id: str) -> Optional[Session]:
        """Get existing session with a peer."""
        return self.sessions.get(peer_id)
    
    def has_session(self, peer_id: str) -> bool:
        """Check if we have a session with a peer."""
        return peer_id in self.sessions
    
    def remove_session(self, peer_id: str) -> bool:
        """Remove session with a peer."""
        if peer_id in self.sessions:
            del self.sessions[peer_id]
            return True
        return False
    
    def save(self) -> None:
        """Save all sessions to storage."""
        if not self.storage_path:
            return
        
        data = {
            "sessions": {
                peer_id: session.to_dict()
                for peer_id, session in self.sessions.items()
            },
            "signed_prekey": self._signed_prekey.to_dict(),
            "prekey_signature": base64.b64encode(self._prekey_signature).decode(),
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.sessions)} sessions")
    
    def load(self) -> None:
        """Load sessions from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        with open(self.storage_path, "r") as f:
            data = json.load(f)
        
        self._signed_prekey = KeyPair.from_dict(data["signed_prekey"])
        self._prekey_signature = base64.b64decode(data["prekey_signature"])
        
        for peer_id, session_data in data.get("sessions", {}).items():
            self.sessions[peer_id] = Session.from_dict(session_data)
        
        logger.info(f"Loaded {len(self.sessions)} sessions")
    
    def get_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        total_sent = sum(s.messages_sent for s in self.sessions.values())
        total_recv = sum(s.messages_received for s in self.sessions.values())
        
        return {
            "active_sessions": len(self.sessions),
            "total_messages_sent": total_sent,
            "total_messages_received": total_recv,
        }
