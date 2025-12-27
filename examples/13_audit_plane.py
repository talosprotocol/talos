#!/usr/bin/env python3
"""
Example 13: Audit Plane

This example demonstrates the Phase 3 audit aggregation system:
- Recording authorization events
- Recording revocations
- Querying audit history
- Exporting to JSON and CSV
"""


from src.core.audit_plane import (
    AuditAggregator,
    AuditEventType,
    InMemoryAuditStore,
)


def main():
    print("=" * 50)
    print("Example 13: Audit Plane")
    print("=" * 50)
    
    # Create aggregator
    print("\n[1] Creating AuditAggregator...")
    store = InMemoryAuditStore(max_events=1000)
    agg = AuditAggregator(store=store)
    print("  Using InMemoryAuditStore (1000 event capacity)")
    
    # Record authorization events
    print("\n[2] Recording Events...")
    
    # Successful authorization
    event1 = agg.record_authorization(
        agent_id="did:talos:agent1",
        tool="filesystem",
        method="read",
        capability_id="cap_123456",
        allowed=True,
        latency_us=42,
    )
    print(f"  ✓ Authorization: {event1.event_id}")
    
    # Denial
    event2 = agg.record_authorization(
        agent_id="did:talos:agent2",
        tool="admin",
        method="delete",
        capability_id=None,
        allowed=False,
        denial_reason="NO_CAPABILITY",
    )
    print(f"  ✗ Denial: {event2.event_id}")
    
    # Revocation
    event3 = agg.record_revocation(
        agent_id="did:talos:issuer",
        capability_id="cap_789abc",
        reason="session ended",
    )
    print(f"  ⊘ Revocation: {event3.event_id}")
    
    # Query events
    print("\n[3] Querying Events...")
    
    all_events = agg.query(limit=10)
    print(f"  Total events: {len(all_events)}")
    
    denials = agg.query(event_type=AuditEventType.DENIAL)
    print(f"  Denial events: {len(denials)}")
    
    agent1_events = agg.query(agent_id="did:talos:agent1")
    print(f"  Agent1 events: {len(agent1_events)}")
    
    # Statistics
    print("\n[4] Statistics...")
    stats = agg.get_stats()
    print(f"  Total: {stats['total_events']}")
    print(f"  Denials: {stats['denial_count']}")
    print(f"  Approval rate: {stats['approval_rate']:.0%}")
    
    # Export JSON
    print("\n[5] JSON Export...")
    json_export = agg.export_json()
    print(f"  JSON length: {len(json_export)} chars")
    print(f"  Preview: {json_export[:80]}...")
    
    # Export CSV
    print("\n[6] CSV Export...")
    csv_export = agg.export_csv()
    lines = csv_export.split("\n")
    print(f"  CSV rows: {len(lines)}")
    print(f"  Header: {lines[0][:60]}...")
    
    print("\n" + "=" * 50)
    print("Example 13 Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
