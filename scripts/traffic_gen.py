import requests
import time
import random

API_URL = "http://localhost:8000"

def generate_traffic():
    print(f"Starting traffic generation to {API_URL}...")
    while True:
        try:
            res = requests.post(f"{API_URL}/api/demo/generate")
            if res.status_code == 200:
                print(".", end="", flush=True)
            else:
                print("!", end="", flush=True)
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    generate_traffic()
