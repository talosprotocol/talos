# File Transfer

## Overview

BMP supports encrypted file transfer with:
- **End-to-end encryption** using ChaCha20-Poly1305
- **Chunked transfer** for large files (up to 2GB)
- **Hash verification** for integrity
- **Progress tracking** for user feedback

## Supported File Types

| Type | Extensions | Max Size | Chunk Size |
|------|------------|----------|------------|
| Images | jpg, png, gif, webp, svg | 50 MB | 256 KB |
| Audio | mp3, wav, ogg, flac, m4a | 200 MB | 512 KB |
| Video | mp4, webm, mov, avi, mkv | 2 GB | 1 MB |
| Documents | pdf, txt, doc, docx, xls | 100 MB | 256 KB |
| Archives | zip, tar, gz, rar, 7z | 500 MB | 512 KB |
| Other | * | 50 MB | 256 KB |

## Transfer Protocol

### Message Types

```python
FILE           # Start transfer (metadata only)
FILE_CHUNK     # Data chunk
FILE_COMPLETE  # Transfer finished
FILE_ERROR     # Transfer failed
```

### Flow Diagram

```
Sender                                    Recipient
  │                                          │
  │  1. Validate file (size, type)           │
  │  2. Calculate SHA-256 hash               │
  │  3. Create transfer ID                   │
  │                                          │
  │─── FILE ────────────────────────────────▶│
  │    {transfer_id, filename, size,         │
  │     mime_type, total_chunks}             │
  │                                          │
  │  4. Split into chunks                    │
  │  5. Encrypt each chunk                   │
  │                                          │
  │─── FILE_CHUNK[0] ──────────────────────▶│
  │─── FILE_CHUNK[1] ──────────────────────▶│
  │─── FILE_CHUNK[2] ──────────────────────▶│
  │    ...                                   │
  │                                          │
  │─── FILE_COMPLETE ──────────────────────▶│
  │    {transfer_id, file_hash}              │
  │                                          │
  │                      6. Reassemble chunks│
  │                      7. Verify hash      │
  │                      8. Save to disk     │
  │                      9. Invoke callbacks │
  │                                          │
```

## Usage

### CLI

```bash
# Send a file
bmp send-file alice@host "photo.jpg"

# Files are automatically received when listening
bmp listen --port 8766
# Received files saved to ~/.bmp/downloads/
```

### Python API

```python
from src.client import Client

client = Client(config)
await client.start()

# Send file
transfer_id = await client.send_file(
    recipient_id="abc123...",
    file_path="/path/to/document.pdf"
)

# Track progress
transfer = client.get_transfer(transfer_id)
print(f"Progress: {transfer.progress_percent}%")

# Receive files
def on_file_received(media):
    print(f"Received: {media.filename} ({media.size_formatted})")
    print(f"Saved to: {media.local_path}")
    print(f"Hash verified: {media.verified}")

client.on_file(on_file_received)
```

## MediaFile Class

```python
from src.engine.media import MediaFile

# Load file
file = MediaFile.from_path("/path/to/image.jpg")

print(file.filename)       # image.jpg
print(file.size)           # 2457600 (bytes)
print(file.size_formatted) # 2.4 MB
print(file.mime_type)      # image/jpeg
print(file.media_type)     # MediaType.IMAGE
print(file.file_hash)      # SHA-256 hash
print(file.chunk_size)     # 262144 (256 KB)

# Read in chunks
for chunk in file.read_chunks():
    process(chunk)
```

## TransferManager

```python
from src.engine.media import TransferManager, TransferStatus

manager = TransferManager(max_concurrent=5)

# Create send transfer
transfer = manager.create_send_transfer(
    transfer_id="uuid-1234",
    media_file=file,
    peer_id="recipient-address"
)

# Track state
transfer.start()
transfer.update_progress(bytes_sent=1024)
print(transfer.status)           # TransferStatus.IN_PROGRESS
print(transfer.progress_percent) # 50

transfer.complete()
print(transfer.status)           # TransferStatus.COMPLETED
```

## ReceivedMedia

When a file is received:

```python
@dataclass
class ReceivedMedia:
    id: str              # Transfer ID
    sender: str          # Sender's address
    filename: str        # Original filename
    size: int            # File size in bytes
    mime_type: str       # MIME type
    media_type: MediaType # IMAGE, AUDIO, VIDEO, etc.
    data: bytes          # File contents
    file_hash: str       # SHA-256 hash
    timestamp: float     # When received
    verified: bool       # Hash verification passed
    local_path: Path     # Where saved
```

## Security

### Encryption

1. Each chunk is encrypted separately with ChaCha20-Poly1305
2. Same shared secret as text messages
3. Unique nonce per chunk

### Verification

1. Sender computes SHA-256 of entire file
2. Hash sent in `FILE_COMPLETE` message
3. Recipient recomputes hash after reassembly
4. Transfer rejected if hashes don't match

### Privacy

- Filename and metadata encrypted in transit
- File contents never visible to network
- Only recipient can decrypt

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `FILE_ERROR` | Transfer failed | Retry or cancel |
| Hash mismatch | Corruption detected | Auto-reject, retry |
| Size exceeded | File too large | Use smaller file or split |
| Invalid type | Unsupported format | Convert to supported format |

## Downloads Directory

Default: `~/.bmp/downloads/`

Structure:
```
~/.bmp/downloads/
├── photo_abc123.jpg
├── document_def456.pdf
└── video_ghi789.mp4
```

Files are named: `{original_name}_{transfer_id}.{ext}`
