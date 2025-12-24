#!/usr/bin/env python3
"""
Example 5: Decentralized Identity (DIDs)

This example demonstrates:
- Creating DID documents
- Adding verification methods
- Adding service endpoints
- DID validation
- Serialization

Copy-paste ready!
"""

from src.core.did import (
    DIDDocument,
    DIDManager,
    validate_did,
)
from src.core.crypto import generate_signing_keypair, generate_encryption_keypair
from dataclasses import dataclass


# Mock keypair for DIDManager
@dataclass
class MockKeypair:
    public_key: bytes
    private_key: bytes = b""


def main():
    print("=" * 50)
    print("Example 5: Decentralized Identity (DIDs)")
    print("=" * 50)
    
    # ========================================
    # 1. Create DID with Manager
    # ========================================
    print("\n[1] Creating DID...")
    
    # Generate keys
    signing = generate_signing_keypair()
    encryption = generate_encryption_keypair()
    
    # Create manager with mock interface
    mock_signing = MockKeypair(public_key=signing.public_key)
    mock_encryption = MockKeypair(public_key=encryption.public_key)
    
    manager = DIDManager(mock_signing, mock_encryption)
    did = manager.did
    
    print(f"  DID: {did}")
    
    # ========================================
    # 2. Create DID Document
    # ========================================
    print("\n[2] Creating DID Document...")
    
    doc = manager.create_document(
        service_endpoint="wss://my-agent.example.com:8765"
    )
    
    print(f"  Document ID: {doc.id}")
    print(f"  Created: {doc.created}")
    
    # ========================================
    # 3. Verification Methods
    # ========================================
    print("\n[3] Verification Methods...")
    
    for method in doc.verification_method:
        print(f"  {method.id.split('#')[1]}: {method.type}")
    
    print(f"  Authentication: {len(doc.authentication)} keys")
    print(f"  Key Agreement: {len(doc.key_agreement)} keys")
    
    # ========================================
    # 4. Service Endpoints
    # ========================================
    print("\n[4] Service Endpoints...")
    
    for service in doc.service:
        print(f"  {service.type}: {service.service_endpoint}")
    
    # Add another service
    doc.add_service(
        service_id="#backup",
        service_type="TalosBackup",
        endpoint="https://backup.example.com",
        description="Backup messaging endpoint",
    )
    print(f"  Total services: {len(doc.service)}")
    
    # ========================================
    # 5. DID Validation
    # ========================================
    print("\n[5] DID Validation...")
    
    test_dids = [
        did,
        "did:talos:invalid",
        "did:other:" + "a" * 32,
        "not-a-did",
    ]
    
    for test_did in test_dids:
        is_valid = validate_did(test_did)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {test_did[:40]}...")
    
    # ========================================
    # 6. JSON Serialization
    # ========================================
    print("\n[6] JSON Serialization...")
    
    json_str = doc.to_json(indent=2)
    print(f"  JSON length: {len(json_str)} chars")
    print(f"  Preview: {json_str[:100]}...")
    
    # Round-trip
    loaded = DIDDocument.from_json(json_str)
    print(f"  Round-trip: {loaded.id == doc.id}")
    
    # ========================================
    # 7. Update Service
    # ========================================
    print("\n[7] Update Service...")
    
    manager.update_service_endpoint("wss://new-endpoint.example.com:9000")
    
    svc = manager.document.get_service("#messaging")
    print(f"  Updated: {svc.service_endpoint if svc else 'N/A'}")
    
    print("\n" + "=" * 50)
    print("Example 5 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
