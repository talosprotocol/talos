"""Unit tests for RatchetFrameCrypto (Phase 10.3)."""

import pytest
from unittest.mock import MagicMock, patch
import json
import hashlib

from talos_sdk.a2a.ratchet_crypto import (
    RatchetFrameCrypto,
    _b64u_decode_strict,
    NONCE_LEN,
)
from talos_sdk.crypto import b64u_encode


# === Base64url Strict Decode Tests ===


class TestB64uDecodeStrict:
    def test_valid_decode(self):
        """Valid base64url without padding decodes correctly."""
        # "hello" in base64url
        result = _b64u_decode_strict("aGVsbG8")
        assert result == b"hello"

    def test_rejects_padding(self):
        """Inputs with padding are rejected."""
        with pytest.raises(ValueError, match="must not contain padding"):
            _b64u_decode_strict("aGVsbG8=")

    def test_rejects_invalid_length(self):
        """Inputs with len % 4 == 1 are rejected (impossible base64url)."""
        # "a" has length 1, which is impossible for valid base64url
        with pytest.raises(ValueError, match="Invalid base64url length"):
            _b64u_decode_strict("a")

        # "abcde" has length 5, len % 4 == 1
        with pytest.raises(ValueError, match="Invalid base64url length"):
            _b64u_decode_strict("abcde")

    def test_valid_lengths(self):
        """Valid lengths decode correctly."""
        # len % 4 == 0 (no padding needed)
        assert _b64u_decode_strict("YWJj") == b"abc"

        # len % 4 == 2 (needs 2 padding)
        assert _b64u_decode_strict("YWI") == b"ab"

        # len % 4 == 3 (needs 1 padding)
        assert _b64u_decode_strict("YQ") == b"a"


# === RatchetFrameCrypto Tests ===


class TestRatchetFrameCrypto:
    @pytest.fixture
    def mock_session(self):
        """Create a mock Session with encrypt/decrypt."""
        session = MagicMock()

        # Mock encrypt to return a valid envelope
        def mock_encrypt(plaintext):
            nonce = b"\x00" * 12  # 12-byte nonce
            ciphertext = b"encrypted:" + plaintext  # Fake ciphertext
            envelope = {
                "header": {"dh": "AAAA", "pn": 0, "n": 0},
                "nonce": b64u_encode(nonce),
                "ciphertext": b64u_encode(ciphertext),
            }
            from talos_sdk.canonical import canonical_json_bytes

            return canonical_json_bytes(envelope)

        session.encrypt = mock_encrypt
        return session

    def test_encrypt_returns_three_values(self, mock_session):
        """encrypt() returns (header_b64u, ciphertext_b64u, ciphertext_hash)."""
        crypto = RatchetFrameCrypto(mock_session)
        result = crypto.encrypt(b"test message")

        assert len(result) == 3
        header_b64u, ciphertext_b64u, ciphertext_hash = result

        assert isinstance(header_b64u, str)
        assert isinstance(ciphertext_b64u, str)
        assert isinstance(ciphertext_hash, str)
        assert len(ciphertext_hash) == 64  # SHA-256 hex

    def test_ciphertext_hash_excludes_nonce(self, mock_session):
        """ciphertext_hash is SHA-256 of ciphertext only, not nonce."""
        crypto = RatchetFrameCrypto(mock_session)
        _, ciphertext_b64u, ciphertext_hash = crypto.encrypt(b"test")

        # Decode and split
        combined = _b64u_decode_strict(ciphertext_b64u)
        nonce = combined[:NONCE_LEN]
        ciphertext = combined[NONCE_LEN:]

        # Hash should be of ciphertext only
        expected_hash = hashlib.sha256(ciphertext).hexdigest()
        assert ciphertext_hash == expected_hash

        # Hash should NOT include nonce
        wrong_hash = hashlib.sha256(combined).hexdigest()
        assert ciphertext_hash != wrong_hash

    def test_nonce_length_is_12(self, mock_session):
        """Nonce is exactly 12 bytes (regression guard)."""
        crypto = RatchetFrameCrypto(mock_session)
        _, ciphertext_b64u, _ = crypto.encrypt(b"test")

        combined = _b64u_decode_strict(ciphertext_b64u)
        assert len(combined) >= NONCE_LEN

        nonce = combined[:NONCE_LEN]
        assert len(nonce) == 12

    def test_header_is_canonical_json(self, mock_session):
        """header_b64u is canonical JSON bytes."""
        crypto = RatchetFrameCrypto(mock_session)
        header_b64u, _, _ = crypto.encrypt(b"test")

        header_bytes = _b64u_decode_strict(header_b64u)
        header_dict = json.loads(header_bytes.decode("utf-8"))

        # Verify keys are sorted (canonical)
        assert list(header_dict.keys()) == sorted(header_dict.keys())

    def test_encrypt_rejects_unexpected_nonce_length(self):
        """encrypt() raises if Session returns wrong nonce length."""
        session = MagicMock()

        def bad_encrypt(plaintext):
            nonce = b"\x00" * 8  # Wrong: 8 bytes instead of 12
            envelope = {
                "header": {"dh": "AAAA", "pn": 0, "n": 0},
                "nonce": b64u_encode(nonce),
                "ciphertext": b64u_encode(b"ct"),
            }
            from talos_sdk.canonical import canonical_json_bytes

            return canonical_json_bytes(envelope)

        session.encrypt = bad_encrypt
        crypto = RatchetFrameCrypto(session)

        with pytest.raises(ValueError, match="Unexpected nonce length"):
            crypto.encrypt(b"test")


class TestRatchetFrameCryptoDecrypt:
    @pytest.fixture
    def mock_session_decrypt(self):
        """Create a mock Session with decrypt."""
        session = MagicMock()
        session.decrypt.return_value = b"decrypted plaintext"
        return session

    def test_decrypt_with_valid_hash(self, mock_session_decrypt):
        """decrypt() succeeds with valid ciphertext_hash."""
        crypto = RatchetFrameCrypto(mock_session_decrypt)

        # Prepare valid inputs
        header_dict = {"dh": "AAAA", "n": 0, "pn": 0}
        from talos_sdk.canonical import canonical_json_bytes

        header_b64u = b64u_encode(canonical_json_bytes(header_dict))

        nonce = b"\x00" * 12
        ciphertext = b"encrypted data"
        ciphertext_b64u = b64u_encode(nonce + ciphertext)
        ciphertext_hash = hashlib.sha256(ciphertext).hexdigest()

        result = crypto.decrypt(header_b64u, ciphertext_b64u, ciphertext_hash)
        assert result == b"decrypted plaintext"

    def test_decrypt_rejects_hash_mismatch(self, mock_session_decrypt):
        """decrypt() raises if ciphertext_hash doesn't match."""
        crypto = RatchetFrameCrypto(mock_session_decrypt)

        header_dict = {"dh": "AAAA", "n": 0, "pn": 0}
        from talos_sdk.canonical import canonical_json_bytes

        header_b64u = b64u_encode(canonical_json_bytes(header_dict))

        nonce = b"\x00" * 12
        ciphertext = b"encrypted data"
        ciphertext_b64u = b64u_encode(nonce + ciphertext)
        wrong_hash = "0" * 64

        with pytest.raises(ValueError, match="hash mismatch"):
            crypto.decrypt(header_b64u, ciphertext_b64u, wrong_hash)

    def test_decrypt_rejects_too_short_ciphertext(self, mock_session_decrypt):
        """decrypt() raises if combined bytes are shorter than nonce."""
        crypto = RatchetFrameCrypto(mock_session_decrypt)

        header_dict = {"dh": "AAAA", "n": 0, "pn": 0}
        from talos_sdk.canonical import canonical_json_bytes

        header_b64u = b64u_encode(canonical_json_bytes(header_dict))
        ciphertext_b64u = b64u_encode(b"short")  # Only 5 bytes

        with pytest.raises(ValueError, match="too short"):
            crypto.decrypt(header_b64u, ciphertext_b64u)

    def test_decrypt_rejects_invalid_header_json(self, mock_session_decrypt):
        """decrypt() raises if header is not valid JSON."""
        crypto = RatchetFrameCrypto(mock_session_decrypt)

        header_b64u = b64u_encode(b"not valid json")
        ciphertext_b64u = b64u_encode(b"\x00" * 20)

        with pytest.raises(ValueError, match="Invalid header JSON"):
            crypto.decrypt(header_b64u, ciphertext_b64u)

    def test_decrypt_rejects_missing_header_fields(self, mock_session_decrypt):
        """decrypt() raises if required header fields are missing."""
        crypto = RatchetFrameCrypto(mock_session_decrypt)

        # Missing 'pn' field
        header_dict = {"dh": "AAAA", "n": 0}
        from talos_sdk.canonical import canonical_json_bytes

        header_b64u = b64u_encode(canonical_json_bytes(header_dict))
        ciphertext_b64u = b64u_encode(b"\x00" * 20)

        with pytest.raises(ValueError, match="Missing header fields"):
            crypto.decrypt(header_b64u, ciphertext_b64u)

    def test_decrypt_rejects_padded_b64url(self, mock_session_decrypt):
        """decrypt() rejects base64url with padding."""
        crypto = RatchetFrameCrypto(mock_session_decrypt)

        with pytest.raises(ValueError, match="must not contain padding"):
            crypto.decrypt("YWJj=", "AAAA")
