"""
Rate Limiter for Talos Protocol (Phase 2 Hardening).

Uses time.monotonic() per protocol spec for accurate rate limiting
that is immune to wall clock adjustments.
"""

import time
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float = 100.0
    burst_size: int = 10
    window_seconds: float = 1.0


@dataclass
class SlidingWindowCounter:
    """
    Sliding window rate limiter using time.monotonic().
    
    Per Phase 2 spec: uses monotonic clock for accuracy.
    """
    config: RateLimitConfig
    _tokens: float = field(default=0.0, init=False)
    _last_update: float = field(default=0.0, init=False)
    _request_count: int = field(default=0, init=False)

    def __post_init__(self):
        self._tokens = float(self.config.burst_size)
        self._last_update = time.monotonic()

    def allow(self) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            True if request is allowed, False if rate limited
        """
        now = time.monotonic()
        elapsed = now - self._last_update
        self._last_update = now

        # Replenish tokens based on elapsed time
        self._tokens = min(
            self.config.burst_size,
            self._tokens + elapsed * self.config.requests_per_second
        )

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            self._request_count += 1
            return True
        
        return False

    def reset(self) -> None:
        """Reset rate limiter state."""
        self._tokens = float(self.config.burst_size)
        self._last_update = time.monotonic()
        self._request_count = 0

    @property
    def request_count(self) -> int:
        """Total requests allowed since creation/reset."""
        return self._request_count


class SessionRateLimiter:
    """
    Per-session rate limiting for capability authorization.
    
    Each session gets its own sliding window counter.
    """

    def __init__(self, default_config: RateLimitConfig | None = None):
        self._config = default_config or RateLimitConfig()
        self._sessions: dict[bytes, SlidingWindowCounter] = {}
        self._max_sessions = 10000  # Prevent memory exhaustion

    def allow(self, session_id: bytes) -> bool:
        """
        Check if request from session is allowed.
        
        Args:
            session_id: 16-byte session identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        if session_id not in self._sessions:
            if len(self._sessions) >= self._max_sessions:
                self._evict_inactive()
            self._sessions[session_id] = SlidingWindowCounter(self._config)

        return self._sessions[session_id].allow()

    def remove_session(self, session_id: bytes) -> bool:
        """Remove a session from rate limiting."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _evict_inactive(self) -> None:
        """Remove oldest sessions (basic LRU)."""
        # Remove 10% of sessions
        sessions_to_remove = max(1, len(self._sessions) // 10)
        session_ids = list(self._sessions.keys())[:sessions_to_remove]
        for sid in session_ids:
            del self._sessions[sid]

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            "active_sessions": len(self._sessions),
            "max_sessions": self._max_sessions,
            "config": {
                "requests_per_second": self._config.requests_per_second,
                "burst_size": self._config.burst_size,
            }
        }
