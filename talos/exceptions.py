"""
Talos SDK Exceptions.

All SDK exceptions inherit from TalosError for easy catching.
"""


class TalosError(Exception):
    """Base exception for all Talos SDK errors."""
    
    def __init__(self, message: str, code: str = "TALOS_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message


class ConnectionError(TalosError):
    """Failed to connect to peer or network."""
    
    def __init__(self, message: str, peer_id: str = None):
        super().__init__(message, "CONNECTION_ERROR")
        self.peer_id = peer_id


class EncryptionError(TalosError):
    """Encryption or decryption failed."""
    
    def __init__(self, message: str):
        super().__init__(message, "ENCRYPTION_ERROR")


class AuthenticationError(TalosError):
    """Authentication or signature verification failed."""
    
    def __init__(self, message: str, peer_id: str = None):
        super().__init__(message, "AUTHENTICATION_ERROR")
        self.peer_id = peer_id


class RateLimitError(TalosError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message, "RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class SessionError(TalosError):
    """Session-related error (e.g., no session, expired)."""
    
    def __init__(self, message: str, peer_id: str = None):
        super().__init__(message, "SESSION_ERROR")
        self.peer_id = peer_id


class BlockchainError(TalosError):
    """Blockchain validation or sync error."""
    
    def __init__(self, message: str, block_hash: str = None):
        super().__init__(message, "BLOCKCHAIN_ERROR")
        self.block_hash = block_hash


class TimeoutError(TalosError):
    """Operation timed out."""
    
    def __init__(self, message: str, timeout: float = None):
        super().__init__(message, "TIMEOUT_ERROR")
        self.timeout = timeout
