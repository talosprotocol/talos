import requests
import time
import random

BASE_URL = "http://localhost:8080"

def generate_traffic():
    print(f"Starting traffic generation to {BASE_URL}...")
    while True:
        try:
            payload = {
                "event_type": "access_request",
                "actor": f"user_{random.randint(1, 5)}",
                "action": "login",
                "resource": "dashboard",
                "metadata": {"ip": "127.0.0.1"}
            }
            res = requests.post(f"{BASE_URL}/api/events", json=payload)
            if res.status_code == 200:
                print(".", end="", flush=True)
            else:
                print(f"!({res.status_code}: {res.text})", end="", flush=True)
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    generate_traffic()
