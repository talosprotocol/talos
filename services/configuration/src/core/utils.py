"""Utility functions for the configuration service."""

import base64
import hashlib
from datetime import datetime

import msgpack  # type: ignore

from .storage import IdempotencyRecord  # type: ignore


def encode_cursor(created_at: datetime, item_id: str) -> str:
    """Encode a pagination cursor."""
    # Format: base64url(msgpack([timestamp_str, id]))
    # Using ISO format string for simple serialization in msgpack
    score = created_at.isoformat()
    packed = msgpack.packb([score, item_id])
    return base64.urlsafe_b64encode(packed).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    """Decode a pagination cursor."""
    try:
        packed = base64.urlsafe_b64decode(cursor)
        unpacked = msgpack.unpackb(packed)
        if not isinstance(unpacked, list) or len(unpacked) != 2:
            raise ValueError("Invalid cursor format")
        return datetime.fromisoformat(unpacked[0]), unpacked[1]
    except Exception as e:
        raise ValueError("Invalid cursor") from e


def check_idempotency_conflict(
    record: IdempotencyRecord, current_digest: str
) -> bool:
    """Check for idempotency conflicts.

    Returns True if there is a conflict (same key, different body).
    Returns False if it is a valid replay (same key, same body).
    """
    return bool(record.request_digest != current_digest)


def compute_body_digest(body: bytes) -> str:
    """Compute SHA256 digest of request body."""
    return hashlib.sha256(body).hexdigest()
