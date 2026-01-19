#!/usr/bin/env python3
"""
Talos Audit Event Generator - Generate realistic test data

Creates diverse audit events with:
- Various outcomes: ALLOWED, DENIED, FLAGGED, REDACTED
- Different principals (users, services, agents)
- Multiple resource types
- Timestamps spread over time
- Realistic patterns and occasional errors
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict

AUDIT_URL = "http://localhost:8001"

# Sample data for realistic events
PRINCIPALS = [
    "user:alice@talosprotocol.com",
    "user:bob@talosprotocol.com",
    "service:ai-chat-agent",
    "service:mcp-connector",
    "agent:governance-001",
    "user:eve@external.com",  # External user for denials
]

RESOURCES = [
    "document:contracts/nda-2024.pdf",
    "api:gateway/admin/secrets",
    "model:gpt-4",
    "database:users",
    "api:mcp/resources",
    "secret:api-key-production",
    "deployment:kubernetes/prod",
]

ACTIONS = [
    "read",
    "write",
    "execute",
    "delete",
    "list",
    "update",
]

OUTCOMES = {
    "ALLOWED": 0.60,  # 60% allowed
    "DENIED": 0.25,   # 25% denied
    "FLAGGED": 0.10,  # 10% flagged
    "REDACTED": 0.05, # 5% redacted
}

DENY_REASONS = [
    "Insufficient permissions",
    "Resource not found",
    "Rate limit exceeded",
    "Invalid authentication token",
    "External domain not allowed",
]

def weighted_choice(choices: Dict[str, float]) -> str:
    """Select item based on weights"""
    items = list(choices.keys())
    weights = list(choices.values())
    return random.choices(items, weights=weights)[0]

def generate_event(timestamp: datetime) -> Dict:
    """Generate a single realistic audit event"""
    import uuid_utils as uuid
    
    principal = random.choice(PRINCIPALS)
    resource = random.choice(RESOURCES)
    action = random.choice(ACTIONS)
    outcome = weighted_choice(OUTCOMES)
    
    # Build event with required fields
    event = {
        "event_id": str(uuid.uuid7()),  # Required field
        "principal": principal,
        "resource": resource,
        "action": action,
        "outcome": outcome,
        "timestamp": timestamp.isoformat() + "Z",
        "context": {
            "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": random.choice([
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "TalosSDK/1.0 Python/3.11",
                "curl/7.84.0",
            ])
        }
    }
    
    # Add reason for denials
    if outcome == "DENIED":
        event["reason"] = random.choice(DENY_REASONS)
    
    # Add redaction info
    if outcome == "REDACTED":
        event["redacted_fields"] = ["context.ip_address"]
    
    # Add flag reason
    if outcome == "FLAGGED":
        event["flag_reason"] = "Unusual access pattern detected"
    
    return event

def send_event(event: Dict) -> bool:
    """Send event to audit service"""
    try:
        response = requests.post(
            f"{AUDIT_URL}/events",
            json=event,
            timeout=5
        )
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"  ✗ Failed: {response.status_code} - {response.text[:100]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error: {e}")
        return False

def generate_historical_events(count: int = 100):
    """Generate historical events spread over past 7 days"""
    print(f"\n📊 Generating {count} historical audit events...")
    print(f"Target: {AUDIT_URL}")
    
    # Check if service is available
    try:
        health = requests.get(f"{AUDIT_URL}/health",timeout=2)
        print(f"✓ Audit service healthy: {health.json()}")
    except:
        print(f"✗ Audit service not available at {AUDIT_URL}")
        print("  Start it with: cd services/audit && PYTHONPATH=../../sdks/python/src uvicorn src.adapters.http.main:app --port 8001")
        return
    
    # Generate events
    now = datetime.utcnow()
    success = 0
    failed = 0
    
    for i in range(count):
        # Spread events over last 7 days
        hours_ago = random.randint(0, 7 * 24)
        timestamp = now - timedelta(hours=hours_ago)
        
        event = generate_event(timestamp)
        
        if send_event(event):
            success += 1
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{count}")
        else:
            failed += 1
        
        # Small delay to avoid overwhelming the service
        time.sleep(0.05)
    
    print(f"\n✓ Generation complete!")
    print(f"  Success: {success}/{count}")
    print(f"  Failed: {failed}/{count}")
    
    # Show distribution
    print(f"\n📈 Expected distribution:")
    for outcome, weight in OUTCOMES.items():
        expected = int(count * weight)
        print(f"  {outcome}: ~{expected} events ({int(weight*100)}%)")

def generate_realtime_stream(duration_seconds: int = 60):
    """Generate events in real-time for testing SSE"""
    print(f"\n🔄 Generating real-time events for {duration_seconds} seconds...")
    print(f"Watch SSE stream at: http://localhost:3000/audit")
    
    end_time = time.time() + duration_seconds
    count = 0
    
    while time.time() < end_time:
        event = generate_event(datetime.utcnow())
        if send_event(event):
            count += 1
            print(f"  Sent event #{count}: {event['outcome']} - {event['principal']}")
        
        # Random delay between 1-5 seconds
        time.sleep(random.uniform(1, 5))
    
    print(f"\n✓ Generated {count} real-time events")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "realtime":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            generate_realtime_stream(duration)
        elif mode == "historical":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            generate_historical_events(count)
        else:
            print("Usage:")
            print("  python3 generate_audit_data.py historical [count]")
            print("  python3 generate_audit_data.py realtime [seconds]")
    else:
        # Default: generate 100 historical events
        generate_historical_events(100)
