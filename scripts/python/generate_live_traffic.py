
import json
import time
import uuid
import hashlib
import urllib.request
import urllib.error
import random
import sys
from datetime import datetime, timezone

import os

AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:8001/events")

def uuid7_str():
    # Simple UUIDv7 implementation for testing
    # 48 bits timestamp (ms), 12 bits ver/rand, 62 bits rand
    t = int(time.time() * 1000)
    # 0x7 = version 7
    # Data structure: 
    # unix_ts_ms (48 bits) | ver (4 bits) | rand_a (12 bits) | var (2 bits) | rand_b (62 bits)
    
    # We can use uuid library if available? Python 3.13 has uuid7 but we are likely on older.
    # Let's just mock it or try to overlap standard uuid4
    
    # Actually, we can just fake it well enough for the regex: ^[0-9a-f]{8,}_[0-9a-f-]+$
    # Wait, that regex was for CURSOR in the service. The service likely accepts standard UUIDs for event_ids.
    # The error "event_id is not uuidv7" implies validation strongly prefers it.
    
    # Let's try to make a compliant v7 string
    rand_a = random.getrandbits(12)
    rand_b = random.getrandbits(62)
    
    u_int = (t << 80) | (7 << 76) | (rand_a << 64) | (2 << 62) | rand_b
    return str(uuid.UUID(int=u_int))

def calculate_event_hash(event_data):
    # Sort keys, no spaces after separators
    # Canonical string representation for hashing (RFC 8785)
    # The validation logic in service:
    # return json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    
    # We must exclude event_hash from the calculation
    clean = {k: v for k, v in event_data.items() if k != "event_hash"}
    
    canonical_str = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

def generate_random_event():
    # Use integer seconds for dashboard cursor compatibility
    now_ts = int(time.time())
    ts = datetime.fromtimestamp(now_ts, timezone.utc).isoformat().replace("+00:00", "Z")
    event_id = uuid7_str()
    
    outcomes = ["OK", "DENY", "ERROR"]
    outcome = random.choices(outcomes, weights=[0.8, 0.15, 0.05])[0]
    
    event = {
        "schema_id": "talos.audit_event",
        "schema_version": "v1",
        "event_id": event_id,
        "ts": ts,
        "request_id": str(uuid.uuid4()),
        "surface_id": "gateway",
        "outcome": outcome,
        "principal": {
            "agent_id": f"did:talos:agent-{random.randint(1,5)}",
            "peer_id": f"10.0.0.{random.randint(1,255)}"
        },
        "http": {
            "method": random.choice(["POST", "GET", "PUT", "DELETE"]),
            "path": f"/api/resources/{random.randint(100,999)}",
            "status_code": 200 if outcome == "OK" else (403 if outcome == "DENY" else 500)
        },
        "meta": {
            "origin": "test-script",
            "environment": "dev"
        },
        "resource": {
            "type": "database",
            "id": f"db-{random.randint(1,10)}"
        }
    }
    
    # Add denial reason if DENY
    if outcome == "DENY":
        event["meta"]["denial_reason"] = random.choice(["NO_CAPABILITY", "INVALID_TOKEN", "RATE_LIMIT"])
    
    # Compute hash
    clean = {k: v for k, v in event.items() if k != "event_hash" and k != "hashes"}
    canonical_str = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    event_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    
    event["event_hash"] = event_hash
    event["hashes"] = {
        "event_hash": event_hash,
        "capability_hash": f"sha256:{hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]}",
        "request_hash": f"sha256:{hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]}"
    }
    
    return event

def send_event(event):
    data = json.dumps(event).encode('utf-8')
    req = urllib.request.Request(AUDIT_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status
    except urllib.error.HTTPError as e:
        print(f"Failed to send event: {e.code} - {e.read().decode('utf-8')}")
        return e.code
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return 0

def main():
    print(f"Generating live traffic to {AUDIT_URL}...")
    
    for i in range(25):
        event = generate_random_event()
        status = send_event(event)
        
        symbol = "✅" if status == 200 else "❌"
        print(f"{symbol} [{i+1}/25] {event['http']['method']} {event['http']['path']} -> {event['outcome']}")
        
        time.sleep(0.2)
        
    print("\nDone. Traffic generation complete.")

if __name__ == "__main__":
    main()
