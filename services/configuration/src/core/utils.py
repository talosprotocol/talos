
import base64
import msgpack
from datetime import datetime
from typing import Optional, Tuple
from src.core.storage import IdempotencyRecord
import hashlib

def encode_cursor(created_at: datetime, id: str) -> str:
    # Format: base64url(msgpack([timestamp_str, id]))
    # Using ISO format string for simple serialization in msgpack
    score = created_at.isoformat()
    packed = msgpack.packb([score, id])
    return base64.urlsafe_b64encode(packed).decode('utf-8')

def decode_cursor(cursor: str) -> Tuple[datetime, str]:
    try:
        packed = base64.urlsafe_b64decode(cursor)
        unpacked = msgpack.unpackb(packed)
        if not isinstance(unpacked, list) or len(unpacked) != 2:
             raise ValueError("Invalid cursor format")
        return datetime.fromisoformat(unpacked[0]), unpacked[1]
    except Exception:
        raise ValueError("Invalid cursor")

def check_idempotency_conflict(record: IdempotencyRecord, current_digest: str) -> bool:
    """
    Returns True if there is a conflict (same key, different body).
    Returns False if it is a valid replay (same key, same body).
    """
    return record.request_digest != current_digest

def compute_body_digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()
