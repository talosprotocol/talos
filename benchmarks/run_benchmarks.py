import time
import asyncio
import os
import shutil
from statistics import mean, median
from pathlib import Path
from src.core.crypto import Wallet, batch_verify_signatures, derive_shared_secret, encrypt_message, decrypt_message
from src.core.blockchain import Blockchain, Block
from src.core.validation.engine import ValidationEngine
from src.core.storage import StorageConfig, LMDBStorage, BlockStorage
from src.core.serialization import serialize_message, deserialize_message

def print_result(name, ops, total_time):
    ms_per_op = (total_time / ops) * 1000
    ops_per_sec = ops / total_time
    print(f"| {name:<25} | {ms_per_op:.4f}ms | {ops_per_sec:,.0f} |")

def benchmark_crypto():
    print("\n## Cryptography")
    print(f"| {'Operation':<25} | {'Latency':<9} | {'Throughput (ops/s)'} |")
    print(f"|{'-'*27}|{'-'*11}|{'-'*22}|")
    
    wallet = Wallet.generate("Benchmarker")
    msg = b"Hello, benchmarks!" * 100  # 1.8KB message
    
    # 1. Signing
    count = 1000
    start = time.perf_counter()
    for _ in range(count):
        wallet.sign(msg)
    print_result("Sign (Ed25519)", count, time.perf_counter() - start)
    
    # 2. Verify
    sig = wallet.sign(msg)
    pk = wallet.signing_keys.public_key
    start = time.perf_counter()
    for _ in range(count):
        wallet.signing_keys.public_key  # Access property
        from src.core.crypto import verify_signature
        verify_signature(msg, sig, pk)
    print_result("Verify (Ed25519)", count, time.perf_counter() - start)
    
    # 3. Batch Verify
    items = [(msg, sig, pk)] * 100
    batch_count = 100
    start = time.perf_counter()
    for _ in range(batch_count):
        batch_verify_signatures(items, parallel=True)
    total_ops = batch_count * 100
    print_result("Batch Verify (Parallel)", total_ops, time.perf_counter() - start)
    
    # 4. Encryption
    peer = Wallet.generate("Peer")
    shared = derive_shared_secret(wallet.encryption_keys.private_key, peer.encryption_keys.public_key)
    start = time.perf_counter()
    for _ in range(count):
        encrypt_message(msg, shared)
    print_result("Encrypt (ChaCha20)", count, time.perf_counter() - start)

async def benchmark_validation():
    print("\n## Validation")
    print(f"| {'Operation':<25} | {'Latency':<9} | {'Throughput (ops/s)'} |")
    print(f"|{'-'*27}|{'-'*11}|{'-'*22}|")
    
    # Setup complex block
    bc = Blockchain(difficulty=1)
    messages = [{"id": f"msg{i}", "content": f"data{i}" * 50} for i in range(100)]
    bc.add_data({"messages": messages})
    block = bc.mine_pending()
    engine = ValidationEngine()
    
    if not block:
        print("Failed to mine block for validation benchmark")
        return

    count = 100
    
    # 1. Standard
    start = time.perf_counter()
    for _ in range(count):
        await engine.validate_block(block)
    print_result("Standard Validation", count, time.perf_counter() - start)
    
    # 2. Parallel
    start = time.perf_counter()
    for _ in range(count):
        await engine.validate_block_parallel(block)
    print_result("Parallel Validation", count, time.perf_counter() - start)

def benchmark_serialization():
    print("\n## Serialization")
    print(f"| {'Operation':<25} | {'Latency':<9} | {'Throughput (ops/s)'} |")
    print(f"|{'-'*27}|{'-'*11}|{'-'*22}|")
    
    data = {
        "id": "test-msg",
        "content": "data" * 100,
        "meta": {"timestamp": 1234567890, "tags": ["bench", "mark"]}
    }
    
    count = 10000
    start = time.perf_counter()
    for _ in range(count):
        serialize_message(data)
    print_result("Serialize (JSON)", count, time.perf_counter() - start)
    
    serialized = serialize_message(data)
    start = time.perf_counter()
    for _ in range(count):
        deserialize_message(serialized)
    print_result("Deserialize (JSON)", count, time.perf_counter() - start)

def benchmark_storage():
    print("\n## Storage (LMDB)")
    print(f"| {'Operation':<25} | {'Latency':<9} | {'Throughput (ops/s)'} |")
    print(f"|{'-'*27}|{'-'*11}|{'-'*22}|")
    
    path = "bench_db"
    if Path(path).exists():
        shutil.rmtree(path)
    
    try:
        config = StorageConfig(path=path)
        storage = LMDBStorage(config)
        
        count = 10000
        # Writes
        start = time.perf_counter()
        with storage.write() as txn:
            for i in range(count):
                storage.put(txn, f"key{i}".encode(), f"val{i}".encode())
        print_result("Write (Batch)", count, time.perf_counter() - start)
        
        # Reads
        start = time.perf_counter()
        with storage.read() as txn:
            for i in range(count):
                storage.get(txn, f"key{i}".encode())
        print_result("Read (Random)", count, time.perf_counter() - start)
        
        storage.close()
    finally:
        if Path(path).exists():
            shutil.rmtree(path)

async def main():
    print("# Talos Protocol Benchmarks")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    benchmark_crypto()
    await benchmark_validation()
    benchmark_serialization()
    benchmark_storage()

if __name__ == "__main__":
    asyncio.run(main())
