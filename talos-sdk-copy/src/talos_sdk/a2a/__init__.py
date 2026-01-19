"""Talos SDK A2A Module.

Provides HTTP transport, sequence tracking, and session management
for secure Agent-to-Agent communication.

Phase 10.2: Transport-only (no encryption). Phase 10.3 adds FrameCrypto binding.
"""

from .errors import (
    A2ACryptoNotConfiguredError,
    A2AError,
    A2AFrameDigestMismatchError,
    A2AFrameReplayError,
    A2AFrameSequenceTooFarError,
    A2ASessionNotFoundError,
    A2ASessionStateInvalidError,
    A2ATransportError,
)
from .models import (
    EncryptedFrame,
    ErrorResponse,
    FrameListResponse,
    FrameSendResponse,
    GroupResponse,
    SessionResponse,
)
from .ratchet_crypto import RatchetFrameCrypto
from .sequence_tracker import InMemorySequenceStorage, SequenceStorage, SequenceTracker
from .session_client import A2ASessionClient, FrameCrypto
from .transport import A2ATransport

__all__ = [
    # Errors
    "A2AError",
    "A2ATransportError",
    "A2ASessionNotFoundError",
    "A2ASessionStateInvalidError",
    "A2AFrameReplayError",
    "A2AFrameDigestMismatchError",
    "A2AFrameSequenceTooFarError",
    "A2ACryptoNotConfiguredError",
    # Models
    "EncryptedFrame",
    "SessionResponse",
    "FrameSendResponse",
    "FrameListResponse",
    "GroupResponse",
    "ErrorResponse",
    # Sequence
    "SequenceTracker",
    "SequenceStorage",
    "InMemorySequenceStorage",
    # Transport
    "A2ATransport",
    # Session
    "A2ASessionClient",
    "FrameCrypto",
    # Ratchet
    "RatchetFrameCrypto",
]
