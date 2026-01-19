"""Talos SDK Errors.

Canonical error taxonomy as defined in SDK_CONTRACT.md.
"""

from typing import Any


class TalosError(Exception):
    """Base class for all Talos SDK errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict | None = None,
        request_id: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a TalosError.

        Args:
            code: Error code from ERROR_TAXONOMY.md (e.g., TALOS_DENIED)
            message: Human-readable error message
            details: Additional context (optional)
            request_id: Correlation ID if available (optional)
            cause: Underlying exception if chained (optional)
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
        self.cause = cause

    def to_dict(self) -> dict:
        """Convert error to dictionary representation."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
            "cause": str(self.cause) if self.cause else None,
        }


# Authorization Errors
class TalosDeniedError(TalosError):
    """Authorization denied."""

    def __init__(self, message: str = "Authorization denied", **kwargs: Any) -> None:
        super().__init__("TALOS_DENIED", message, **kwargs)


class TalosInvalidCapabilityError(TalosError):
    """Capability token invalid."""

    def __init__(
        self, message: str = "Invalid capability token", **kwargs: Any
    ) -> None:
        super().__init__("TALOS_INVALID_CAPABILITY", message, **kwargs)


class TalosRevokedError(TalosError):
    """Identity or key revoked."""

    def __init__(self, message: str = "Identity revoked", **kwargs: Any) -> None:
        super().__init__("TALOS_REVOKED", message, **kwargs)


# Protocol Errors
class TalosProtocolMismatchError(TalosError):
    """Protocol version incompatible."""

    def __init__(
        self, message: str = "Protocol version mismatch", **kwargs: Any
    ) -> None:
        super().__init__("TALOS_PROTOCOL_MISMATCH", message, **kwargs)


class TalosFrameInvalidError(TalosError):
    """Wire frame decode failure."""

    def __init__(self, message: str = "Invalid frame", **kwargs: Any) -> None:
        super().__init__("TALOS_FRAME_INVALID", message, **kwargs)


# Crypto Errors
class TalosCryptoError(TalosError):
    """Cryptographic operation failed."""

    def __init__(
        self, message: str = "Cryptographic operation failed", **kwargs: Any
    ) -> None:
        super().__init__("TALOS_CRYPTO_ERROR", message, **kwargs)


class TalosInvalidInputError(TalosError):
    """Invalid input parameters."""

    def __init__(self, message: str = "Invalid input", **kwargs: Any) -> None:
        super().__init__("TALOS_INVALID_INPUT", message, **kwargs)


# Transport Errors
class TalosTransportTimeoutError(TalosError):
    """Transport operation timed out."""

    def __init__(self, message: str = "Transport timeout", **kwargs: Any) -> None:
        super().__init__("TALOS_TRANSPORT_TIMEOUT", message, **kwargs)


class TalosTransportError(TalosError):
    """Transport-level failure."""

    def __init__(self, message: str = "Transport error", **kwargs: Any) -> None:
        super().__init__("TALOS_TRANSPORT_ERROR", message, **kwargs)
