import os
import sys
from dataclasses import dataclass

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from talos_sdk.adapters.crypto import Ed25519CryptoAdapter  # noqa: E402
from talos_sdk.adapters.hash import NativeHashAdapter  # noqa: E402
from talos_sdk.adapters.memory_store import (  # noqa: E402
    InMemoryAuditStore,
    InMemoryKeyValueStore,
)


def test_hash_adapter():
    adapter = NativeHashAdapter()
    data = b"hello"
    h = adapter.sha256(data)
    assert len(h) == 32
    # Known hash for "hello"
    assert h.hex() == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    obj = {"b": 2, "a": 1}
    # Canonical: {"a":1,"b":2}
    h_canon = adapter.canonical_hash(obj)
    # sha256({"a":1,"b":2})
    # echo -n '{"a":1,"b":2}' | openssl dgst -sha256
    # 6325...
    assert len(h_canon) == 32


def test_crypto_adapter():
    adapter = Ed25519CryptoAdapter()
    # 32 bytes seed
    seed = b"12345678901234567890123456789012"
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.from_private_bytes(seed)
    # pub bytes
    from cryptography.hazmat.primitives import serialization

    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    # Actually just call sign
    msg = b"hello world"
    sig = adapter.sign(msg, seed)
    assert len(sig) == 64

    valid = adapter.verify(msg, sig, pub_bytes)
    assert valid is True

    invalid = adapter.verify(b"hallo", sig, pub_bytes)
    assert invalid is False


def test_kv_store():
    store = InMemoryKeyValueStore()
    store.put("k", b"v")
    assert store.get("k") == b"v"
    store.delete("k")
    assert store.get("k") is None


@dataclass
class MockEvent:
    event_id: str
    timestamp: float


def test_audit_store():
    store = InMemoryAuditStore()
    e1 = MockEvent("1", 100.0)
    store.append(e1)

    page = store.list()
    assert len(page.events) == 1
    assert page.events[0] == e1
