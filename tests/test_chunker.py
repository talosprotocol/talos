"""
Tests for data chunker module.

These tests cover:
- Chunk dataclass
- DataChunker class
- ReassemblyBuffer class
- ChunkReassembler class
"""

import pytest
from src.engine.chunker import (
    Chunk,
    DataChunker,
    ReassemblyBuffer,
    ChunkReassembler,
    CHUNK_SIZE_TEXT,
    CHUNK_SIZE_AUDIO,
    CHUNK_SIZE_VIDEO,
)


class TestChunk:
    """Tests for Chunk dataclass."""

    def test_chunk_creation(self):
        """Create a chunk."""
        chunk = Chunk(
            stream_id="stream1",
            sequence=0,
            total=3,
            data=b"Hello"
        )

        assert chunk.stream_id == "stream1"
        assert chunk.sequence == 0
        assert chunk.total == 3
        assert chunk.data == b"Hello"

    def test_hash_calculated(self):
        """Hash is calculated on creation."""
        chunk = Chunk(stream_id="stream", sequence=0, total=1, data=b"data")
        assert len(chunk.hash) == 64  # SHA256 hex

    def test_verify_valid(self):
        """Valid chunk passes verification."""
        chunk = Chunk(stream_id="stream", sequence=0, total=1, data=b"test data")
        assert chunk.verify() is True

    def test_verify_tampered(self):
        """Tampered chunk fails verification."""
        chunk = Chunk(stream_id="stream", sequence=0, total=1, data=b"test data")
        chunk.hash = "invalid"
        assert chunk.verify() is False

    def test_to_chunk_info(self):
        """Convert to ChunkInfo."""
        chunk = Chunk(stream_id="stream", sequence=1, total=5, data=b"data")
        info = chunk.to_chunk_info()

        assert info.sequence == 1
        assert info.total == 5
        assert info.stream_id == "stream"
        assert info.hash == chunk.hash


class TestDataChunker:
    """Tests for DataChunker class."""

    def test_default_chunk_size(self):
        """Default chunk size is text size."""
        chunker = DataChunker()
        assert chunker.chunk_size == CHUNK_SIZE_TEXT

    def test_custom_chunk_size(self):
        """Custom chunk size."""
        chunker = DataChunker(chunk_size=1024)
        assert chunker.chunk_size == 1024

    def test_chunk_small_data(self):
        """Chunking data smaller than chunk size."""
        chunker = DataChunker(chunk_size=100)
        data = b"small data"

        chunks = chunker.chunk(data)

        assert len(chunks) == 1
        assert chunks[0].data == data
        assert chunks[0].sequence == 0
        assert chunks[0].total == 1

    def test_chunk_exact_size(self):
        """Chunking data exactly chunk size."""
        chunker = DataChunker(chunk_size=10)
        data = b"1234567890"

        chunks = chunker.chunk(data)

        assert len(chunks) == 1
        assert chunks[0].data == data

    def test_chunk_multiple(self):
        """Chunking data into multiple chunks."""
        chunker = DataChunker(chunk_size=5)
        data = b"Hello World!"  # 12 bytes

        chunks = chunker.chunk(data)

        assert len(chunks) == 3
        assert chunks[0].data == b"Hello"
        assert chunks[1].data == b" Worl"
        assert chunks[2].data == b"d!"

        for i, chunk in enumerate(chunks):
            assert chunk.sequence == i
            assert chunk.total == 3

    def test_chunk_custom_stream_id(self):
        """Custom stream ID."""
        chunker = DataChunker(chunk_size=100)
        chunks = chunker.chunk(b"data", stream_id="my-stream")

        assert chunks[0].stream_id == "my-stream"

    def test_chunk_generated_stream_id(self):
        """Generated stream ID when not provided."""
        chunker = DataChunker(chunk_size=100)
        chunks = chunker.chunk(b"data")

        assert len(chunks[0].stream_id) > 0

    def test_chunk_iter(self):
        """Iterate over chunks."""
        chunker = DataChunker(chunk_size=5)
        data = b"Hello World!"

        chunks = list(chunker.chunk_iter(data))

        assert len(chunks) == 3
        assert chunks[0].data == b"Hello"

    def test_chunk_iter_custom_id(self):
        """Chunk iterator with custom ID."""
        chunker = DataChunker(chunk_size=100)
        chunks = list(chunker.chunk_iter(b"data", stream_id="iter-stream"))

        assert chunks[0].stream_id == "iter-stream"


class TestReassemblyBuffer:
    """Tests for ReassemblyBuffer class."""

    def test_add_chunk(self):
        """Add chunk to buffer."""
        buffer = ReassemblyBuffer(stream_id="stream", total=2)
        chunk = Chunk(stream_id="stream", sequence=0, total=2, data=b"data")

        result = buffer.add_chunk(chunk)

        assert result is True
        assert 0 in buffer.chunks

    def test_add_duplicate_chunk(self):
        """Duplicate chunk returns False."""
        buffer = ReassemblyBuffer(stream_id="stream", total=2)
        chunk = Chunk(stream_id="stream", sequence=0, total=2, data=b"data")

        buffer.add_chunk(chunk)
        result = buffer.add_chunk(chunk)

        assert result is False

    def test_add_wrong_stream(self):
        """Wrong stream ID raises error."""
        buffer = ReassemblyBuffer(stream_id="stream1", total=2)
        chunk = Chunk(stream_id="stream2", sequence=0, total=2, data=b"data")

        with pytest.raises(ValueError, match="mismatch"):
            buffer.add_chunk(chunk)

    def test_is_complete(self):
        """Check completion status."""
        buffer = ReassemblyBuffer(stream_id="stream", total=2)

        assert buffer.is_complete is False

        buffer.add_chunk(Chunk(stream_id="stream", sequence=0, total=2, data=b"a"))
        assert buffer.is_complete is False

        buffer.add_chunk(Chunk(stream_id="stream", sequence=1, total=2, data=b"b"))
        assert buffer.is_complete is True

    def test_progress(self):
        """Check progress calculation."""
        buffer = ReassemblyBuffer(stream_id="stream", total=4)

        assert buffer.progress == 0.0

        buffer.add_chunk(Chunk(stream_id="stream", sequence=0, total=4, data=b"a"))
        assert buffer.progress == 0.25

        buffer.add_chunk(Chunk(stream_id="stream", sequence=1, total=4, data=b"b"))
        assert buffer.progress == 0.5

    def test_missing(self):
        """Get missing chunks."""
        buffer = ReassemblyBuffer(stream_id="stream", total=3)

        assert buffer.missing == [0, 1, 2]

        buffer.add_chunk(Chunk(stream_id="stream", sequence=1, total=3, data=b"b"))
        assert buffer.missing == [0, 2]

    def test_reassemble(self):
        """Reassemble complete buffer."""
        buffer = ReassemblyBuffer(stream_id="stream", total=3)
        buffer.add_chunk(Chunk(stream_id="stream", sequence=0, total=3, data=b"Hello"))
        buffer.add_chunk(Chunk(stream_id="stream", sequence=1, total=3, data=b" "))
        buffer.add_chunk(Chunk(stream_id="stream", sequence=2, total=3, data=b"World"))

        data = buffer.reassemble()

        assert data == b"Hello World"

    def test_reassemble_incomplete(self):
        """Reassemble incomplete buffer raises error."""
        buffer = ReassemblyBuffer(stream_id="stream", total=2)
        buffer.add_chunk(Chunk(stream_id="stream", sequence=0, total=2, data=b"a"))

        with pytest.raises(ValueError, match="Missing"):
            buffer.reassemble()


class TestChunkReassembler:
    """Tests for ChunkReassembler class."""

    def test_single_chunk_stream(self):
        """Single chunk returns data immediately."""
        reassembler = ChunkReassembler()
        chunk = Chunk(stream_id="stream", sequence=0, total=1, data=b"complete")

        result = reassembler.add_chunk(chunk)

        assert result == b"complete"

    def test_multi_chunk_stream(self):
        """Multi-chunk stream returns on completion."""
        reassembler = ChunkReassembler()

        result1 = reassembler.add_chunk(Chunk(stream_id="s", sequence=0, total=2, data=b"Hello"))
        assert result1 is None

        result2 = reassembler.add_chunk(Chunk(stream_id="s", sequence=1, total=2, data=b"World"))
        assert result2 == b"HelloWorld"

    def test_out_of_order(self):
        """Handle out-of-order chunks."""
        reassembler = ChunkReassembler()

        reassembler.add_chunk(Chunk(stream_id="s", sequence=2, total=3, data=b"C"))
        reassembler.add_chunk(Chunk(stream_id="s", sequence=0, total=3, data=b"A"))
        result = reassembler.add_chunk(Chunk(stream_id="s", sequence=1, total=3, data=b"B"))

        assert result == b"ABC"

    def test_multiple_streams(self):
        """Handle multiple concurrent streams."""
        reassembler = ChunkReassembler()

        reassembler.add_chunk(Chunk(stream_id="s1", sequence=0, total=2, data=b"A"))
        reassembler.add_chunk(Chunk(stream_id="s2", sequence=0, total=2, data=b"X"))

        assert len(reassembler.active_streams) == 2

        r1 = reassembler.add_chunk(Chunk(stream_id="s1", sequence=1, total=2, data=b"B"))
        r2 = reassembler.add_chunk(Chunk(stream_id="s2", sequence=1, total=2, data=b"Y"))

        assert r1 == b"AB"
        assert r2 == b"XY"

    def test_get_progress(self):
        """Get stream progress."""
        reassembler = ChunkReassembler()
        reassembler.add_chunk(Chunk(stream_id="s", sequence=0, total=4, data=b"a"))

        progress = reassembler.get_progress("s")
        assert progress == 0.25

    def test_get_progress_unknown(self):
        """Get progress for unknown stream."""
        reassembler = ChunkReassembler()
        assert reassembler.get_progress("unknown") is None

    def test_get_missing(self):
        """Get missing chunks."""
        reassembler = ChunkReassembler()
        reassembler.add_chunk(Chunk(stream_id="s", sequence=1, total=3, data=b"b"))

        missing = reassembler.get_missing("s")
        assert missing == [0, 2]

    def test_get_missing_unknown(self):
        """Get missing for unknown stream."""
        reassembler = ChunkReassembler()
        assert reassembler.get_missing("unknown") is None

    def test_discard(self):
        """Discard incomplete stream."""
        reassembler = ChunkReassembler()
        reassembler.add_chunk(Chunk(stream_id="s", sequence=0, total=2, data=b"a"))

        result = reassembler.discard("s")

        assert result is True
        assert "s" not in reassembler.active_streams

    def test_discard_unknown(self):
        """Discard unknown stream."""
        reassembler = ChunkReassembler()
        result = reassembler.discard("unknown")
        assert result is False

    def test_active_streams(self):
        """Get active stream list."""
        reassembler = ChunkReassembler()

        assert reassembler.active_streams == []

        reassembler.add_chunk(Chunk(stream_id="s1", sequence=0, total=2, data=b"a"))
        reassembler.add_chunk(Chunk(stream_id="s2", sequence=0, total=2, data=b"b"))

        assert set(reassembler.active_streams) == {"s1", "s2"}


class TestChunkSizeConstants:
    """Tests for chunk size constants."""

    def test_text_chunk_size(self):
        """Text chunk size is 64KB."""
        assert CHUNK_SIZE_TEXT == 64 * 1024

    def test_audio_chunk_size(self):
        """Audio chunk size is 1MB."""
        assert CHUNK_SIZE_AUDIO == 1 * 1024 * 1024

    def test_video_chunk_size(self):
        """Video chunk size is 4MB."""
        assert CHUNK_SIZE_VIDEO == 4 * 1024 * 1024
