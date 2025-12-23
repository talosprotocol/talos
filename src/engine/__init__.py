"""
Transmission engine components for data chunking, streaming, and media transfer.

This package provides:
- TransmissionEngine: Main interface for sending/receiving data
- DataChunker/ChunkReassembler: Large data handling
- Media handlers: File transfer with progress tracking
"""

from .engine import (
    TransmissionEngine,
    ReceivedMessage,
    ReceivedMedia,
    ContentType,
    MessageCallback,
    FileCallback,
)

from .chunker import (
    DataChunker,
    ChunkReassembler,
    Chunk,
    CHUNK_SIZE_TEXT,
    CHUNK_SIZE_AUDIO,
    CHUNK_SIZE_VIDEO,
)

from .media import (
    MediaFile,
    MediaInfo,
    MediaType,
    MediaTransfer,
    TransferManager,
    TransferStatus,
    MediaError,
    FileTooLargeError,
    HashVerificationError,
    get_chunk_size,
    get_media_type,
    format_file_size,
)

__all__ = [
    # Engine
    "TransmissionEngine",
    "ReceivedMessage",
    "ReceivedMedia",
    "ContentType",
    "MessageCallback",
    "FileCallback",
    # Chunker
    "DataChunker",
    "ChunkReassembler",
    "Chunk",
    "CHUNK_SIZE_TEXT",
    "CHUNK_SIZE_AUDIO",
    "CHUNK_SIZE_VIDEO",
    # Media
    "MediaFile",
    "MediaInfo",
    "MediaType",
    "MediaTransfer",
    "TransferManager",
    "TransferStatus",
    "MediaError",
    "FileTooLargeError",
    "HashVerificationError",
    "get_chunk_size",
    "get_media_type",
    "format_file_size",
]
