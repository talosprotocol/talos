"""A2A Error types and mapping factory."""

from typing import TYPE_CHECKING

from talos_sdk.errors import TalosError

if TYPE_CHECKING:
    from .models import ErrorResponse


class A2AError(TalosError):
    """Base class for A2A errors."""
    pass


class A2ATransportError(A2AError):
    """HTTP transport failure."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__("A2A_TRANSPORT_ERROR", message)
        self.status_code = status_code


class A2ASessionNotFoundError(A2AError):
    """Session not found."""

    def __init__(self):
        super().__init__("A2A_SESSION_NOT_FOUND", "Session not found")


class A2ASessionStateInvalidError(A2AError):
    """Invalid session state transition."""

    def __init__(self, current_state: str = ""):
        super().__init__("A2A_SESSION_STATE_INVALID", f"Invalid state: {current_state}")
        self.current_state = current_state


class A2AFrameReplayError(A2AError):
    """Duplicate frame detected (replay)."""

    def __init__(self, sender_seq: int = -1):
        super().__init__("A2A_FRAME_REPLAY_DETECTED", f"Duplicate sender_seq: {sender_seq}")
        self.sender_seq = sender_seq


class A2AFrameDigestMismatchError(A2AError):
    """Frame digest does not match computed value."""

    def __init__(self):
        super().__init__("A2A_FRAME_DIGEST_MISMATCH", "Frame digest mismatch")


class A2AFrameSequenceTooFarError(A2AError):
    """Sequence number exceeds MAX_FUTURE_DELTA."""

    def __init__(self, sender_seq: int = -1, expected_seq: int = -1):
        super().__init__("A2A_FRAME_SEQUENCE_TOO_FAR", f"Sequence too far: {sender_seq}. Expected: {expected_seq}")
        self.sender_seq = sender_seq
        self.expected_seq = expected_seq


class A2AFrameSizeExceededError(A2AError):
    """Frame payload exceeds maximum size."""

    def __init__(self, size: int = -1, limit: int = -1):
        super().__init__("A2A_FRAME_SIZE_EXCEEDED", f"Frame size {size} exceeds limit {limit}")
        self.size = size
        self.limit = limit


class A2ACryptoNotConfiguredError(A2AError):
    """FrameCrypto hook not configured (Phase 10.3 required)."""

    def __init__(self):
        super().__init__("A2A_CRYPTO_NOT_CONFIGURED", "FrameCrypto not configured")


def raise_mapped_error(err: "ErrorResponse", status_code: int | None = None) -> None:
    """Map gateway ErrorResponse to SDK exception.

    Extracts details from err.details when available.
    """
    code = err.error_code
    details = err.details or {}

    if code == "A2A_SESSION_NOT_FOUND":
        raise A2ASessionNotFoundError()

    if code == "A2A_SESSION_STATE_INVALID":
        raise A2ASessionStateInvalidError(current_state=str(details.get("current_state", "")))

    if code == "A2A_FRAME_REPLAY_DETECTED":
        seq = details.get("sender_seq", -1)
        raise A2AFrameReplayError(sender_seq=int(seq) if seq is not None else -1)

    if code == "A2A_FRAME_DIGEST_MISMATCH":
        raise A2AFrameDigestMismatchError()

    if code == "A2A_FRAME_SEQUENCE_TOO_FAR":
        seq = details.get("sender_seq", details.get("received_seq", -1))
        expected = details.get("expected_seq", -1)
        raise A2AFrameSequenceTooFarError(
            sender_seq=int(seq) if seq is not None else -1,
            expected_seq=int(expected) if expected is not None else -1
        )

    if code == "A2A_FRAME_SIZE_EXCEEDED":
        size = details.get("size", -1)
        limit = details.get("limit", -1)
        raise A2AFrameSizeExceededError(
            size=int(size) if size is not None else -1,
            limit=int(limit) if limit is not None else -1
        )

    # Default fallback
    raise A2ATransportError(err.message, status_code=status_code)
