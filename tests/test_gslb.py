import shutil

import pytest
import requests
import time
import subprocess

BASE_URL = "http://localhost:8080"


def _require_ingress() -> None:
    try:
        requests.get(f"{BASE_URL}/healthz", timeout=1.0)
    except requests.RequestException as exc:
        pytest.skip(f"local ingress unavailable: {exc}")


def _require_docker() -> None:
    if shutil.which("docker") is None:
        pytest.skip("docker not available for failover integration test")

def test_health_check():
    """Verify Ingress handles basic traffic."""
    _require_ingress()
    print("Testing Ingress Connectivity...")
    res = requests.get(f"{BASE_URL}/healthz")
    assert res.status_code == 200
    data = res.json()
    print(f"✅ Ingress UP. Region: {data.get('region')}")
    return data.get('region')

def test_geo_routing():
    """Verify Header-based Geo Routing."""
    _require_ingress()
    print("\nTesting Geo Routing (EU)...")
    headers = {"X-Talos-Sim": "1", "X-Geo-Country": "EU"}
    res = requests.get(f"{BASE_URL}/healthz", headers=headers)
    assert res.status_code == 200
    data = res.json()
    region = data.get('region')
    if region == "eu":
        print("✅ Geo-Routing Success: Routed to EU")
    else:
        pytest.fail(f"Geo-routing routed to {region!r} instead of 'eu'")

def test_failover():
    """Verify Failover from US to EU."""
    _require_ingress()
    _require_docker()
    print("\nTesting Failover (US Hard Down)...")
    try:
        # Stop US
        subprocess.run(["docker", "stop", "talos-gateway-us"], check=True)
        time.sleep(5) # Allow health checks to fail
        
        start_time = time.time()
        success = False
        
        print("Polling for failover (timeout=30s)...")
        while time.time() - start_time < 30:
            try:
                # Should route to EU (Priority 1)
                res = requests.get(f"{BASE_URL}/healthz", timeout=2)
                if res.status_code == 200:
                    data = res.json()
                    region = data.get('region')
                    if region in ["eu", "asia"]:
                        print(f"✅ Failover Success: Routed to {region}")
                        success = True
                        break
            except Exception:
                pass
            time.sleep(2)
            
        if not success:
            pytest.fail("Traffic did not shift to EU/ASIA within 30s")
    finally:
        # Restore
        subprocess.run(["docker", "start", "talos-gateway-us"], check=True)
        print("Restored US Gateway.")

if __name__ == "__main__":
    current_region = test_health_check()
    test_geo_routing()
    # Only run failover if default is US, otherwise it's confusing
    if current_region == "us":
        test_failover()
    else:
        print("Skipping failover test (Default primary is not US)")
