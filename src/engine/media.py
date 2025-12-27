"""
Media handling for the blockchain messaging protocol.

This module provides production-ready support for:
- File type detection and validation
- Media file metadata management
- Transfer state management
- Progress tracking

Supports images, audio, video, and document files with
automatic MIME type detection and secure hash verification.
"""

import hashlib
import logging
import mimetypes
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Iterator

logger = logging.getLogger(__name__)

# Initialize mimetypes
mimetypes.init()


class MediaType(Enum):
    """Supported media types for file transfer."""

    IMAGE = auto()     # jpg, png, gif, webp, svg
    AUDIO = auto()     # mp3, wav, ogg, m4a, flac
    VIDEO = auto()     # mp4, webm, mov, avi, mkv
    DOCUMENT = auto()  # pdf, doc, docx, txt, md
    ARCHIVE = auto()   # zip, tar, gz, 7z
    UNKNOWN = auto()   # Unrecognized types


class TransferStatus(Enum):
    """Status of a file transfer."""

    PENDING = auto()     # Not yet started
    IN_PROGRESS = auto() # Transfer in progress
    COMPLETED = auto()   # Successfully completed
    FAILED = auto()      # Transfer failed
    CANCELLED = auto()   # Cancelled by user


# MIME type to MediaType mapping
MIME_TYPE_MAP: dict[str, MediaType] = {
    # Images
    "image/jpeg": MediaType.IMAGE,
    "image/png": MediaType.IMAGE,
    "image/gif": MediaType.IMAGE,
    "image/webp": MediaType.IMAGE,
    "image/svg+xml": MediaType.IMAGE,
    "image/bmp": MediaType.IMAGE,
    "image/tiff": MediaType.IMAGE,

    # Audio
    "audio/mpeg": MediaType.AUDIO,
    "audio/mp3": MediaType.AUDIO,
    "audio/wav": MediaType.AUDIO,
    "audio/ogg": MediaType.AUDIO,
    "audio/aac": MediaType.AUDIO,
    "audio/flac": MediaType.AUDIO,
    "audio/x-m4a": MediaType.AUDIO,
    "audio/mp4": MediaType.AUDIO,

    # Video
    "video/mp4": MediaType.VIDEO,
    "video/webm": MediaType.VIDEO,
    "video/quicktime": MediaType.VIDEO,
    "video/x-msvideo": MediaType.VIDEO,
    "video/x-matroska": MediaType.VIDEO,
    "video/mpeg": MediaType.VIDEO,

    # Documents
    "application/pdf": MediaType.DOCUMENT,
    "application/msword": MediaType.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": MediaType.DOCUMENT,
    "application/vnd.ms-excel": MediaType.DOCUMENT,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": MediaType.DOCUMENT,
    "text/plain": MediaType.DOCUMENT,
    "text/markdown": MediaType.DOCUMENT,
    "text/csv": MediaType.DOCUMENT,
    "application/json": MediaType.DOCUMENT,

    # Archives
    "application/zip": MediaType.ARCHIVE,
    "application/x-tar": MediaType.ARCHIVE,
    "application/gzip": MediaType.ARCHIVE,
    "application/x-7z-compressed": MediaType.ARCHIVE,
    "application/x-rar-compressed": MediaType.ARCHIVE,
}

# Optimal chunk sizes by media type (in bytes)
CHUNK_SIZES: dict[MediaType, int] = {
    MediaType.IMAGE: 256 * 1024,       # 256KB - balance between latency and throughput
    MediaType.AUDIO: 512 * 1024,       # 512KB - audio can be larger
    MediaType.VIDEO: 1024 * 1024,      # 1MB - video needs larger chunks
    MediaType.DOCUMENT: 256 * 1024,    # 256KB - documents are usually small
    MediaType.ARCHIVE: 512 * 1024,     # 512KB
    MediaType.UNKNOWN: 256 * 1024,     # 256KB default
}

# Maximum file sizes by media type (in bytes)
MAX_FILE_SIZES: dict[MediaType, int] = {
    MediaType.IMAGE: 50 * 1024 * 1024,      # 50MB
    MediaType.AUDIO: 200 * 1024 * 1024,     # 200MB
    MediaType.VIDEO: 2 * 1024 * 1024 * 1024, # 2GB
    MediaType.DOCUMENT: 100 * 1024 * 1024,   # 100MB
    MediaType.ARCHIVE: 500 * 1024 * 1024,    # 500MB
    MediaType.UNKNOWN: 50 * 1024 * 1024,     # 50MB default
}


class MediaError(Exception):
    """Base exception for media handling errors."""
    pass


class FileNotFoundError(MediaError):
    """File does not exist."""
    pass


class FileTooLargeError(MediaError):
    """File exceeds maximum allowed size."""
    pass


class UnsupportedMediaTypeError(MediaError):
    """Media type is not supported."""
    pass


class HashVerificationError(MediaError):
    """File hash verification failed."""
    pass


def detect_mime_type(file_path: Path) -> str:
    """
    Detect MIME type from file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string (e.g., 'image/jpeg')
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def get_media_type(mime_type: str) -> MediaType:
    """
    Get MediaType for a MIME type string.
    
    Args:
        mime_type: MIME type string
        
    Returns:
        Corresponding MediaType enum value
    """
    return MIME_TYPE_MAP.get(mime_type, MediaType.UNKNOWN)


def get_chunk_size(media_type: MediaType) -> int:
    """
    Get optimal chunk size for a media type.
    
    Args:
        media_type: The type of media
        
    Returns:
        Chunk size in bytes
    """
    return CHUNK_SIZES.get(media_type, CHUNK_SIZES[MediaType.UNKNOWN])


def get_max_file_size(media_type: MediaType) -> int:
    """
    Get maximum allowed file size for a media type.
    
    Args:
        media_type: The type of media
        
    Returns:
        Maximum file size in bytes
    """
    return MAX_FILE_SIZES.get(media_type, MAX_FILE_SIZES[MediaType.UNKNOWN])


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file using streaming to handle large files.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)
        
    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if size_bytes != int(size_bytes) else f"{int(size_bytes)} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


class MediaInfo(BaseModel):
    """
    Metadata for a media file transfer.
    
    Included in file message payloads to describe the file being transferred.
    """

    filename: str
    mime_type: str
    media_type: MediaType
    size: int
    file_hash: str  # SHA-256 of complete file
    chunk_count: int
    chunk_size: int

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer('media_type')
    def serialize_media_type(self, v: MediaType, _info):
        return v.name

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "filename": self.filename,
            "mime_type": self.mime_type,
            "media_type": self.media_type.name,
            "size": self.size,
            "file_hash": self.file_hash,
            "chunk_count": self.chunk_count,
            "chunk_size": self.chunk_size,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MediaInfo":
        """Create from dictionary."""
        return cls(
            filename=data["filename"],
            mime_type=data["mime_type"],
            media_type=MediaType[data["media_type"]],
            size=data["size"],
            file_hash=data["file_hash"],
            chunk_count=data["chunk_count"],
            chunk_size=data["chunk_size"],
        )

    @property
    def size_formatted(self) -> str:
        """Get human-readable file size."""
        return format_file_size(self.size)

    def __repr__(self) -> str:
        return f"MediaInfo({self.filename}, {self.mime_type}, {self.size_formatted})"


class MediaFile(BaseModel):
    """
    Represents a local media file ready for transfer.
    
    Wraps a file path with all necessary metadata for secure transfer.
    """

    path: Path
    filename: str
    mime_type: str
    media_type: MediaType
    size: int
    file_hash: str
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_path(cls, file_path: str | Path, validate: bool = True) -> "MediaFile":
        """
        Create MediaFile from a file path.
        
        Args:
            file_path: Path to the file
            validate: Whether to validate file exists and check size limits
            
        Returns:
            MediaFile instance
            
        Raises:
            FileNotFoundError: If file does not exist
            FileTooLargeError: If file exceeds size limit
        """
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise MediaError(f"Path is not a file: {path}")

        # Get file info
        size = path.stat().st_size
        mime_type = detect_mime_type(path)
        media_type = get_media_type(mime_type)

        # Validate size
        if validate:
            max_size = get_max_file_size(media_type)
            if size > max_size:
                raise FileTooLargeError(
                    f"File size ({format_file_size(size)}) exceeds maximum "
                    f"({format_file_size(max_size)}) for {media_type.name}"
                )

        # Calculate hash (this may take time for large files)
        logger.debug(f"Calculating hash for {path.name}...")
        file_hash = calculate_file_hash(path)

        return cls(
            path=path,
            filename=path.name,
            mime_type=mime_type,
            media_type=media_type,
            size=size,
            file_hash=file_hash,
        )

    def to_media_info(self) -> MediaInfo:
        """Convert to MediaInfo for transfer metadata."""
        chunk_size = get_chunk_size(self.media_type)
        chunk_count = (self.size + chunk_size - 1) // chunk_size

        return MediaInfo(
            filename=self.filename,
            mime_type=self.mime_type,
            media_type=self.media_type,
            size=self.size,
            file_hash=self.file_hash,
            chunk_count=chunk_count,
            chunk_size=chunk_size,
        )

    def read_chunks(self, chunk_size: Optional[int] = None) -> Iterator[bytes]:
        """
        Read file in chunks for streaming transfer.
        
        Args:
            chunk_size: Override chunk size (uses optimal size if not specified)
            
        Yields:
            File data chunks
        """
        if chunk_size is None:
            chunk_size = get_chunk_size(self.media_type)

        with open(self.path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @property
    def size_formatted(self) -> str:
        """Get human-readable file size."""
        return format_file_size(self.size)

    def __repr__(self) -> str:
        return f"MediaFile({self.filename}, {self.media_type.name}, {self.size_formatted})"


class MediaTransfer(BaseModel):
    """
    Tracks the state of an in-progress file transfer.
    
    Used for both sending and receiving files, tracking progress
    and enabling resume on failure.
    """

    id: str
    media_info: MediaInfo
    peer_id: str
    direction: str  # "send" or "receive"
    status: TransferStatus = TransferStatus.PENDING
    chunks_completed: int = 0
    bytes_transferred: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    data: bytes = Field(default=b"", repr=False)  # Accumulated data for receive

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def start(self) -> None:
        """Mark transfer as started."""
        self.status = TransferStatus.IN_PROGRESS
        self.started_at = datetime.now()
        logger.info(f"Transfer {self.id[:8]}... started: {self.media_info.filename}")

    def complete(self) -> None:
        """Mark transfer as completed."""
        self.status = TransferStatus.COMPLETED
        self.completed_at = datetime.now()
        logger.info(
            f"Transfer {self.id[:8]}... completed: {self.media_info.filename} "
            f"({self.media_info.size_formatted})"
        )

    def fail(self, error: str) -> None:
        """Mark transfer as failed."""
        self.status = TransferStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
        logger.error(f"Transfer {self.id[:8]}... failed: {error}")

    def cancel(self) -> None:
        """Cancel the transfer."""
        self.status = TransferStatus.CANCELLED
        self.completed_at = datetime.now()
        logger.info(f"Transfer {self.id[:8]}... cancelled")

    def add_chunk(self, chunk_data: bytes) -> None:
        """Add a received chunk."""
        self.data += chunk_data
        self.chunks_completed += 1
        self.bytes_transferred = len(self.data)

    @property
    def progress(self) -> float:
        """Get transfer progress (0.0 to 1.0)."""
        if self.media_info.chunk_count == 0:
            return 0.0
        return self.chunks_completed / self.media_info.chunk_count

    @property
    def progress_percent(self) -> int:
        """Get transfer progress as percentage."""
        return int(self.progress * 100)

    @property
    def is_complete(self) -> bool:
        """Check if all chunks have been transferred."""
        return self.chunks_completed >= self.media_info.chunk_count

    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def transfer_rate(self) -> Optional[float]:
        """Get transfer rate in bytes per second."""
        elapsed = self.elapsed_time
        if not elapsed or elapsed == 0:
            return None
        return self.bytes_transferred / elapsed

    @property
    def transfer_rate_formatted(self) -> str:
        """Get human-readable transfer rate."""
        rate = self.transfer_rate
        if rate is None:
            return "N/A"
        return f"{format_file_size(int(rate))}/s"

    def verify_hash(self) -> bool:
        """
        Verify the integrity of received data.
        
        Returns:
            True if hash matches, False otherwise
        """
        if not self.data:
            return False

        actual_hash = hashlib.sha256(self.data).hexdigest()
        return actual_hash == self.media_info.file_hash

    def __repr__(self) -> str:
        return (
            f"MediaTransfer({self.direction}, {self.media_info.filename}, "
            f"{self.status.name}, {self.progress_percent}%)"
        )


class TransferManager:
    """
    Manages multiple concurrent file transfers.
    
    Provides centralized tracking, progress monitoring, and cleanup
    of file transfers.
    """

    def __init__(self, max_concurrent: int = 5) -> None:
        """
        Initialize transfer manager.
        
        Args:
            max_concurrent: Maximum concurrent transfers per direction
        """
        self.max_concurrent = max_concurrent
        self._transfers: dict[str, MediaTransfer] = {}

    def create_send_transfer(
        self,
        transfer_id: str,
        media_file: MediaFile,
        peer_id: str
    ) -> MediaTransfer:
        """
        Create a new send transfer.
        
        Args:
            transfer_id: Unique transfer ID
            media_file: File to send
            peer_id: Recipient peer ID
            
        Returns:
            New MediaTransfer instance
        """
        transfer = MediaTransfer(
            id=transfer_id,
            media_info=media_file.to_media_info(),
            peer_id=peer_id,
            direction="send",
        )
        self._transfers[transfer_id] = transfer
        return transfer

    def create_receive_transfer(
        self,
        transfer_id: str,
        media_info: MediaInfo,
        peer_id: str
    ) -> MediaTransfer:
        """
        Create a new receive transfer.
        
        Args:
            transfer_id: Unique transfer ID
            media_info: File metadata
            peer_id: Sender peer ID
            
        Returns:
            New MediaTransfer instance
        """
        transfer = MediaTransfer(
            id=transfer_id,
            media_info=media_info,
            peer_id=peer_id,
            direction="receive",
        )
        self._transfers[transfer_id] = transfer
        return transfer

    def get_transfer(self, transfer_id: str) -> Optional[MediaTransfer]:
        """Get a transfer by ID."""
        return self._transfers.get(transfer_id)

    def remove_transfer(self, transfer_id: str) -> bool:
        """Remove a transfer from tracking."""
        if transfer_id in self._transfers:
            del self._transfers[transfer_id]
            return True
        return False

    def get_active_transfers(self) -> list[MediaTransfer]:
        """Get all active (in-progress) transfers."""
        return [
            t for t in self._transfers.values()
            if t.status == TransferStatus.IN_PROGRESS
        ]

    def get_pending_transfers(self) -> list[MediaTransfer]:
        """Get all pending transfers."""
        return [
            t for t in self._transfers.values()
            if t.status == TransferStatus.PENDING
        ]

    def get_completed_transfers(self) -> list[MediaTransfer]:
        """Get all completed transfers."""
        return [
            t for t in self._transfers.values()
            if t.status == TransferStatus.COMPLETED
        ]

    def cleanup_completed(self, older_than_seconds: float = 3600) -> int:
        """
        Remove completed transfers older than specified time.
        
        Args:
            older_than_seconds: Age threshold in seconds
            
        Returns:
            Number of transfers cleaned up
        """
        now = datetime.now()
        to_remove = []

        for transfer_id, transfer in self._transfers.items():
            if transfer.status in (TransferStatus.COMPLETED, TransferStatus.FAILED, TransferStatus.CANCELLED):
                if transfer.completed_at:
                    age = (now - transfer.completed_at).total_seconds()
                    if age > older_than_seconds:
                        to_remove.append(transfer_id)

        for transfer_id in to_remove:
            del self._transfers[transfer_id]

        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} old transfers")

        return len(to_remove)

    @property
    def active_count(self) -> int:
        """Get count of active transfers."""
        return len(self.get_active_transfers())

    @property
    def can_start_transfer(self) -> bool:
        """Check if a new transfer can be started."""
        return self.active_count < self.max_concurrent

    def __len__(self) -> int:
        return len(self._transfers)

    def __repr__(self) -> str:
        return f"TransferManager(active={self.active_count}, total={len(self)})"
