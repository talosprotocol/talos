#!/usr/bin/env python3
"""
Example 4: Light Client (SPV)

This example demonstrates:
- Creating light blockchain
- Adding block headers
- SPV proof verification
- Storage efficiency

Copy-paste ready!
"""

from src.core.light import (
    LightBlockchain,
    BlockHeader,
    SPVProof,
)
from src.core.blockchain import Blockchain


def main():
    print("=" * 50)
    print("Example 4: Light Client (SPV)")
    print("=" * 50)
    
    # ========================================
    # 1. Create Full Blockchain (Server)
    # ========================================
    print("\n[1] Creating Full Blockchain...")
    
    full = Blockchain(difficulty=1)
    
    # Add some data
    for i in range(3):
        full.add_data({"msg": f"Message {i}"})
        full.mine_pending()
    
    print(f"  Full blockchain: {len(full.chain)} blocks")
    
    # ========================================
    # 2. Create Light Client
    # ========================================
    print("\n[2] Creating Light Client...")
    
    light = LightBlockchain(difficulty=1)
    print(f"  Light client height: {light.height}")
    
    # ========================================
    # 3. Sync Headers
    # ========================================
    print("\n[3] Syncing Headers...")
    
    # Extract headers from full blockchain
    for block in full.chain:
        header = BlockHeader.from_block(block, difficulty=1)
        light.add_header(header)
    
    print(f"  Synced headers: {len(light)}")
    print(f"  Latest hash: {light.latest_hash[:16]}...")
    
    # ========================================
    # 4. Verify SPV Proof
    # ========================================
    print("\n[4] SPV Proof Verification...")
    
    # Create proof for data in block 1
    block = full.chain[1]
    proof = SPVProof(
        data_hash=block.merkle_root,
        block_hash=block.hash,
        block_height=block.index,
        merkle_root=block.merkle_root,
        merkle_path=[],  # Single element tree
    )
    
    # Verify
    is_valid = light.verify_spv_proof(proof)
    print(f"  Proof valid: {is_valid}")
    print(f"  Data hash: {proof.data_hash[:16]}...")
    
    # Check cached
    has_data = light.has_verified_data(block.merkle_root)
    print(f"  Data cached: {has_data}")
    
    # ========================================
    # 5. Storage Comparison
    # ========================================
    print("\n[5] Storage Comparison...")
    
    import json
    
    full_size = len(json.dumps(full.to_dict()))
    light_size = sum(h.size for h in light.headers)
    
    print(f"  Full chain: {full_size:,} bytes")
    print(f"  Light headers: {light_size:,} bytes")
    print(f"  Reduction: {100 - (light_size / full_size * 100):.1f}%")
    
    # ========================================
    # 6. Sync Requests
    # ========================================
    print("\n[6] Sync Protocol...")
    
    # Generate sync request
    sync_req = light.get_sync_request(batch_size=100)
    print(f"  Sync request: {sync_req}")
    
    # Generate proof request
    proof_req = light.get_proof_request("somehash123")
    print(f"  Proof request: {proof_req}")
    
    # ========================================
    # 7. Statistics
    # ========================================
    print("\n[7] Light Client Stats...")
    
    stats = light.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    print("Example 4 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
