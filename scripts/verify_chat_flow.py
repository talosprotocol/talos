
import requests
import uuid
import json
import sys
import time

GATEWAY_URL = "http://localhost:8000"

def main():
    print("=" * 60)
    print("TALOS SECURE CHAT VERIFICATION")
    print("=" * 60)

    session_id = str(uuid.uuid4())
    print(f"Session ID: {session_id}")

    payload = {
        "session_id": session_id,
        "model": "llama3.2:latest",
        "messages": [
            {"role": "user", "content": "What is the capital of France? Answer in one word."}
        ],
        "capability": "cap_test_12345", # Required to bypass auth check in Gateway logic
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    print("\n[1] Sending Chat Request to Gateway...")
    print(f"  Target: {GATEWAY_URL}/mcp/tools/chat")
    
    try:
        start_time = time.time()
        res = requests.post(f"{GATEWAY_URL}/mcp/tools/chat", json=payload, timeout=30)
        duration = time.time() - start_time
        
        if res.status_code != 200:
            print(f"  ❌ Error {res.status_code}: {res.text}")
            sys.exit(1)
            
        data = res.json()
        print(f"  ✅ Response received in {duration:.2f}s")
        
        # Parse response
        # Gateway returns mcp_res["result"]
        # which is { messages: [...], ... }
        
        messages = data.get("messages", [])
        if messages:
            answer = messages[0].get("content", "").strip()
            print(f"  🤖 Answer: {answer}")
        else:
            print(f"  ⚠️ No answer message found in response: {data}")

    except Exception as e:
        print(f"  ❌ Connection Failed: {e}")
        sys.exit(1)

    print("\n[2] Flow Verification")
    print("  Check Dashboard Console for:")
    print("  - CHAT_REQUEST_RECEIVED")
    print("  - CHAT_TOOL_CALL")
    print("  - CHAT_TOOL_RESULT")
    print("  - CHAT_RESPONSE_SENT")
    print("=" * 60)

if __name__ == "__main__":
    main()
