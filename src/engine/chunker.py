"""
Data chunker for handling large payloads.

This module provides:
- DataChunker: Split data into chunks for transmission
- ChunkReassembler: Reassemble chunks back into original data
- Designed to support future audio/video streaming
"""

import hashlib
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Iterator

from ..core.message import ChunkInfo


# Default chunk sizes for different content types
CHUNK_SIZE_TEXT = 64 * 1024  # 64KB for text
CHUNK_SIZE_AUDIO = 1 * 1024 * 1024  # 1MB for audio
CHUNK_SIZE_VIDEO = 4 * 1024 * 1024  # 4MB for video


class Chunk(BaseModel):
    """A single chunk of data."""

    stream_id: str
    sequence: int
    total: int
    data: bytes
    hash: str = ""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        if not self.hash:
            self.hash = hashlib.sha256(self.data).hexdigest()

    def to_chunk_info(self) -> ChunkInfo:
        """Convert to ChunkInfo for message payload."""
        return ChunkInfo(
            sequence=self.sequence,
            total=self.total,
            stream_id=self.stream_id,
            hash=self.hash
        )

    def verify(self) -> bool:
        """Verify chunk integrity."""
        return hashlib.sha256(self.data).hexdigest() == self.hash


class DataChunker:
    """
    Splits data into chunks for transmission.
    
    Supports different chunk sizes for different content types,
    making it suitable for text, audio, and video data.
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE_TEXT) -> None:
        """
        Initialize chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in bytes
        """
        self.chunk_size = chunk_size

    def chunk(self, data: bytes, stream_id: Optional[str] = None) -> list[Chunk]:
        """
        Split data into chunks.
        
        Args:
            data: Data to split
            stream_id: Optional stream ID (generated if not provided)
            
        Returns:
            List of Chunk objects
        """
        if stream_id is None:
            stream_id = str(uuid.uuid4())

        chunks = []
        total = (len(data) + self.chunk_size - 1) // self.chunk_size

        for i in range(total):
            start = i * self.chunk_size
            end = min(start + self.chunk_size, len(data))

            chunk = Chunk(
                stream_id=stream_id,
                sequence=i,
                total=total,
                data=data[start:end]
            )
            chunks.append(chunk)

        return chunks

    def chunk_iter(
        self,
        data: bytes,
        stream_id: Optional[str] = None
    ) -> Iterator[Chunk]:
        """
        Iterate over chunks (memory efficient for large data).
        
        Args:
            data: Data to split
            stream_id: Optional stream ID
            
        Yields:
            Chunk objects
        """
        if stream_id is None:
            stream_id = str(uuid.uuid4())

        total = (len(data) + self.chunk_size - 1) // self.chunk_size

        for i in range(total):
            start = i * self.chunk_size
            end = min(start + self.chunk_size, len(data))

            yield Chunk(
                stream_id=stream_id,
                sequence=i,
                total=total,
                data=data[start:end]
            )


class ReassemblyBuffer(BaseModel):
    """Buffer for reassembling a single stream."""

    stream_id: str
    total: int
    chunks: dict[int, bytes] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_chunk(self, chunk: Chunk) -> bool:
        """
        Add a chunk to the buffer.
        
        Args:
            chunk: Chunk to add
            
        Returns:
            True if chunk was added, False if already present
        """
        if chunk.stream_id != self.stream_id:
            raise ValueError("Chunk stream_id mismatch")

        if chunk.sequence in self.chunks:
            return False

        if not chunk.verify():
            raise ValueError("Chunk verification failed")

        self.chunks[chunk.sequence] = chunk.data
        return True

    @property
    def is_complete(self) -> bool:
        """Check if all chunks have been received."""
        return len(self.chunks) == self.total

    @property
    def progress(self) -> float:
        """Get reassembly progress (0.0 to 1.0)."""
        return len(self.chunks) / self.total if self.total > 0 else 0.0

    @property
    def missing(self) -> list[int]:
        """Get list of missing chunk sequence numbers."""
        return [i for i in range(self.total) if i not in self.chunks]

    def reassemble(self) -> bytes:
        """
        Reassemble chunks into original data.
        
        Returns:
            Original data
            
        Raises:
            ValueError: If not all chunks are present
        """
        if not self.is_complete:
            raise ValueError(f"Missing chunks: {self.missing}")

        parts = []
        for i in range(self.total):
            parts.append(self.chunks[i])

        return b"".join(parts)


class ChunkReassembler:
    """
    Reassembles chunks back into original data.
    
    Manages multiple concurrent streams and handles
    out-of-order chunk arrival.
    """

    def __init__(self, timeout: float = 60.0) -> None:
        """
        Initialize reassembler.
        
        Args:
            timeout: Time in seconds before incomplete streams are discarded
        """
        self._buffers: dict[str, ReassemblyBuffer] = {}
        self.timeout = timeout

    def add_chunk(self, chunk: Chunk) -> Optional[bytes]:
        """
        Add a chunk and return completed data if stream is complete.
        
        Args:
            chunk: Chunk to add
            
        Returns:
            Reassembled data if complete, None otherwise
        """
        stream_id = chunk.stream_id

        # Create buffer if needed
        if stream_id not in self._buffers:
            self._buffers[stream_id] = ReassemblyBuffer(
                stream_id=stream_id,
                total=chunk.total
            )

        buffer = self._buffers[stream_id]
        buffer.add_chunk(chunk)

        # Check if complete
        if buffer.is_complete:
            data = buffer.reassemble()
            del self._buffers[stream_id]
            return data

        return None

    def get_progress(self, stream_id: str) -> Optional[float]:
        """Get progress for a stream."""
        buffer = self._buffers.get(stream_id)
        if buffer:
            return buffer.progress
        return None

    def get_missing(self, stream_id: str) -> Optional[list[int]]:
        """Get missing chunk sequences for a stream."""
        buffer = self._buffers.get(stream_id)
        if buffer:
            return buffer.missing
        return None

    def discard(self, stream_id: str) -> bool:
        """Discard an incomplete stream."""
        if stream_id in self._buffers:
            del self._buffers[stream_id]
            return True
        return False

    @property
    def active_streams(self) -> list[str]:
        """Get list of active stream IDs."""
        return list(self._buffers.keys())
