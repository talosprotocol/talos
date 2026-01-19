"""A2A Session Client facade with FrameCrypto hook for Phase 10.3."""

import hashlib
from datetime import datetime, timezone
from typing import Protocol

from talos_sdk.canonical import canonical_json_bytes

from .errors import A2ACryptoNotConfiguredError
from .models import EncryptedFrame, FrameListResponse, FrameSendResponse
from .sequence_tracker import SequenceStorage, SequenceTracker
from .transport import A2ATransport


class FrameCrypto(Protocol):
    """Hook for Phase 10.3 Ratchet Binding.

    Implement this protocol to enable send_message() and receive_messages().
    """

    def encrypt(self, plaintext: bytes) -> tuple[str, str, str]:
        """Encrypt plaintext and return frame components.

        Returns:
            Tuple of (header_b64u, ciphertext_b64u, ciphertext_hash)

        Note:
            frame_digest is computed by session_client after reserving sender_seq.
        """
        ...

    def decrypt(
        self,
        header_b64u: str,
        ciphertext_b64u: str,
        ciphertext_hash: str | None = None,
    ) -> bytes:
        """Decrypt frame and return plaintext."""
        ...


class A2ASessionClient:
    """High-level session facade for A2A communication.

    Combines transport, sequence tracking, and optional crypto.

    Phase 10.2: Transport-only. Use send_frame() and receive_frames().
    Phase 10.3: With crypto hook, use send_message() and receive_messages().

    Usage:
        # As initiator
        client = await A2ASessionClient.initiate(transport, sender_id, responder_id)

        # As responder
        client = await A2ASessionClient.accept(transport, session_id, sender_id, initiator_id)

        # Send frame (Phase 10.2)
        await client.send_frame(encrypted_frame)

        # Receive frames
        resp = await client.receive_frames()
    """

    def __init__(
        self,
        transport: A2ATransport,
        session_id: str,
        sender_id: str,
        peer_id: str,
        is_initiator: bool,
        sequence_storage: SequenceStorage | None = None,
        crypto: FrameCrypto | None = None,
    ):
        self._transport = transport
        self._session_id = session_id
        self._sender_id = sender_id
        self._peer_id = peer_id
        self._is_initiator = is_initiator
        self._seq_tracker = SequenceTracker(session_id, sender_id, sequence_storage)
        self._crypto = crypto

    @property
    def session_id(self) -> str:
        """Get the session ID."""
        return self._session_id

    @property
    def sender_id(self) -> str:
        """Get the sender (self) ID."""
        return self._sender_id

    @property
    def peer_id(self) -> str:
        """Get the peer ID."""
        return self._peer_id

    @property
    def is_initiator(self) -> bool:
        """Whether this client initiated the session."""
        return self._is_initiator

    async def send_frame(self, frame: EncryptedFrame) -> FrameSendResponse:
        """Send a pre-constructed encrypted frame.

        Use this in Phase 10.2 when constructing frames externally.
        """
        return await self._transport.send_frame(self._session_id, frame)

    async def receive_frames(
        self, cursor: str | None = None, limit: int = 100
    ) -> FrameListResponse:
        """Receive encrypted frames with cursor pagination."""
        return await self._transport.receive_frames(
            self._session_id, cursor=cursor, limit=limit
        )

    async def send_message(self, plaintext: bytes) -> FrameSendResponse:
        """Encrypt and send a message.

        Requires FrameCrypto hook (Phase 10.3).
        Sequence is reserved atomically before encryption for retry safety.

        Raises:
            A2ACryptoNotConfiguredError: If crypto hook not provided.
        """
        if self._crypto is None:
            raise A2ACryptoNotConfiguredError()

        # Reserve sequence ONCE before encryption (retry-safe)
        sender_seq = self._seq_tracker.reserve()

        # Encrypt using crypto hook (returns 3 values, not 4)
        header_b64u, ciphertext_b64u, ciphertext_hash = self._crypto.encrypt(plaintext)

        # Compute frame_digest per LOCKED SPEC
        # Preimage: {schema_id, schema_version, session_id, sender_id, sender_seq, header_b64u, ciphertext_hash}
        preimage = {
            "schema_id": "talos.a2a.encrypted_frame",
            "schema_version": "v1",
            "session_id": self._session_id,
            "sender_id": self._sender_id,
            "sender_seq": sender_seq,
            "header_b64u": header_b64u,
            "ciphertext_hash": ciphertext_hash,
        }
        frame_digest = hashlib.sha256(canonical_json_bytes(preimage)).hexdigest()

        frame = EncryptedFrame(
            session_id=self._session_id,
            sender_id=self._sender_id,
            sender_seq=sender_seq,
            header_b64u=header_b64u,
            ciphertext_b64u=ciphertext_b64u,
            frame_digest=frame_digest,
            ciphertext_hash=ciphertext_hash,
            created_at=datetime.now(timezone.utc),
        )

        # Transport handles retry internally (same frame on timeout)
        return await self.send_frame(frame)

    async def receive_messages(self, cursor: str | None = None) -> list[bytes]:
        """Receive and decrypt messages.

        Requires FrameCrypto hook (Phase 10.3).

        Raises:
            A2ACryptoNotConfiguredError: If crypto hook not provided.
        """
        if self._crypto is None:
            raise A2ACryptoNotConfiguredError()

        resp = await self.receive_frames(cursor)
        return [
            self._crypto.decrypt(
                frame.header_b64u, frame.ciphertext_b64u, frame.ciphertext_hash
            )
            for frame in resp.items
        ]

    async def rotate(self) -> None:
        """Rotate session keys."""
        await self._transport.rotate_session(self._session_id)

    async def close(self) -> None:
        """Close the session."""
        await self._transport.close_session(self._session_id)

    @classmethod
    async def initiate(
        cls,
        transport: A2ATransport,
        sender_id: str,
        responder_id: str,
        sequence_storage: SequenceStorage | None = None,
        crypto: FrameCrypto | None = None,
    ) -> "A2ASessionClient":
        """Create a new session as initiator."""
        resp = await transport.create_session(responder_id)
        return cls(
            transport=transport,
            session_id=resp.session_id,
            sender_id=sender_id,
            peer_id=responder_id,
            is_initiator=True,
            sequence_storage=sequence_storage,
            crypto=crypto,
        )

    @classmethod
    async def accept(
        cls,
        transport: A2ATransport,
        session_id: str,
        sender_id: str,
        initiator_id: str,
        sequence_storage: SequenceStorage | None = None,
        crypto: FrameCrypto | None = None,
    ) -> "A2ASessionClient":
        """Accept a pending session as responder."""
        await transport.accept_session(session_id)
        return cls(
            transport=transport,
            session_id=session_id,
            sender_id=sender_id,
            peer_id=initiator_id,
            is_initiator=False,
            sequence_storage=sequence_storage,
            crypto=crypto,
        )
