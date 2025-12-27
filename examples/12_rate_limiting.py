#!/usr/bin/env python3
"""
Example 12: Rate Limiting

This example demonstrates the Phase 2 rate limiting system:
- SlidingWindowCounter (token bucket algorithm)
- SessionRateLimiter (per-session limits)
- Burst handling and replenishment
"""

import secrets
import time

from src.core.rate_limiter import (
    SlidingWindowCounter,
    SessionRateLimiter,
    RateLimitConfig,
)


def main():
    print("=" * 50)
    print("Example 12: Rate Limiting")
    print("=" * 50)
    
    # Basic sliding window counter
    print("\n[1] Sliding Window Counter...")
    config = RateLimitConfig(
        burst_size=5,
        requests_per_second=2,
    )
    counter = SlidingWindowCounter(config)
    
    print(f"  Burst size: {config.burst_size}")
    print(f"  Refill rate: {config.requests_per_second}/sec")
    
    # Use burst
    allowed = sum(1 for _ in range(10) if counter.allow())
    print(f"  10 requests: {allowed} allowed, {10-allowed} blocked")
    
    # Wait for replenishment
    print("\n[2] Token Replenishment...")
    print("  Waiting 1 second...")
    time.sleep(1.0)
    
    allowed = sum(1 for _ in range(5) if counter.allow())
    print(f"  5 requests after wait: {allowed} allowed")
    
    # Session rate limiter
    print("\n[3] Session Rate Limiter...")
    session_config = RateLimitConfig(
        burst_size=3,
        requests_per_second=1,
    )
    limiter = SessionRateLimiter(session_config)
    
    session_a = secrets.token_bytes(16)
    session_b = secrets.token_bytes(16)
    
    print(f"  Session A: {session_a.hex()[:8]}...")
    print(f"  Session B: {session_b.hex()[:8]}...")
    
    # Each session has independent limits
    a_allowed = sum(1 for _ in range(5) if limiter.allow(session_a))
    b_allowed = sum(1 for _ in range(5) if limiter.allow(session_b))
    
    print(f"\n  Session A: {a_allowed}/5 allowed (burst=3)")
    print(f"  Session B: {b_allowed}/5 allowed (burst=3)")
    
    # Stats
    print("\n[4] Limiter Stats...")
    stats = limiter.get_stats()
    print(f"  Active sessions: {stats['active_sessions']}")
    print(f"  Max sessions: {stats['max_sessions']}")
    print(f"  Config: {stats['config']}")
    
    print("\n" + "=" * 50)
    print("Example 12 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
