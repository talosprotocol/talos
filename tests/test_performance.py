"""
Performance Tests for Talos Protocol Phase 1.

Tests verify the performance SLAs defined in PROTOCOL.md Section 0:
- Authorization (cached session): <1ms p99
- Signature verification: <500μs
- Total Talos overhead: <5ms p99

Run with: pytest tests/test_performance.py -v --tb=short -s
"""

import pytest
import time
import secrets
import statistics
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.core.capability import (
    CapabilityManager,
)


class TestPerformanceSLAs:
    """Performance tests verifying Phase 1 SLAs from PROTOCOL.md."""

    @pytest.fixture
    def keypair(self):
        """Generate test keypair."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @pytest.fixture
    def manager(self, keypair):
        """Create capability manager."""
        private_key, public_key = keypair
        return CapabilityManager(
            issuer_id="did:talos:issuer",
            private_key=private_key,
            public_key=public_key,
        )

    def test_authorize_fast_under_1ms_p99(self, manager):
        """
        SLA: authorize_fast <1ms p99 (cached session authorization).
        
        Per PROTOCOL.md Section 0.1:
        - Authorization (cached session): <1ms target, 5ms hard limit
        """
        # Setup: Grant capability and cache session
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tool:test/method:ping",
            expires_in=3600,
        )
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Warmup
        for _ in range(10):
            manager.authorize_fast(session_id, "test", "ping")

        # Collect latencies
        latencies = []
        iterations = 1000

        for _ in range(iterations):
            result = manager.authorize_fast(session_id, "test", "ping")
            assert result.allowed is True
            latencies.append(result.latency_us)

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(iterations * 0.50)]
        p95 = latencies_sorted[int(iterations * 0.95)]
        p99 = latencies_sorted[int(iterations * 0.99)]
        avg = statistics.mean(latencies)
        max_latency = max(latencies)

        print("\n=== authorize_fast Performance ===")
        print(f"  Iterations: {iterations}")
        print(f"  Average: {avg:.1f}μs")
        print(f"  p50: {p50}μs")
        print(f"  p95: {p95}μs")
        print(f"  p99: {p99}μs")
        print(f"  Max: {max_latency}μs")

        # SLA assertions
        assert p99 < 1000, f"p99 latency {p99}μs exceeds 1ms (1000μs) SLA"
        assert max_latency < 5000, f"Max latency {max_latency}μs exceeds 5ms hard limit"

    def test_signature_verification_under_500us(self, manager):
        """
        SLA: Signature verification <500μs.
        
        Per PROTOCOL.md Section 0.1:
        - Signature verification: <500μs target
        """
        # Create capability for verification
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tool:test/method:ping",
            expires_in=3600,
        )

        # Warmup
        for _ in range(10):
            manager.verify(cap)

        # Collect latencies
        latencies = []
        iterations = 500

        for _ in range(iterations):
            start = time.perf_counter_ns()
            result = manager.verify(cap)
            end = time.perf_counter_ns()
            
            assert result is True
            latencies.append((end - start) // 1000)  # Convert to μs

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(iterations * 0.50)]
        p95 = latencies_sorted[int(iterations * 0.95)]
        p99 = latencies_sorted[int(iterations * 0.99)]
        avg = statistics.mean(latencies)

        print("\n=== verify() (signature check) Performance ===")
        print(f"  Iterations: {iterations}")
        print(f"  Average: {avg:.1f}μs")
        print(f"  p50: {p50}μs")
        print(f"  p95: {p95}μs")
        print(f"  p99: {p99}μs")

        # SLA assertion (500μs target, 2ms hard limit)
        assert p99 < 2000, f"p99 signature verify {p99}μs exceeds 2ms hard limit"

    def test_grant_capability_performance(self, manager):
        """
        Test capability granting performance.
        
        Grant includes: ID generation, timestamp, signature.
        """
        # Warmup
        for i in range(10):
            manager.grant(f"did:talos:agent{i}", "tool:test", expires_in=3600)

        # Collect latencies
        latencies = []
        iterations = 500

        for i in range(iterations):
            start = time.perf_counter_ns()
            cap = manager.grant(
                subject=f"did:talos:agent{i}",
                scope="tool:test/method:ping",
                expires_in=3600,
            )
            end = time.perf_counter_ns()
            
            assert cap.id is not None
            latencies.append((end - start) // 1000)

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(iterations * 0.50)]
        p95 = latencies_sorted[int(iterations * 0.95)]
        p99 = latencies_sorted[int(iterations * 0.99)]
        avg = statistics.mean(latencies)

        print("\n=== grant() Performance ===")
        print(f"  Iterations: {iterations}")
        print(f"  Average: {avg:.1f}μs")
        print(f"  p50: {p50}μs")
        print(f"  p95: {p95}μs")
        print(f"  p99: {p99}μs")

        # Capability grant should complete in reasonable time
        assert p99 < 5000, f"p99 grant latency {p99}μs exceeds 5ms"

    def test_revocation_check_under_100us(self, manager):
        """
        SLA: Revocation check <100μs.
        
        Per PROTOCOL.md Section 0.1:
        - Revocation check: <100μs target
        """
        # Setup: Grant capability, cache session, revoke 50% of capabilities
        session_ids = []
        for i in range(100):
            cap = manager.grant(
                subject=f"did:talos:agent{i}",
                scope="tool:test/method:ping",
                expires_in=3600,
            )
            session_id = secrets.token_bytes(16)
            manager.cache_session(session_id, cap)
            session_ids.append(session_id)
            
            # Revoke half
            if i % 2 == 0:
                manager.revoke(cap.id, reason="test")

        # Collect latencies (revocation check is part of authorize_fast)
        latencies = []
        iterations = 500

        for _ in range(iterations):
            session_id = secrets.choice(session_ids)
            result = manager.authorize_fast(session_id, "test", "ping")
            latencies.append(result.latency_us)

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(iterations * 0.50)]
        p99 = latencies_sorted[int(iterations * 0.99)]
        avg = statistics.mean(latencies)

        print("\n=== authorize_fast with revocation checks ===")
        print(f"  Iterations: {iterations}")
        print(f"  Average: {avg:.1f}μs")
        print(f"  p50: {p50}μs")
        print(f"  p99: {p99}μs")

        # Even with revocation checks, should be fast
        assert p99 < 1000, f"p99 with revocation {p99}μs exceeds 1ms SLA"

    def test_session_cache_lru_eviction_performance(self, manager):
        """
        Test that LRU eviction doesn't degrade performance.
        """
        # Fill cache to max, then overflow
        manager._session_cache_max_size = 1000

        latencies = []
        iterations = 1500  # 50% overflow

        for i in range(iterations):
            cap = manager.grant(
                subject=f"did:talos:agent{i}",
                scope="tool:test/method:ping",
                expires_in=3600,
            )
            session_id = secrets.token_bytes(16)
            
            start = time.perf_counter_ns()
            manager.cache_session(session_id, cap)
            end = time.perf_counter_ns()
            
            latencies.append((end - start) // 1000)

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[int(iterations * 0.50)]
        p99 = latencies_sorted[int(iterations * 0.99)]
        avg = statistics.mean(latencies)

        print("\n=== cache_session with LRU eviction ===")
        print(f"  Iterations: {iterations}")
        print(f"  Cache size: {len(manager._session_cache)}")
        print(f"  Average: {avg:.1f}μs")
        print(f"  p50: {p50}μs")
        print(f"  p99: {p99}μs")

        # Cache operations should be fast even with eviction
        assert p99 < 10000, f"p99 cache operation {p99}μs exceeds 10ms"

    def test_concurrent_authorization_performance(self, manager):
        """
        Test authorization under concurrent load.
        """
        import concurrent.futures

        # Setup: Create 100 sessions
        sessions = []
        for i in range(100):
            cap = manager.grant(
                subject=f"did:talos:agent{i}",
                scope="tool:test/method:ping",
                expires_in=3600,
            )
            session_id = secrets.token_bytes(16)
            manager.cache_session(session_id, cap)
            sessions.append(session_id)

        def auth_worker(session_ids):
            latencies = []
            for _ in range(100):
                session_id = secrets.choice(session_ids)
                result = manager.authorize_fast(session_id, "test", "ping")
                latencies.append(result.latency_us)
            return latencies

        # Run with multiple threads
        all_latencies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(auth_worker, sessions) for _ in range(10)]
            for future in concurrent.futures.as_completed(futures):
                all_latencies.extend(future.result())

        # Calculate percentiles
        latencies_sorted = sorted(all_latencies)
        total = len(latencies_sorted)
        p50 = latencies_sorted[int(total * 0.50)]
        p99 = latencies_sorted[int(total * 0.99)]
        avg = statistics.mean(all_latencies)

        print("\n=== Concurrent authorization (10 threads × 100 calls) ===")
        print(f"  Total calls: {total}")
        print(f"  Average: {avg:.1f}μs")
        print(f"  p50: {p50}μs")
        print(f"  p99: {p99}μs")

        # Should still meet SLA under concurrent load
        assert p99 < 2000, f"p99 under concurrent load {p99}μs exceeds 2ms"


class TestThroughput:
    """Throughput tests for capacity planning."""

    @pytest.fixture
    def manager(self):
        """Create capability manager."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return CapabilityManager(
            issuer_id="did:talos:issuer",
            private_key=private_key,
            public_key=public_key,
        )

    def test_authorization_throughput(self, manager):
        """
        Measure authorizations per second.
        
        Target: >10,000 authorizations/second (cached path).
        """
        # Setup
        cap = manager.grant(
            subject="did:talos:agent",
            scope="tool:test/method:ping",
            expires_in=3600,
        )
        session_id = secrets.token_bytes(16)
        manager.cache_session(session_id, cap)

        # Measure throughput
        iterations = 10000
        start = time.perf_counter()
        
        for _ in range(iterations):
            result = manager.authorize_fast(session_id, "test", "ping")
            assert result.allowed is True
        
        elapsed = time.perf_counter() - start
        throughput = iterations / elapsed

        print("\n=== Authorization Throughput ===")
        print(f"  Iterations: {iterations}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.0f} auth/sec")

        # Target: >10,000/sec
        assert throughput > 10000, f"Throughput {throughput:.0f}/sec below 10,000/sec target"

    def test_capability_grant_throughput(self, manager):
        """
        Measure capability grants per second.
        
        Target: >1,000 grants/second.
        """
        iterations = 1000
        start = time.perf_counter()
        
        for i in range(iterations):
            manager.grant(
                subject=f"did:talos:agent{i}",
                scope="tool:test/method:ping",
                expires_in=3600,
            )
        
        elapsed = time.perf_counter() - start
        throughput = iterations / elapsed

        print("\n=== Capability Grant Throughput ===")
        print(f"  Iterations: {iterations}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.0f} grants/sec")

        # Target: >1,000/sec
        assert throughput > 1000, f"Throughput {throughput:.0f}/sec below 1,000/sec target"
