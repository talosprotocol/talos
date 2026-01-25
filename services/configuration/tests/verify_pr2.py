
import json
import urllib.request
import urllib.error
import time

def run_test():
    url_base = "http://127.0.0.1:8001/api/config"
    
    # payload
    valid_payload = {
        "config": {
            "config_version": "1.0",
            "global": {"env": "prod"},
            "extensions": {"password": "secret_value"} # Should be redacted
        },
        "strict": True
    }
    
    print("Testing /validate...")
    req = urllib.request.Request(
        f"{url_base}/validate", 
        data=json.dumps(valid_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as f:
            print(f"Validate Status: {f.status}")
            data = json.load(f)
            print(f"Valid: {data['valid']}")
            norm = data['normalized_config']
            ext = norm.get('extensions', {})
            print(f"Redaction Check: password={ext.get('password')}") 
            if ext.get('password') == "***":
                print("✅ Redaction Working")
            else:
                print("❌ Redaction Failed")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed: {e.code} {e.read().decode()}")

    # Test Normalize
    print("\nTesting /normalize...")
    req = urllib.request.Request(
        f"{url_base}/normalize", 
        data=json.dumps(valid_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as f:
            print(f"Normalize Status: {f.status}")
            data = json.load(f)
            digest = data['config_digest']
            print(f"Digest: {digest}")
            if len(digest) == 64:
                 print("✅ Digest looks valid")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed: {e.code} {e.read().decode()}")

if __name__ == "__main__":
    # Wait for server
    time.sleep(2)
    run_test()
