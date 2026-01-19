#!/usr/bin/env python3
"""Talos SDK Benchmarks.

Comprehensive benchmarks for cryptographic operations:
- Wallet operations (key generation, signing, verification)
- Double Ratchet (encryption, decryption, key derivation)
- A2A frame operations (digest computation, frame creation)
- Session operations (create, persist, restore)

Run: python benchmarks/bench_crypto.py
"""

import json
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add src for SDK imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from talos_sdk import Wallet, TalosClient
from talos_sdk.a2a.ratchet_crypto import RatchetFrameCrypto
from talos_sdk.canonical import canonical_json_bytes
from talos_sdk.crypto import generate_signing_keypair
from talos_sdk.session import SessionManager
import hashlib


@dataclass
class BenchResult:
    name: str
    iterations: int
    total_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    ops_per_sec: float


def bench(name: str, iterations: int, fn):
    """Run a benchmark and return results."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms

    total = sum(times)
    return BenchResult(
        name=name,
        iterations=iterations,
        total_ms=total,
        avg_ms=statistics.mean(times),
        min_ms=min(times),
        max_ms=max(times),
        ops_per_sec=iterations / (total / 1000),
    )


def print_result(r: BenchResult):
    print(f"  {r.name:40} {r.avg_ms:8.3f} ms  ({r.ops_per_sec:,.0f} ops/sec)")


def main():
    print("=" * 70)
    print("  Talos SDK Benchmarks")
    print("=" * 70)
    print()

    results = []

    # =========================================================================
    # Wallet Operations
    # =========================================================================
    print("## Wallet Operations")

    # Key generation
    r = bench("Wallet.generate()", 100, lambda: Wallet.generate())
    results.append(r)
    print_result(r)

    # Wallet from seed
    seed = b"x" * 32
    r = bench("Wallet.from_seed()", 1000, lambda: Wallet.from_seed(seed))
    results.append(r)
    print_result(r)

    # Signing
    wallet = Wallet.generate()
    message = b"Hello, Talos! This is a test message for benchmarking."
    r = bench("Wallet.sign(64B)", 1000, lambda: wallet.sign(message))
    results.append(r)
    print_result(r)

    # Signing large message
    large_msg = b"x" * 10240  # 10KB
    r = bench("Wallet.sign(10KB)", 1000, lambda: wallet.sign(large_msg))
    results.append(r)
    print_result(r)

    # Verification
    sig = wallet.sign(message)
    pub = wallet.public_key
    r = bench("Wallet.verify()", 1000, lambda: Wallet.verify(message, sig, pub))
    results.append(r)
    print_result(r)

    # DID generation
    r = bench("Wallet.to_did()", 1000, lambda: wallet.to_did())
    results.append(r)
    print_result(r)

    print()

    # =========================================================================
    # Double Ratchet Operations
    # =========================================================================
    print("## Double Ratchet Operations")

    # Session creation
    alice_kp = generate_signing_keypair()
    bob_kp = generate_signing_keypair()

    def create_session_pair():
        alice_mgr = SessionManager(alice_kp)
        bob_mgr = SessionManager(bob_kp)
        bob_bundle = bob_mgr.get_prekey_bundle()
        alice_sess = alice_mgr.create_session_as_initiator("bob", bob_bundle)
        bob_sess = bob_mgr.create_session_as_responder(
            "alice", alice_sess.state.dh_keypair.public_key
        )
        return alice_sess, bob_sess

    r = bench("Session create pair (X3DH)", 100, lambda: create_session_pair())
    results.append(r)
    print_result(r)

    # Encryption
    alice_sess, bob_sess = create_session_pair()
    msg = b"Hello Bob, this is a test message!"

    r = bench("Session.encrypt(35B)", 1000, lambda: alice_sess.encrypt(msg))
    results.append(r)
    print_result(r)

    # Encryption large
    large_msg = b"x" * 10240
    r = bench("Session.encrypt(10KB)", 500, lambda: alice_sess.encrypt(large_msg))
    results.append(r)
    print_result(r)

    # Full roundtrip (create sessions, encrypt, decrypt)
    def roundtrip_fresh():
        a_sess, b_sess = create_session_pair()
        ct = a_sess.encrypt(msg)
        return b_sess.decrypt(ct)

    r = bench("Session roundtrip(35B)", 200, roundtrip_fresh)
    results.append(r)
    print_result(r)

    print()

    # =========================================================================
    # RatchetFrameCrypto Operations
    # =========================================================================
    print("## RatchetFrameCrypto Operations")

    alice_sess, bob_sess = create_session_pair()
    alice_crypto = RatchetFrameCrypto(alice_sess)
    bob_crypto = RatchetFrameCrypto(bob_sess)

    r = bench("RatchetFrameCrypto.encrypt()", 500, lambda: alice_crypto.encrypt(msg))
    results.append(r)
    print_result(r)

    header, ct, ct_hash = alice_crypto.encrypt(msg)

    def decrypt_frame():
        nonlocal alice_sess, bob_sess, alice_crypto, bob_crypto
        alice_sess, bob_sess = create_session_pair()
        alice_crypto = RatchetFrameCrypto(alice_sess)
        bob_crypto = RatchetFrameCrypto(bob_sess)
        h, c, ch = alice_crypto.encrypt(msg)
        return bob_crypto.decrypt(h, c, ch)

    r = bench("RatchetFrameCrypto roundtrip", 200, decrypt_frame)
    results.append(r)
    print_result(r)

    print()

    # =========================================================================
    # Canonical JSON & Digest Operations
    # =========================================================================
    print("## Canonical JSON & Digest Operations")

    frame_preimage = {
        "schema_id": "talos.a2a.encrypted_frame",
        "schema_version": "v1",
        "session_id": "01234567-89ab-7cde-8f01-23456789abcd",
        "sender_id": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
        "sender_seq": 42,
        "header_b64u": "eyJhbGciOiJFZERTQSJ9",
        "ciphertext_hash": "a" * 64,
    }

    r = bench("canonical_json_bytes()", 5000, lambda: canonical_json_bytes(frame_preimage))
    results.append(r)
    print_result(r)

    canonical = canonical_json_bytes(frame_preimage)
    r = bench("SHA256 digest", 10000, lambda: hashlib.sha256(canonical).hexdigest())
    results.append(r)
    print_result(r)

    print()

    # =========================================================================
    # Session Serialization
    # =========================================================================
    print("## Session Serialization")

    alice_sess, bob_sess = create_session_pair()

    r = bench("Session.to_dict()", 1000, lambda: alice_sess.to_dict())
    results.append(r)
    print_result(r)

    state_dict = alice_sess.to_dict()
    state_json = json.dumps(state_dict)

    r = bench("json.dumps(session)", 1000, lambda: json.dumps(alice_sess.to_dict()))
    results.append(r)
    print_result(r)

    r = bench("json.loads(session)", 1000, lambda: json.loads(state_json))
    results.append(r)
    print_result(r)

    from talos_sdk.session import Session
    r = bench("Session.from_dict()", 500, lambda: Session.from_dict(state_dict))
    results.append(r)
    print_result(r)

    print()

    # =========================================================================
    # Summary
    # =========================================================================
    print("=" * 70)
    print("  Summary")
    print("=" * 70)
    print()

    # Group by category
    categories = {
        "Wallet": [],
        "Ratchet": [],
        "Frame": [],
        "Canonical": [],
        "Serialize": [],
    }

    for r in results:
        if "Wallet" in r.name or "to_did" in r.name:
            categories["Wallet"].append(r)
        elif "Session" in r.name and "dict" not in r.name.lower() and "json" not in r.name.lower():
            categories["Ratchet"].append(r)
        elif "Ratchet" in r.name:
            categories["Frame"].append(r)
        elif "canonical" in r.name.lower() or "SHA" in r.name:
            categories["Canonical"].append(r)
        else:
            categories["Serialize"].append(r)

    for cat, items in categories.items():
        if items:
            avg = statistics.mean([r.ops_per_sec for r in items])
            print(f"  {cat:15} avg ops/sec: {avg:,.0f}")

    print()
    print(f"  Total benchmarks run: {len(results)}")
    print()


if __name__ == "__main__":
    main()
