"""
Tests for media handling module.
"""

import hashlib
import tempfile
from pathlib import Path

import pytest

from src.engine.media import (
    MediaFile,
    MediaInfo,
    MediaType,
    MediaTransfer,
    TransferManager,
    TransferStatus,
    detect_mime_type,
    get_media_type,
    get_chunk_size,
    format_file_size,
    MediaError,
)


class TestMimeTypeDetection:
    """Tests for MIME type detection."""

    def test_detect_image_types(self):
        assert detect_mime_type(Path("test.jpg")) == "image/jpeg"
        assert detect_mime_type(Path("test.png")) == "image/png"
        assert detect_mime_type(Path("test.gif")) == "image/gif"
        assert detect_mime_type(Path("test.webp")) == "image/webp"

    def test_detect_audio_types(self):
        assert detect_mime_type(Path("test.mp3")) == "audio/mpeg"
        assert detect_mime_type(Path("test.wav")) in ("audio/wav", "audio/x-wav")
        assert detect_mime_type(Path("test.ogg")) in ("audio/ogg", "application/ogg")

    def test_detect_video_types(self):
        assert detect_mime_type(Path("test.mp4")) == "video/mp4"
        assert detect_mime_type(Path("test.webm")) == "video/webm"

    def test_detect_document_types(self):
        assert detect_mime_type(Path("test.pdf")) == "application/pdf"
        assert detect_mime_type(Path("test.txt")) == "text/plain"
        assert detect_mime_type(Path("test.json")) == "application/json"

    def test_unknown_type(self):
        # Use a truly unknown extension
        result = detect_mime_type(Path("test.unknownext123"))
        assert result == "application/octet-stream"


class TestMediaType:
    """Tests for MediaType mapping."""

    def test_image_mapping(self):
        assert get_media_type("image/jpeg") == MediaType.IMAGE
        assert get_media_type("image/png") == MediaType.IMAGE

    def test_audio_mapping(self):
        assert get_media_type("audio/mpeg") == MediaType.AUDIO
        assert get_media_type("audio/mp3") == MediaType.AUDIO

    def test_video_mapping(self):
        assert get_media_type("video/mp4") == MediaType.VIDEO
        assert get_media_type("video/webm") == MediaType.VIDEO

    def test_document_mapping(self):
        assert get_media_type("application/pdf") == MediaType.DOCUMENT
        assert get_media_type("text/plain") == MediaType.DOCUMENT

    def test_unknown_mapping(self):
        assert get_media_type("unknown/type") == MediaType.UNKNOWN


class TestChunkSizes:
    """Tests for chunk size configuration."""

    def test_different_sizes_per_type(self):
        image_size = get_chunk_size(MediaType.IMAGE)
        video_size = get_chunk_size(MediaType.VIDEO)

        # Video chunks should be larger than image chunks
        assert video_size > image_size

    def test_unknown_type_has_default(self):
        size = get_chunk_size(MediaType.UNKNOWN)
        assert size > 0


class TestFormatFileSize:
    """Tests for file size formatting."""

    def test_bytes(self):
        assert format_file_size(500) == "500 B"

    def test_kilobytes(self):
        assert format_file_size(1024) == "1 KB"
        assert format_file_size(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_file_size(1024 * 1024) == "1 MB"

    def test_gigabytes(self):
        assert format_file_size(1024 * 1024 * 1024) == "1 GB"


class TestMediaFile:
    """Tests for MediaFile class."""

    def test_create_from_path(self):
        """Test creating MediaFile from a real file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Hello, World!")
            f.flush()

            media_file = MediaFile.from_path(f.name)

            assert media_file.filename.endswith(".txt")
            assert media_file.size == 13
            assert media_file.media_type == MediaType.DOCUMENT
            assert media_file.mime_type == "text/plain"
            assert len(media_file.file_hash) == 64  # SHA-256 hex

            # Cleanup
            Path(f.name).unlink()

    def test_file_not_found(self):
        """Test that missing file raises error."""
        with pytest.raises(MediaError):
            MediaFile.from_path("/nonexistent/file.txt")

    def test_read_chunks(self):
        """Test reading file in chunks."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            test_data = b"A" * 1000
            f.write(test_data)
            f.flush()

            media_file = MediaFile.from_path(f.name)

            # Read in small chunks
            chunks = list(media_file.read_chunks(chunk_size=100))
            assert len(chunks) == 10
            assert all(len(c) == 100 for c in chunks)

            # Verify reassembly
            reassembled = b"".join(chunks)
            assert reassembled == test_data

            Path(f.name).unlink()

    def test_to_media_info(self):
        """Test converting to MediaInfo."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test content")
            f.flush()

            media_file = MediaFile.from_path(f.name)
            info = media_file.to_media_info()

            assert info.filename == media_file.filename
            assert info.size == media_file.size
            assert info.file_hash == media_file.file_hash
            assert info.chunk_count >= 1

            Path(f.name).unlink()


class TestMediaInfo:
    """Tests for MediaInfo class."""

    def test_serialization(self):
        """Test MediaInfo to_dict and from_dict."""
        info = MediaInfo(
            filename="test.jpg",
            mime_type="image/jpeg",
            media_type=MediaType.IMAGE,
            size=1024,
            file_hash="abc123",
            chunk_count=4,
            chunk_size=256
        )

        data = info.to_dict()
        restored = MediaInfo.from_dict(data)

        assert restored.filename == info.filename
        assert restored.mime_type == info.mime_type
        assert restored.media_type == info.media_type
        assert restored.size == info.size
        assert restored.file_hash == info.file_hash


class TestMediaTransfer:
    """Tests for MediaTransfer class."""

    def test_transfer_lifecycle(self):
        """Test transfer start, progress, complete lifecycle."""
        info = MediaInfo(
            filename="test.jpg",
            mime_type="image/jpeg",
            media_type=MediaType.IMAGE,
            size=1024,
            file_hash="",  # Will be set properly
            chunk_count=4,
            chunk_size=256
        )

        transfer = MediaTransfer(
            id="test-transfer",
            media_info=info,
            peer_id="peer123",
            direction="receive"
        )

        assert transfer.status == TransferStatus.PENDING
        assert transfer.progress == 0.0

        transfer.start()
        assert transfer.status == TransferStatus.IN_PROGRESS

        # Simulate receiving chunks
        transfer.add_chunk(b"A" * 256)
        assert transfer.progress == 0.25

        transfer.add_chunk(b"B" * 256)
        assert transfer.progress == 0.5

        transfer.add_chunk(b"C" * 256)
        transfer.add_chunk(b"D" * 256)
        assert transfer.progress == 1.0
        assert transfer.is_complete

    def test_transfer_hash_verification(self):
        """Test hash verification after transfer."""
        test_data = b"Hello, World!"
        expected_hash = hashlib.sha256(test_data).hexdigest()

        info = MediaInfo(
            filename="test.txt",
            mime_type="text/plain",
            media_type=MediaType.DOCUMENT,
            size=len(test_data),
            file_hash=expected_hash,
            chunk_count=1,
            chunk_size=1024
        )

        transfer = MediaTransfer(
            id="test-transfer",
            media_info=info,
            peer_id="peer123",
            direction="receive"
        )

        transfer.add_chunk(test_data)
        assert transfer.verify_hash() is True

    def test_transfer_hash_verification_fails(self):
        """Test that wrong hash fails verification."""
        info = MediaInfo(
            filename="test.txt",
            mime_type="text/plain",
            media_type=MediaType.DOCUMENT,
            size=13,
            file_hash="wrong_hash",
            chunk_count=1,
            chunk_size=1024
        )

        transfer = MediaTransfer(
            id="test-transfer",
            media_info=info,
            peer_id="peer123",
            direction="receive"
        )

        transfer.add_chunk(b"Hello, World!")
        assert transfer.verify_hash() is False


class TestTransferManager:
    """Tests for TransferManager class."""

    def test_create_send_transfer(self):
        """Test creating a send transfer."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test content")
            f.flush()

            manager = TransferManager()
            media_file = MediaFile.from_path(f.name)

            transfer = manager.create_send_transfer(
                transfer_id="test-123",
                media_file=media_file,
                peer_id="peer456"
            )

            assert transfer.id == "test-123"
            assert transfer.direction == "send"
            assert len(manager) == 1

            Path(f.name).unlink()

    def test_get_active_transfers(self):
        """Test getting active transfers."""
        manager = TransferManager()

        info = MediaInfo(
            filename="test.txt",
            mime_type="text/plain",
            media_type=MediaType.DOCUMENT,
            size=100,
            file_hash="abc",
            chunk_count=1,
            chunk_size=100
        )

        # Create two transfers
        t1 = manager.create_receive_transfer("t1", info, "peer1")
        manager.create_receive_transfer("t2", info, "peer2")

        # Start one
        t1.start()

        active = manager.get_active_transfers()
        assert len(active) == 1
        assert active[0].id == "t1"

    def test_max_concurrent_check(self):
        """Test max concurrent transfers check."""
        manager = TransferManager(max_concurrent=2)

        info = MediaInfo(
            filename="test.txt",
            mime_type="text/plain",
            media_type=MediaType.DOCUMENT,
            size=100,
            file_hash="abc",
            chunk_count=1,
            chunk_size=100
        )

        t1 = manager.create_receive_transfer("t1", info, "peer1")
        t2 = manager.create_receive_transfer("t2", info, "peer2")

        t1.start()
        assert manager.can_start_transfer is True

        t2.start()
        assert manager.can_start_transfer is False
