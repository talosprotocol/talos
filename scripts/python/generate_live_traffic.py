import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from typing import Any

AUDIT_URL = os.getenv("AUDIT_URL", "http://localhost:8001/events")
if not AUDIT_URL.startswith(("http://", "https://")):
    raise ValueError(f"Invalid AUDIT_URL scheme: {AUDIT_URL}")


def uuid7_str() -> str:
    """Mocking a compliant UUIDv7 string for testing."""
    t = int(time.time() * 1000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    u_int = (t << 80) | (7 << 76) | (rand_a << 64) | (2 << 62) | rand_b
    return str(uuid.UUID(int=u_int))


def calculate_event_hash(event_data: dict[str, Any]) -> str:
    """Canonical string representation for hashing (RFC 8785)."""
    clean = {k: v for k, v in event_data.items() if k != "event_hash"}

    canonical_str = json.dumps(
        clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def generate_random_event() -> dict[str, Any]:
    """Generate a mock audit event."""
    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    event_id = uuid7_str()

    outcomes = ["OK", "DENY", "ERROR"]
    outcome = secrets.choice(outcomes)

    event: dict[str, Any] = {
        "schema_id": "talos.audit_event",
        "schema_version": "v1",
        "event_id": event_id,
        "ts": ts,
        "request_id": str(uuid.uuid4()),
        "surface_id": "gateway",
        "outcome": outcome,
        "principal": {
            "agent_id": f"did:talos:agent-{secrets.randbelow(5) + 1}",
            "peer_id": f"10.0.0.{secrets.randbelow(255) + 1}",
        },
        "http": {
            "method": secrets.choice(["POST", "GET", "PUT", "DELETE"]),
            "path": f"/api/resources/{secrets.randbelow(900) + 100}",
            "status_code": (
                200 if outcome == "OK" else (403 if outcome == "DENY" else 500)
            ),
        },
        "meta": {"origin": "test-script", "environment": "dev"},
        "resource": {"type": "database", "id": f"db-{secrets.randbelow(10) + 1}"},
    }

    # Add denial reason if DENY
    if outcome == "DENY":
        event["meta"]["denial_reason"] = secrets.choice(
            ["NO_CAPABILITY", "INVALID_TOKEN", "RATE_LIMIT"]
        )

    # Compute hash
    clean = {k: v for k, v in event.items() if k != "event_hash" and k != "hashes"}
    canonical_str = json.dumps(
        clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    event_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    event["event_hash"] = event_hash
    event["hashes"] = {
        "event_hash": event_hash,
        "capability_hash": f"sha256:{secrets.token_hex(8)}",
        "request_hash": f"sha256:{secrets.token_hex(8)}",
    }

    return event


def send_event(event: dict[str, Any]) -> int:
    data = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        AUDIT_URL, data=data, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:  # nosec B310
            res_status = response.status
            return int(res_status) if res_status is not None else 0
    except urllib.error.HTTPError as e:
        print(f"Failed to send event: {e.code} - {e.read().decode('utf-8')}")
        return e.code
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return 0


def main() -> None:
    print(f"Generating live traffic to {AUDIT_URL}...")

    for i in range(25):
        event = generate_random_event()
        status = send_event(event)

        symbol = "✅" if status == 200 else "❌"
        print(
            f"{symbol} [{i+1}/25] {event['http']['method']} "
            f"{event['http']['path']} -> {event['outcome']}"
        )

        time.sleep(0.2)

    print("\nDone. Traffic generation complete.")


if __name__ == "__main__":
    main()
