"""Identifier helpers for root Talos runtime code."""

from __future__ import annotations

import secrets
import time


def uuid7() -> str:
    """Generate a lowercase UUIDv7 string without external runtime dependencies."""
    ms = time.time_ns() // 1_000_000
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    uuid_int = (ms & 0xFFFFFFFFFFFF) << 80
    uuid_int |= 0x7 << 76
    uuid_int |= rand_a << 64
    uuid_int |= 0x2 << 62
    uuid_int |= rand_b

    h = f"{uuid_int:032x}"
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"
