import requests
import time
import random
import sys

BASE_URL = "http://localhost:8000"

def generate_traffic():
    print(f"Starting traffic generation to {BASE_URL}...")
    headers = {"X-Talos-Key-ID": "test-user-1"}
    
    success = 0
    errors = 0
    
    while True:
        try:
            # 1. Health check (bypass RL, not audited usually)
            try:
                requests.get(f"{BASE_URL}/health", timeout=1)
            except:
                pass
            
            # 2. Public endpoint (RL applies)
            # /v1/models is standard LLM endpoint
            try:
                res = requests.get(f"{BASE_URL}/v1/models", headers=headers, timeout=2)
                if res.status_code < 500:
                    print(f".", end="", flush=True)
                    success += 1
                else:
                    print(f"!({res.status_code})", end="", flush=True)
                    errors += 1
            except Exception as e:
                print("E", end="", flush=True)
                errors += 1

            # 3. Simulate access request (Audited)
            # /v1/mcp/servers triggers auth/audit
            try:
                res = requests.get(f"{BASE_URL}/v1/mcp/servers", headers=headers, timeout=2)
                if res.status_code < 500:
                    pass
            except:
                pass

        except KeyboardInterrupt:
            print("\nStopping.")
            sys.exit(0)
        except Exception as e:
            print(f"\nCritical Error: {e}")
            time.sleep(1)
        
        # Add some randomness suitable for dashboard viz
        time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    generate_traffic()
