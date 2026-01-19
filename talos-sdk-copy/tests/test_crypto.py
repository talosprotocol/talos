from talos_sdk.crypto import (
    KeyPair,
    b64u_decode,
    b64u_encode,
    generate_encryption_keypair,
    generate_signing_keypair,
    sign_message,
    verify_signature,
)


def test_b64u_encoding():
    data = b"hello world"
    encoded = b64u_encode(data)
    assert encoded == "aGVsbG8gd29ybGQ"  # no padding
    decoded = b64u_decode(encoded)
    assert decoded == data


def test_b64u_decode_padding():
    # Test cases with different lengths requiring padding
    assert b64u_decode("YQ") == b"a"  # "YQ=="
    assert b64u_decode("YWI") == b"ab"  # "YWI="
    assert b64u_decode("YWJj") == b"abc"  # "YWJj"


def test_encryption_keypair_lifecycle():
    kp = generate_encryption_keypair()
    assert kp.key_type == "x25519"
    assert len(kp.public_key) == 32
    assert len(kp.private_key) == 32

    # Test serialization
    data = kp.to_dict()
    assert data["type"] == "x25519"
    assert "public" in data
    assert "private" in data

    # Test deserialization
    kp2 = KeyPair.from_dict(data)
    assert kp2.public_key == kp.public_key
    assert kp2.private_key == kp.private_key
    assert kp2.key_type == kp.key_type


def test_signing_keypair_lifecycle():
    kp = generate_signing_keypair()
    assert kp.key_type == "ed25519"
    assert len(kp.public_key) == 32
    assert len(kp.private_key) == 32


def test_sign_and_verify():
    kp = generate_signing_keypair()
    msg = b"test message for signing"

    # Sign
    signature = sign_message(msg, kp.private_key)
    assert len(signature) == 64

    # Verify Success
    assert verify_signature(msg, signature, kp.public_key) is True

    # Verify Failure (Wrong Message)
    assert verify_signature(b"altered message", signature, kp.public_key) is False

    # Verify Failure (Wrong Key)
    other_kp = generate_signing_keypair()
    assert verify_signature(msg, signature, other_kp.public_key) is False


def test_verify_invalid_input():
    # Helper to test exception handling in verify_signature
    assert verify_signature(b"msg", b"sig", b"short_key") is False
