"""Verification script for PR-3 changes."""

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

URL_BASE = "http://127.0.0.1:8001/api/config"


def request(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | str, str | None]:
    """Perform an HTTP request and ensure correct headers."""
    if headers is None:
        headers = {}
    if data:
        json_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        json_data = None

    req = urllib.request.Request(
        f"{URL_BASE}{endpoint}", data=json_data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req) as f:  # nosec B310
            return f.status, json.load(f), f.getheader("Content-Type")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body), None
        except (ValueError, KeyError, json.JSONDecodeError):
            return e.code, body, None


def run_test() -> None:
    """Run verification tests."""
    print("--- PR-3 Verification ---")

    # 1. Create Draft
    print("\n1. Create Draft")
    idem_key = str(uuid.uuid4())
    payload = {
        "config": {
            "config_version": "1.0",
            "global": {"env": "prod"},
            "extensions": {"password": os.getenv("TEST_PASSWORD", "secret_v1")},
        },
        "note": "Initial version",
    }

    status, body, _ = request(
        "POST",
        "/drafts",
        payload,
        {"Idempotency-Key": idem_key, "X-Talos-Principal-Id": "user-1"},
    )
    print(f"Status: {status}")
    if status != 200:
        print(f"Failed: {body}")
        return

    if not isinstance(body, dict):
        print(f"Failed: Unexpected body type {type(body)}")
        return

    draft_id = body["draft_id"]
    # body["config_digest"]  # Removed useless statement
    print(f"Draft ID: {draft_id}")

    # 2. Idempotency Check (Replay)
    print("\n2. Replay Draft (Idempotency)")
    status2, body2, _ = request(
        "POST",
        "/drafts",
        payload,
        {"Idempotency-Key": idem_key, "X-Talos-Principal-Id": "user-1"},
    )
    print(f"Status: {status2}")
    if status2 == 200 and isinstance(body2, dict) and body2.get("draft_id") == draft_id:
        print("✅ Idempotency Works (Same ID returned)")
    else:
        print("❌ Idempotency Failed")

    # 3. Publish
    print("\n3. Publish Draft")
    pub_key = str(uuid.uuid4())
    status3, body3, _ = request(
        "POST",
        "/publish",
        {"draft_id": draft_id},
        {"Idempotency-Key": pub_key, "X-Talos-Principal-Id": "admin-1"},
    )
    print(f"Status: {status3}")
    if status3 == 200:
        print("✅ Published")
    else:
        print(f"❌ Publish Failed: {body3}")

    # 4. History & Redaction
    print("\n4. List History")
    status4, body4, _ = request("GET", "/history?limit=10")
    print(f"Status: {status4}")
    items = body4.get("items", []) if isinstance(body4, dict) else []
    if len(items) > 0:
        latest = items[0]
        ext = latest["redacted_config"]["extensions"]
        print(f"History Item 0 Redaction: {ext.get('password')}")
        if ext.get("password") == "***":
            print("✅ History Redacted")
        else:
            print("❌ History Leak")
    else:
        print("❌ History Empty")

    # 5. Export
    print("\n5. Export YAML (Redacted)")
    status5, body5, _ = request("POST", "/export", {"format": "yaml"})
    print(f"Status: {status5}")
    if status5 == 200 and isinstance(body5, dict):
        content = body5["content"]
        print("Content Snippet:")
        print(content[:100])
        if "***" in content:
            print("✅ Export Redacted")
        else:
            print("❌ Export Leak / No Secret")
    else:
        print(f"❌ Export Failed: {body5}")


if __name__ == "__main__":
    time.sleep(2)
    run_test()
