#!/usr/bin/env python3
"""
Example 7: Block Validation Engine

This example demonstrates:
- Creating validation engine
- Validating blocks
- Generating audit reports

Copy-paste ready!
"""

import asyncio
from src.core.blockchain import Blockchain
from src.core.validation import ValidationEngine, generate_audit_report


async def main():
    print("=" * 50)
    print("Example 7: Block Validation Engine")
    print("=" * 50)
    
    # ========================================
    # 1. Create Blockchain with Blocks
    # ========================================
    print("\n[1] Creating Blockchain...")
    
    bc = Blockchain(difficulty=1)
    
    # Add and mine blocks
    bc.add_data({"sender": "alice", "msg": "Hello"})
    bc.add_data({"sender": "bob", "msg": "Hi!"})
    bc.mine_pending()
    
    bc.add_data({"sender": "alice", "msg": "Bye"})
    bc.mine_pending()
    
    print(f"  Blocks: {len(bc.chain)}")
    
    # ========================================
    # 2. Create Validation Engine
    # ========================================
    print("\n[2] Creating Validation Engine...")
    
    engine = ValidationEngine(difficulty=1)
    print(f"  Engine ready")
    
    # ========================================
    # 3. Validate Blocks
    # ========================================
    print("\n[3] Validating Blocks...")
    
    for i, block in enumerate(bc.chain):
        prev = bc.chain[i-1] if i > 0 else None
        result = await engine.validate_block(block, prev)
        status = "✓" if result.is_valid else "✗"
        print(f"  Block {i}: {status} ({result.duration_ms:.2f}ms)")
    
    # ========================================
    # 4. Validation Details
    # ========================================
    print("\n[4] Validation Details (Block 1)...")
    
    result = await engine.validate_block(bc.chain[1], bc.chain[0])
    
    print(f"  Valid: {result.is_valid}")
    print(f"  Layers passed: {result.layers_passed}")
    print(f"  Layers failed: {result.layers_failed}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    # ========================================
    # 5. Generate Audit Report
    # ========================================
    print("\n[5] Generating Audit Report...")
    
    block = bc.chain[1]
    prev = bc.chain[0]
    result = await engine.validate_block(block, prev)
    
    report = generate_audit_report(block, result)
    
    print(f"  Report ID: {report.report_id[:16]}...")
    print(f"  Block hash: {report.block_hash[:16]}...")
    print(f"  Valid: {report.is_valid}")
    print(f"  Duration: {report.duration_ms:.2f}ms")
    
    # ========================================
    # 6. Full Chain Validation
    # ========================================
    print("\n[6] Full Chain Validation...")
    
    all_valid = True
    for i, block in enumerate(bc.chain):
        prev = bc.chain[i-1] if i > 0 else None
        result = await engine.validate_block(block, prev)
        if not result.is_valid:
            all_valid = False
            print(f"  Block {i} INVALID: {result.errors}")
    
    print(f"  Chain valid: {all_valid}")
    
    print("\n" + "=" * 50)
    print("Example 7 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
