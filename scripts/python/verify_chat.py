import requests
import json
import uuid
import sys

BASE_URL = "http://localhost:8080"
SESSION_ID = f"sess_{str(uuid.uuid4())[:8]}"

def test_chat():
    print(f"Testing Chat Flow with Session: {SESSION_ID}")
    
    payload = {
        "session_id": SESSION_ID,
        "model": "llama3.2:latest",
        "messages": [
            {"role": "user", "content": "Hello, are you online?"}
        ],
        "capability": "cap_valid_demo_token", # Mocked valid capability in Gateway
        "client_request_id": str(uuid.uuid4())
    }
    
    try:
        print(f"Sending POST to {BASE_URL}/mcp/tools/chat...")
        resp = requests.post(f"{BASE_URL}/mcp/tools/chat", json=payload, timeout=60)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Response:", json.dumps(data, indent=2))
            
            if data.get("messages"):
                print("✅ Chat Success!")
                return True
            else:
                print("❌ Chat response format invalid or empty")
                return False
        else:
            print("❌ Chat Failed")
            print(resp.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_chat()
    sys.exit(0 if success else 1)
