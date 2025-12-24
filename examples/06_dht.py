#!/usr/bin/env python3
"""
Example 6: Distributed Hash Table (DHT)

This example demonstrates:
- Creating DHT nodes
- Routing table operations
- Key-value storage
- DID resolution

Copy-paste ready!
"""

import asyncio
from src.network.dht import (
    DHTNode,
    DHTStorage,
    RoutingTable,
    NodeInfo,
    DIDResolver,
    generate_node_id,
    xor_distance,
)


def main():
    print("=" * 50)
    print("Example 6: Distributed Hash Table (DHT)")
    print("=" * 50)
    
    # ========================================
    # 1. Node ID Generation
    # ========================================
    print("\n[1] Node ID Generation...")
    
    node_id1 = generate_node_id()
    node_id2 = generate_node_id()
    node_id3 = generate_node_id(b"deterministic-seed")
    
    print(f"  Random 1: {node_id1[:16]}...")
    print(f"  Random 2: {node_id2[:16]}...")
    print(f"  Seeded:   {node_id3[:16]}...")
    
    # ========================================
    # 2. XOR Distance
    # ========================================
    print("\n[2] XOR Distance...")
    
    dist1 = xor_distance(node_id1, node_id2)
    dist2 = xor_distance(node_id1, node_id3)
    
    print(f"  Node1 <-> Node2: {dist1}")
    print(f"  Node1 <-> Node3: {dist2}")
    print(f"  Closer: Node{'2' if dist1 < dist2 else '3'}")
    
    # ========================================
    # 3. Routing Table
    # ========================================
    print("\n[3] Routing Table...")
    
    table = RoutingTable(node_id1)
    
    # Add contacts
    contacts = [
        NodeInfo(generate_node_id(), "192.168.1.1", 8000),
        NodeInfo(generate_node_id(), "192.168.1.2", 8000),
        NodeInfo(generate_node_id(), "192.168.1.3", 8000),
    ]
    
    for contact in contacts:
        table.add_contact(contact)
    
    print(f"  Contacts: {table.contact_count()}")
    
    # Find closest
    target = generate_node_id()
    closest = table.get_closest(target, 2)
    print(f"  Closest to target: {len(closest)} nodes")
    
    # ========================================
    # 4. Local Storage
    # ========================================
    print("\n[4] Local Storage...")
    
    storage = DHTStorage(max_age=3600)
    
    storage.store("key1", {"data": "value1"})
    storage.store("key2", {"data": "value2"})
    
    print(f"  Stored: {len(storage)} items")
    
    value = storage.get("key1")
    print(f"  key1: {value}")
    
    missing = storage.get("key999")
    print(f"  key999: {missing}")
    
    # ========================================
    # 5. DHT Node
    # ========================================
    print("\n[5] DHT Node...")
    
    node = DHTNode(host="127.0.0.1", port=8468)
    
    print(f"  Node ID: {node.node_id[:16]}...")
    print(f"  Address: {node.host}:{node.port}")
    
    # Stats
    stats = node.get_stats()
    print(f"  Contacts: {stats['contacts']}")
    print(f"  Stored: {stats['stored_values']}")
    
    # ========================================
    # 6. Async Operations
    # ========================================
    print("\n[6] Async Operations...")
    
    async def async_demo():
        # Store and retrieve
        await node.store("test-key", {"hello": "world"})
        value = await node.get("test-key")
        print(f"  Stored and retrieved: {value}")
        
        # Bootstrap
        bootstrap_nodes = [
            NodeInfo(generate_node_id(), "10.0.0.1", 8000),
            NodeInfo(generate_node_id(), "10.0.0.2", 8000),
        ]
        added = await node.bootstrap(bootstrap_nodes)
        print(f"  Bootstrapped: {added} nodes")
    
    asyncio.run(async_demo())
    
    # ========================================
    # 7. DID Resolution
    # ========================================
    print("\n[7] DID Resolution...")
    
    async def did_demo():
        resolver = DIDResolver(node)
        
        # Publish DID document
        did = "did:talos:" + "a" * 32
        doc = {"id": did, "verificationMethod": []}
        
        await resolver.publish(did, doc)
        print(f"  Published: {did[:30]}...")
        
        # Resolve
        resolved = await resolver.resolve(did)
        print(f"  Resolved: {resolved is not None}")
    
    asyncio.run(did_demo())
    
    print("\n" + "=" * 50)
    print("Example 6 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
