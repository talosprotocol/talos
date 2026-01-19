"""Talos SDK Canonical JSON.

Implements the canonicalization rules from CANONICAL_JSON.md.
"""

import json
from typing import Any


def canonical_json(obj: Any) -> str:
    """Serialize an object to canonical JSON.

    Rules:
    - Keys sorted lexicographically
    - No whitespace outside strings
    - UTF-8 encoding
    - Minimal escaping

    Args:
        obj: Object to serialize

    Returns:
        Canonical JSON string
    """

    def _preprocess(o: Any) -> Any:
        if isinstance(o, dict):
            return {k: _preprocess(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_preprocess(v) for v in o]
        if isinstance(o, float) and o.is_integer():
            return int(o)
        return o

    return json.dumps(
        _preprocess(obj),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize an object to canonical JSON bytes.

    Args:
        obj: Object to serialize

    Returns:
        UTF-8 encoded canonical JSON bytes
    """
    return canonical_json(obj).encode("utf-8")
