"""
Tests for Rate Limiter (Phase 2 Hardening).
"""

import time
import pytest

from src.core.rate_limiter import (
    RateLimitConfig,
    SlidingWindowCounter,
    SessionRateLimiter,
)


class TestSlidingWindowCounter:
    """Tests for the sliding window rate limiter."""

    def test_allows_burst(self):
        """Test that burst requests are allowed."""
        config = RateLimitConfig(burst_size=5, requests_per_second=10)
        limiter = SlidingWindowCounter(config)

        # Should allow burst_size requests immediately
        for _ in range(5):
            assert limiter.allow() is True

        # Next request should be rate limited
        assert limiter.allow() is False

    def test_replenishes_over_time(self):
        """Test that tokens replenish based on time.monotonic()."""
        config = RateLimitConfig(burst_size=2, requests_per_second=10)
        limiter = SlidingWindowCounter(config)

        # Exhaust tokens
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False

        # Wait for token replenishment (0.1s = 1 token at 10/sec)
        time.sleep(0.15)
        assert limiter.allow() is True

    def test_request_count_tracking(self):
        """Test request count tracking."""
        config = RateLimitConfig(burst_size=3, requests_per_second=10)
        limiter = SlidingWindowCounter(config)

        limiter.allow()
        limiter.allow()

        assert limiter.request_count == 2

    def test_reset(self):
        """Test reset clears state."""
        config = RateLimitConfig(burst_size=2, requests_per_second=10)
        limiter = SlidingWindowCounter(config)

        limiter.allow()
        limiter.allow()
        assert limiter.allow() is False

        limiter.reset()

        assert limiter.allow() is True
        assert limiter.request_count == 1


class TestSessionRateLimiter:
    """Tests for per-session rate limiting."""

    def test_independent_sessions(self):
        """Test that each session has independent rate limit."""
        limiter = SessionRateLimiter(RateLimitConfig(burst_size=2, requests_per_second=10))

        session1 = b"\x01" * 16
        session2 = b"\x02" * 16

        # Each session has its own burst
        assert limiter.allow(session1) is True
        assert limiter.allow(session1) is True
        assert limiter.allow(session1) is False

        # Session 2 still has full burst
        assert limiter.allow(session2) is True
        assert limiter.allow(session2) is True
        assert limiter.allow(session2) is False

    def test_remove_session(self):
        """Test session removal."""
        limiter = SessionRateLimiter()
        session = b"\x01" * 16

        limiter.allow(session)
        assert limiter.remove_session(session) is True
        assert limiter.remove_session(session) is False

    def test_stats(self):
        """Test statistics."""
        limiter = SessionRateLimiter(RateLimitConfig(burst_size=5, requests_per_second=100))

        session1 = b"\x01" * 16
        session2 = b"\x02" * 16

        limiter.allow(session1)
        limiter.allow(session2)

        stats = limiter.get_stats()
        assert stats["active_sessions"] == 2
        assert stats["config"]["burst_size"] == 5
        assert stats["config"]["requests_per_second"] == 100

    def test_max_sessions_eviction(self):
        """Test that max sessions limit triggers eviction."""
        limiter = SessionRateLimiter()
        limiter._max_sessions = 10  # Small for testing

        # Add sessions up to limit
        for i in range(15):
            session = bytes([i] * 16)
            limiter.allow(session)

        # Should have evicted some
        assert len(limiter._sessions) <= 10


class TestRateLimiterPerformance:
    """Performance tests for rate limiter."""

    def test_allow_latency(self):
        """Test that allow() is fast (<100μs)."""
        config = RateLimitConfig(burst_size=1000, requests_per_second=10000)
        limiter = SlidingWindowCounter(config)

        latencies = []
        for _ in range(100):
            start = time.perf_counter_ns()
            limiter.allow()
            end = time.perf_counter_ns()
            latencies.append((end - start) // 1000)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        print(f"\nallow() latency: avg={avg_latency:.1f}μs, max={max_latency}μs")
        assert max_latency < 100, f"Max latency {max_latency}μs exceeds 100μs"
