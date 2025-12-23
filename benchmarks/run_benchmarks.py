import time
import asyncio
import os
from statistics import mean
from src.core.crypto import Wallet
from src.core.blockchain import Blockchain, Block
from src.engine.engine import TransmissionEngine
from unittest.mock import MagicMock

def benchmark_crypto():
    print("Locked & Loaded: Benchmarking Cryptography...")
    wallet = Wallet.generate("Benchmarker")
    msg = b"Hello, benchmarks!"
    
    # 1. Signing
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        wallet.sign(msg)
        times.append(time.perf_counter() - start)
    print(f"  Signing (Ed25519): {mean(times)*1000:.3f} ms/op ({1/mean(times):.0f} ops/s)")
    
    # 2. Key Exchange
    peer = Wallet.generate("Peer")
    times = []
    from src.core.crypto import derive_shared_secret
    for _ in range(1000):
        start = time.perf_counter()
        derive_shared_secret(wallet.encryption_keys.private_key, peer.encryption_keys.public_key)
        times.append(time.perf_counter() - start)
    print(f"  ECDH (X25519):     {mean(times)*1000:.3f} ms/op ({1/mean(times):.0f} ops/s)")

def benchmark_blockchain():
    print("\nBenchmarking Blockchain...")
    chain = Blockchain(difficulty=1) # Minimal difficulty for raw throughput
    wallet = Wallet.generate("Miner")
    
    times = []
    for i in range(100):
        block = Block(
            index=i,
            previous_hash="00"*32,
            timestamp=time.time(),
            data={"msg": f"msg{i}"},
        )
        start = time.perf_counter()
        # We simulate the mine without full POW loop just to test hashing speed?
        # Actually create_block does mining.
        # Let's just hash.
        block.calculate_hash()
        times.append(time.perf_counter() - start)
        
    print(f"  Block Hashing:     {mean(times)*1000:.3f} ms/op ({1/mean(times):.0f} ops/s)")

if __name__ == "__main__":
    benchmark_crypto()
    benchmark_blockchain()
