#!/usr/bin/env python3
"""
Example 2: Blockchain Operations

This example demonstrates:
- Creating a blockchain
- Adding data
- Mining blocks
- Chain validation
- Merkle proofs

Copy-paste ready!
"""

from src.core.blockchain import Blockchain, Block, MerkleProof


def main():
    print("=" * 50)
    print("Example 2: Blockchain Operations")
    print("=" * 50)
    
    # ========================================
    # 1. Create Blockchain
    # ========================================
    print("\n[1] Creating Blockchain...")
    
    bc = Blockchain(difficulty=1)  # Low difficulty for demo
    print(f"  Difficulty: {bc.difficulty}")
    print(f"  Genesis block: {bc.chain[0].hash[:16]}...")
    
    # ========================================
    # 2. Add Data
    # ========================================
    print("\n[2] Adding Data...")
    
    bc.add_data({"sender": "alice", "msg": "Hello"})
    bc.add_data({"sender": "bob", "msg": "Hi there!"})
    bc.add_data({"sender": "alice", "msg": "How are you?"})
    
    print(f"  Pending data: {len(bc.pending_data)} items")
    
    # ========================================
    # 3. Mine Block
    # ========================================
    print("\n[3] Mining Block...")
    
    block = bc.mine_pending()
    print(f"  Block #{block.index}")
    print(f"  Hash: {block.hash[:24]}...")
    print(f"  Merkle root: {block.merkle_root[:24]}...")
    print(f"  Nonce: {block.nonce}")
    
    # ========================================
    # 4. Validate Chain
    # ========================================
    print("\n[4] Validating Chain...")
    
    is_valid = bc.validate_chain(bc.chain)
    print(f"  Valid: {is_valid}")
    print(f"  Chain length: {len(bc.chain)} blocks")
    
    # ========================================
    # 5. Query Data
    # ========================================
    print("\n[5] Querying Data...")
    
    # Get block by index
    block = bc.chain[1] if len(bc.chain) > 1 else None
    if block:
        print(f"  Block 1 messages: {len(block.data.get('messages', []))}")
    
    # ========================================
    # 6. Block Details
    # ========================================
    print("\n[6] Block Details...")
    
    for i, block in enumerate(bc.chain):
        msg_count = len(block.data.get("messages", []))
        print(f"  Block {i}: hash={block.hash[:12]}... msgs={msg_count}")
    
    # ========================================
    # 7. Persistence
    # ========================================
    print("\n[7] Persistence...")
    
    # Save
    bc_dict = bc.to_dict()
    print(f"  Saved blockchain with {len(bc_dict['chain'])} blocks")
    
    # Load
    bc_loaded = Blockchain.from_dict(bc_dict)
    print(f"  Loaded blockchain with {len(bc_loaded.chain)} blocks")
    print(f"  Match: {bc.chain[-1].hash == bc_loaded.chain[-1].hash}")
    
    print("\n" + "=" * 50)
    print("Example 2 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
