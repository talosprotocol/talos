import hashlib
import json
from typing import Any

from talos_sdk.ports.hash import IHashPort


class NativeHashAdapter(IHashPort):
    def sha256(self, data: bytes) -> bytes:
        return hashlib.sha256(data).digest()

    def canonical_hash(self, obj: Any) -> bytes:
        from talos_sdk.canonical import canonical_json_bytes
        return self.sha256(canonical_json_bytes(obj))
