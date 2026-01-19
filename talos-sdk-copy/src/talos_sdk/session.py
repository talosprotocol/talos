"""Double Ratchet Protocol for Perfect Forward Secrecy.

This module implements the Signal Double Ratchet algorithm for secure
messaging with forward secrecy and break-in recovery.
"""

import base64
import json
import logging
import os
import time
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .canonical import canonical_json_bytes
from .crypto import (
    KeyPair,
    b64u_decode,
    b64u_encode,
    generate_encryption_keypair,
    sign_message,
    verify_signature,
)
from .errors import TalosError

logger = logging.getLogger(__name__)

# Protocol constants
MAX_SKIP = 1000  # Max messages to skip in a chain
INFO_ROOT = b"talos-double-ratchet-root"
INFO_CHAIN = b"talos-double-ratchet-chain"
INFO_MESSAGE = b"talos-double-ratchet-message"


class RatchetError(TalosError):
    """Error during ratchet operation."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__("TALOS_RATCHET_ERROR", message, **kwargs)


class PrekeyBundle(BaseModel):
    """Prekey bundle for X3DH key exchange.

    Published by users to allow others to establish sessions.
    """

    identity_key: bytes  # Long-term Ed25519 public key
    signed_prekey: bytes  # X25519 public key, signed by identity key
    prekey_signature: bytes  # Signature over signed_prekey
    one_time_prekey: bytes | None = None  # Optional ephemeral X25519 key

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("identity_key", "signed_prekey", "prekey_signature")
    def serialize_bytes(self, v: bytes, _info: Any) -> str:
        return base64.b64encode(v).decode()

    @field_serializer("one_time_prekey")
    def serialize_opt_bytes(self, v: bytes | None, _info: Any) -> str | None:
        if v is None:
            return None
        return base64.b64encode(v).decode()

    def verify(self) -> bool:
        """Verify the prekey signature."""
        return verify_signature(
            self.signed_prekey, self.prekey_signature, self.identity_key
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with base64-encoded keys (compat alias)."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PrekeyBundle":
        return cls(
            identity_key=base64.b64decode(data["identity_key"]),
            signed_prekey=base64.b64decode(data["signed_prekey"]),
            prekey_signature=base64.b64decode(data["prekey_signature"]),
            one_time_prekey=base64.b64decode(data["one_time_prekey"])
            if data.get("one_time_prekey")
            else None,
        )


class MessageHeader(BaseModel):
    """Header for ratcheted messages.

    Contains the sender's current DH public key and chain position.
    """

    dh_public: bytes  # Sender's current DH ratchet public key
    previous_chain_length: int  # Messages in previous sending chain
    message_number: int  # Index in current sending chain

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("dh_public")
    def serialize_bytes(self, v: bytes, _info: Any) -> str:
        return base64.b64encode(v).decode()

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(
            {
                "dh": b64u_encode(self.dh_public),
                "pn": self.previous_chain_length,
                "n": self.message_number,
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "MessageHeader":
        d = json.loads(data)
        return cls(
            dh_public=b64u_decode(d["dh"]),
            previous_chain_length=d["pn"],
            message_number=d["n"],
        )


class RatchetState(BaseModel):
    """State of a Double Ratchet session.

    This contains all the keys and counters needed to encrypt
    and decrypt messages with forward secrecy.
    """

    # DH ratchet keys
    dh_keypair: KeyPair  # Our current DH key pair
    dh_remote: bytes | None  # Remote's current DH public key

    # Root key (updated on DH ratchet)
    root_key: bytes

    # Sending and receiving chain keys
    chain_key_send: bytes | None = None
    chain_key_recv: bytes | None = None

    # Message counters
    send_count: int = 0  # Messages sent in current sending chain
    recv_count: int = 0  # Messages received in current receiving chain
    prev_send_count: int = 0  # Messages in previous sending chain

    # Skipped message keys (for out-of-order delivery)
    skipped_keys: dict[tuple[bytes, int], bytes] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer("dh_remote", "root_key", "chain_key_send", "chain_key_recv")
    def serialize_opt_bytes(self, v: bytes | None, _info: Any) -> str | None:
        if v is None:
            return None
        return base64.b64encode(v).decode()

    @field_serializer("dh_keypair")
    def serialize_keypair(self, v: KeyPair, _info: Any) -> dict[str, Any]:
        return v.to_dict()

    @field_serializer("skipped_keys")
    def serialize_skipped(
        self, v: dict[tuple[bytes, int], bytes], _info: Any
    ) -> list[dict[str, Any]]:
        return [
            {
                "dh": base64.b64encode(k[0]).decode(),
                "n": k[1],
                "key": base64.b64encode(val).decode(),
            }
            for k, val in v.items()
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (compat alias)."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RatchetState":
        skipped = {}
        for item in data.get(
            "skipped_keys", data.get("skipped", [])
        ):  # Handle both key names for compat
            key = (base64.b64decode(item["dh"]), item["n"])
            skipped[key] = base64.b64decode(item["key"])

        return cls(
            dh_keypair=KeyPair.from_dict(data["dh_keypair"]),
            dh_remote=base64.b64decode(data["dh_remote"])
            if data.get("dh_remote")
            else None,
            root_key=base64.b64decode(data["root_key"]),
            chain_key_send=base64.b64decode(data["chain_key_send"])
            if data.get("chain_key_send")
            else None,
            chain_key_recv=base64.b64decode(data["chain_key_recv"])
            if data.get("chain_key_recv")
            else None,
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
    """Root key KDF: derive new root key and chain key.

    Returns (new_root_key, new_chain_key)
    """
    # Derive 64 bytes from root key + DH output
    combined = _hkdf_derive(rk + dh_out, INFO_ROOT, length=64)
    return combined[:32], combined[32:]


def _kdf_ck(ck: bytes) -> tuple[bytes, bytes]:
    """Chain key KDF: derive message key and next chain key.

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


def _encrypt_aead(key: bytes, plaintext: bytes, ad: bytes) -> tuple[bytes, bytes]:
    """Encrypt with ChaCha20-Poly1305 AEAD. Returns (nonce, ciphertext)."""
    nonce = os.urandom(12)
    cipher = ChaCha20Poly1305(key)
    ciphertext = cipher.encrypt(nonce, plaintext, ad)
    return nonce, ciphertext


def _decrypt_aead(key: bytes, nonce: bytes, ciphertext: bytes, ad: bytes) -> bytes:
    """Decrypt with ChaCha20-Poly1305 AEAD."""
    cipher = ChaCha20Poly1305(key)
    return cipher.decrypt(nonce, ciphertext, ad)


class Session:
    """A Double Ratchet session with a single peer.

    Provides forward-secure encryption with per-message keys.
    """

    def __init__(self, peer_id: str, state: RatchetState) -> None:
        self.peer_id = peer_id
        self.state = state
        self.created_at = time.time()
        self.last_activity = time.time()
        self.messages_sent = 0
        self.messages_received = 0

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt a message with the current sending key.

        Returns JSON-enveloped message as canonical bytes.
        """
        if self.state.chain_key_send is None:
            self._initialize_sending_chain()

        assert self.state.chain_key_send is not None
        mk, self.state.chain_key_send = _kdf_ck(self.state.chain_key_send)

        header = MessageHeader(
            dh_public=self.state.dh_keypair.public_key,
            previous_chain_length=self.state.prev_send_count,
            message_number=self.state.send_count,
        )

        # Encrypt with raw header bytes as associated data
        header_bytes = header.to_bytes()
        nonce, ciphertext = _encrypt_aead(mk, plaintext, header_bytes)

        # Update counters
        self.state.send_count += 1
        self.messages_sent += 1
        self.last_activity = time.time()

        # Wrap in JSON envelope (v1.1.0 Option A)
        envelope = {
            "header": {
                "dh": b64u_encode(header.dh_public),
                "pn": header.previous_chain_length,
                "n": header.message_number,
            },
            "nonce": b64u_encode(nonce),
            "ciphertext": b64u_encode(ciphertext),
        }
        return canonical_json_bytes(envelope)

    def decrypt(self, message: bytes) -> bytes:
        """Decrypt a message, performing DH ratchet if needed."""
        # Parse envelope
        try:
            envelope = json.loads(message)
            header_dict = envelope["header"]
            # Re-canonicalize header for AAD and parsing
            header_bytes = canonical_json_bytes(header_dict)
            header = MessageHeader.from_bytes(header_bytes)
            nonce = b64u_decode(envelope["nonce"])
            ciphertext = b64u_decode(envelope["ciphertext"])
        except (KeyError, ValueError) as e:
            raise RatchetError(f"Malformed message envelope: {e}")

        # Try skipped keys first
        plaintext = self._try_skipped_keys(header, nonce, ciphertext, header_bytes)
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
            plaintext = _decrypt_aead(mk, nonce, ciphertext, header_bytes)
        except Exception as e:
            raise RatchetError(f"Decryption failed: {e}")

        self.messages_received += 1
        self.last_activity = time.time()

        return plaintext

    def _try_skipped_keys(
        self,
        header: MessageHeader,
        nonce: bytes,
        ciphertext: bytes,
        ad: bytes,
    ) -> bytes | None:
        """Try to decrypt with a skipped message key."""
        key_id = (header.dh_public, header.message_number)
        if key_id in self.state.skipped_keys:
            mk = self.state.skipped_keys.pop(key_id)
            return _decrypt_aead(mk, nonce, ciphertext, ad)
        return None

    def _skip_message_keys(self, until: int) -> None:
        """Store skipped message keys for out-of-order messages."""
        if self.state.chain_key_recv is None:
            return

        if self.state.recv_count + MAX_SKIP < until:
            raise RatchetError("Too many skipped messages")

        while self.state.recv_count < until:
            mk, self.state.chain_key_recv = _kdf_ck(self.state.chain_key_recv)
            assert self.state.dh_remote is not None
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
        assert self.state.dh_remote is not None
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

    def _initialize_sending_chain(self) -> None:
        """Initialize a new sending chain."""
        self.state.prev_send_count = self.state.send_count
        self.state.send_count = 0

        # Generate new DH key pair
        self.state.dh_keypair = generate_encryption_keypair()

        # Derive new sending chain
        # Derive new sending chain
        assert self.state.dh_remote is not None
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
    """Manages Double Ratchet sessions with multiple peers."""

    def __init__(
        self, identity_keypair: KeyPair, storage_path: str | None = None
    ) -> None:
        self.identity_keypair = identity_keypair
        self.storage_path = storage_path
        self.sessions: dict[str, Session] = {}

        # Our prekey for others to contact us
        self._signed_prekey = generate_encryption_keypair()
        self._prekey_signature = sign_message(
            self._signed_prekey.public_key, identity_keypair.private_key
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
        """Create a new session as the initiator (Alice)."""
        # Verify peer's prekey signature
        if not peer_bundle.verify():
            raise RatchetError("Invalid prekey signature")

        # Generate ephemeral key (will be reused as first ratchet key)
        dh_keypair = generate_encryption_keypair()

        # X3DH: Compute shared secret
        dh_x3dh = _dh(dh_keypair.private_key, peer_bundle.signed_prekey)

        # Derive initial root key
        root_key = _hkdf_derive(dh_x3dh, b"x3dh-init")

        # Initialize first sending chain
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
        return session

    def create_session_as_responder(
        self,
        peer_id: str,
        peer_dh_public: bytes,
    ) -> Session:
        """Create a new session as the responder (Bob)."""
        dh_x3dh = _dh(self._signed_prekey.private_key, peer_dh_public)
        root_key = _hkdf_derive(dh_x3dh, b"x3dh-init")

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
        return session

    def get_session(self, peer_id: str) -> Session | None:
        return self.sessions.get(peer_id)
