import subprocess
import time
import sys
import os
import shutil
import re
import json
import pytest
import requests
from pathlib import Path

# Config
PYTHON = sys.executable
ROOT = Path(os.getcwd())

@pytest.fixture(scope="module")
def env():
    env = os.environ.copy()
    # Ensure all workspace packages are discoverable
    env["PYTHONPATH"] = f"{ROOT}:{ROOT}/sdks/python/src:{ROOT}/contracts/python"
    env["DEV_MODE"] = "true"
    env["TALOS_DEV_MODE"] = "true"
    env["STORAGE_TYPE"] = "memory"
    env["TALOS_STORAGE_TYPE"] = "memory"
    env["TALOS_AUDIT_URL"] = "http://127.0.0.1:18002"
    env["AUDIT_URL"] = "http://127.0.0.1:18002"
    return env

class LiveProcess:
    def __init__(self, name, cmd, env, cwd=None, wait_pattern=None, timeout=20):
        self.name = name
        self.cmd = cmd
        self.env = env
        self.cwd = cwd
        self.process = None
        self.wait_pattern = wait_pattern
        self.timeout = timeout
        self.output = []

    def start(self):
        print(f"[{self.name}] Starting in {self.cwd or '.'}...")
        self.process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=self.env,
            cwd=self.cwd,
            bufsize=1,
            universal_newlines=True
        )
        
        if self.wait_pattern:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.output.append(line)
                # print(f"[{self.name}] {line.strip()}")
                if re.search(self.wait_pattern, line):
                    print(f"[{self.name}] ✅ Started and ready")
                    # Start a thread to keep reading output so it doesn't block
                    import threading
                    def reader():
                        for l in self.process.stdout:
                            self.output.append(l)
                    threading.Thread(target=reader, daemon=True).start()
                    return
            # If we timed out, print what we got so far
            print(f"[{self.name}] ❌ Startup failed. Pattern '{self.wait_pattern}' not found.")
            print("".join(self.output[-20:]))
            self.stop()
            raise TimeoutError(f"[{self.name}] Failed to start within {self.timeout}s")

    def stop(self):
        if self.process:
            print(f"[{self.name}] Stopping...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

@pytest.mark.live
def test_gateway_audit_integration(env):
    # 1. Start Audit Service
    audit_service = LiveProcess(
        "AUDIT",
        [PYTHON, "-m", "uvicorn", "src.adapters.http.main:app", "--port", "18002", "--host", "127.0.0.1"],
        env,
        cwd=ROOT / "services/audit",
        wait_pattern=r"Uvicorn running on http://127.0.0.1:18002"
    )
    
    # 2. Start Gateway
    gateway = LiveProcess(
        "GATEWAY",
        [PYTHON, "-m", "uvicorn", "main:app", "--port", "18001", "--host", "127.0.0.1"],
        env,
        cwd=ROOT / "services/gateway",
        wait_pattern=r"Uvicorn running on http://127.0.0.1:18001"
    )
    
    try:
        audit_service.start()
        gateway.start()
        
        # 3. Post an event to the Gateway
        event_data = {
            "event_type": "LIVE_TEST_EVENT",
            "actor": "test-runner",
            "action": "execute-live-test",
            "resource": "talos-stack",
            "metadata": {"test_id": "12345"}
        }
        
        print("Posting event to gateway...")
        try:
            resp = requests.post("http://127.0.0.1:18001/api/events", json=event_data, timeout=10)
            if resp.status_code != 200:
                print(f"Gateway Error {resp.status_code}: {resp.text}")
                print("Gateway Logs:")
                print("".join(gateway.output[-50:]))
                print("Audit Logs:")
                print("".join(audit_service.output[-50:]))
            assert resp.status_code == 200
        except Exception as e:
            print(f"Post failed: {e}")
            raise
            
        result = resp.json()
        assert result["event_type"] == "LIVE_TEST_EVENT"
        print("✅ Event accepted by Gateway")
        
        # 4. Verify the event in Audit Service
        print("Querying Audit Service...")
        time.sleep(2) # Wait for forwarding
        
        resp_audit = requests.get("http://127.0.0.1:18002/api/events", params={"limit": 10}, timeout=10)
        assert resp_audit.status_code == 200
        events = resp_audit.json().get("items", [])
        
        found = False
        for e in events:
            # Check nested metadata or flat
            metadata = e.get("metadata") or e.get("meta") or {}
            if metadata.get("event_type") == "LIVE_TEST_EVENT":
                found = True
                break
        
        assert found, f"Event not found in Audit Service. Events: {json.dumps(events, indent=2)}"
        print("✅ Event found in Audit Service!")

    finally:
        gateway.stop()
        audit_service.stop()
