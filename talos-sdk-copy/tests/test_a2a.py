"""Unit tests for A2A module."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
import threading

from talos_sdk.a2a.errors import (
    A2ATransportError,
    A2ASessionNotFoundError,
    A2ASessionStateInvalidError,
    A2AFrameReplayError,
    A2AFrameDigestMismatchError,
    A2ACryptoNotConfiguredError,
    raise_mapped_error,
)
from talos_sdk.a2a.models import (
    EncryptedFrame,
    SessionResponse,
    FrameSendResponse,
    FrameListResponse,
    ErrorResponse,
)
from talos_sdk.a2a.sequence_tracker import (
    SequenceTracker,
    InMemorySequenceStorage,
    _DEFAULT_STORAGE,
)


# === Error Mapping Tests ===

class TestErrorMapping:
    def test_session_not_found(self):
        err = ErrorResponse(error_code="A2A_SESSION_NOT_FOUND", message="Not found")
        with pytest.raises(A2ASessionNotFoundError):
            raise_mapped_error(err)

    def test_session_state_invalid_with_details(self):
        err = ErrorResponse(
            error_code="A2A_SESSION_STATE_INVALID",
            message="Invalid",
            details={"current_state": "closed"},
        )
        with pytest.raises(A2ASessionStateInvalidError) as exc:
            raise_mapped_error(err)
        assert exc.value.current_state == "closed"

    def test_frame_replay_with_seq(self):
        err = ErrorResponse(
            error_code="A2A_FRAME_REPLAY_DETECTED",
            message="Replay",
            details={"sender_seq": 42},
        )
        with pytest.raises(A2AFrameReplayError) as exc:
            raise_mapped_error(err)
        assert exc.value.sender_seq == 42

    def test_digest_mismatch(self):
        err = ErrorResponse(error_code="A2A_FRAME_DIGEST_MISMATCH", message="Mismatch")
        with pytest.raises(A2AFrameDigestMismatchError):
            raise_mapped_error(err)

    def test_unknown_error_falls_back(self):
        err = ErrorResponse(error_code="UNKNOWN_ERROR", message="Something went wrong")
        with pytest.raises(A2ATransportError) as exc:
            raise_mapped_error(err, status_code=500)
        assert exc.value.status_code == 500


# === Model Validation Tests ===

class TestModelValidation:
    def test_valid_encrypted_frame(self):
        frame = EncryptedFrame(
            session_id="sess-1",
            sender_id="alice",
            sender_seq=0,
            header_b64u="aGVsbG8",
            ciphertext_b64u="d29ybGQ",
            frame_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            ciphertext_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        assert frame.session_id == "sess-1"

    def test_digest_rejects_uppercase(self):
        with pytest.raises(ValueError, match="lowercase hex"):
            EncryptedFrame(
                session_id="sess-1",
                sender_id="alice",
                sender_seq=0,
                header_b64u="aGVsbG8",
                ciphertext_b64u="d29ybGQ",
                frame_digest="E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
                ciphertext_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )

    def test_digest_rejects_short(self):
        with pytest.raises(ValueError, match="64 chars"):
            EncryptedFrame(
                session_id="sess-1",
                sender_id="alice",
                sender_seq=0,
                header_b64u="aGVsbG8",
                ciphertext_b64u="d29ybGQ",
                frame_digest="abc123",
                ciphertext_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )

    def test_b64url_rejects_padding(self):
        with pytest.raises(ValueError, match="base64url without padding"):
            EncryptedFrame(
                session_id="sess-1",
                sender_id="alice",
                sender_seq=0,
                header_b64u="aGVsbG8=",  # Padded!
                ciphertext_b64u="d29ybGQ",
                frame_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ciphertext_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )

    def test_b64url_rejects_empty(self):
        with pytest.raises(ValueError, match="non-empty"):
            EncryptedFrame(
                session_id="sess-1",
                sender_id="alice",
                sender_seq=0,
                header_b64u="",
                ciphertext_b64u="d29ybGQ",
                frame_digest="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                ciphertext_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            )


# === Sequence Tracker Tests ===

class TestSequenceTracker:
    def test_reserve_increments(self):
        storage = InMemorySequenceStorage()
        tracker = SequenceTracker("sess-1", "alice", storage)
        
        assert tracker.reserve() == 0
        assert tracker.reserve() == 1
        assert tracker.reserve() == 2
        assert tracker.current() == 3

    def test_reserve_persists(self):
        storage = InMemorySequenceStorage()
        
        # First tracker reserves some
        tracker1 = SequenceTracker("sess-1", "alice", storage)
        tracker1.reserve()
        tracker1.reserve()
        
        # Second tracker loads from storage
        tracker2 = SequenceTracker("sess-1", "alice", storage)
        assert tracker2.current() == 2
        assert tracker2.reserve() == 2

    def test_default_storage_is_global(self):
        # Two trackers with no storage should share the global default
        tracker1 = SequenceTracker("global-test", "alice")
        tracker2 = SequenceTracker("global-test", "alice")
        
        # They share the same storage, so seq is shared
        tracker1.reserve()
        # tracker2 was constructed before reserve, so it has a cached value
        # New tracker should see the persisted value
        tracker3 = SequenceTracker.load("global-test", "alice")
        assert tracker3.current() == 1

    def test_thread_safety(self):
        storage = InMemorySequenceStorage()
        tracker = SequenceTracker("thread-test", "alice", storage)
        
        sequences = []
        
        def reserve_many():
            for _ in range(100):
                seq = tracker.reserve()
                sequences.append(seq)
        
        threads = [threading.Thread(target=reserve_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All sequences should be unique
        assert len(sequences) == 400
        assert len(set(sequences)) == 400


# === Session Client Tests ===

class TestSessionClient:
    @pytest.mark.asyncio
    async def test_crypto_not_configured_send(self):
        from talos_sdk.a2a.session_client import A2ASessionClient
        
        transport = MagicMock()
        client = A2ASessionClient(
            transport=transport,
            session_id="sess-1",
            sender_id="alice",
            peer_id="bob",
            is_initiator=True,
            crypto=None,
        )
        
        with pytest.raises(A2ACryptoNotConfiguredError):
            await client.send_message(b"hello")

    @pytest.mark.asyncio
    async def test_crypto_not_configured_receive(self):
        from talos_sdk.a2a.session_client import A2ASessionClient
        
        transport = MagicMock()
        client = A2ASessionClient(
            transport=transport,
            session_id="sess-1",
            sender_id="alice",
            peer_id="bob",
            is_initiator=True,
            crypto=None,
        )
        
        with pytest.raises(A2ACryptoNotConfiguredError):
            await client.receive_messages()
