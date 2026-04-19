import json
import requests
import sys
import time
import os
import uuid
from pathlib import Path

def run_collection(file_path):
    with open(file_path, 'r') as f:
        collection = json.load(f)

    variables = {v['key']: v['value'].replace('localhost', '127.0.0.1') for v in collection.get('variable', [])}

    admin_secret = os.getenv("AUTH_ADMIN_SECRET", "dev-admin-secret")
    variables.setdefault("admin_secret", admin_secret)
    variables.setdefault("admin_principal", "dev-admin")
    variables.setdefault("admin_token", "")
    variables.setdefault("admin_token_permissions", "[]")
    variables.setdefault("admin_token_session_id", "")
    variables.setdefault("api_session_token", "")
    variables.setdefault("api_session_permissions", "[]")
    variables.setdefault("api_session_id", "")

    print(f"🚀 Running Postman Collection: {collection['info']['name']}")
    print(f"Base AI Gateway: {variables.get('ai_gateway_url')}")
    print("-" * 60)

    stats = {"passed": 0, "failed": 0, "errors": 0}
    session = requests.Session()

    def substitute(value):
        if not isinstance(value, str):
            return value
        rendered = value
        for var_k, var_v in variables.items():
            rendered = rendered.replace(f"{{{{{var_k}}}}}", var_v)
        rendered = rendered.replace("{{$guid}}", str(uuid.uuid4()))
        return rendered

    def resolve_url(url_spec):
        if isinstance(url_spec, str):
            return substitute(url_spec)
        if isinstance(url_spec, dict):
            if url_spec.get("raw"):
                return substitute(url_spec["raw"])
            protocol = url_spec.get("protocol", "http")
            host = ".".join(url_spec.get("host", []))
            path = "/".join(url_spec.get("path", []))
            query = url_spec.get("query", [])
            query_string = "&".join(f"{q['key']}={q.get('value', '')}" for q in query if not q.get("disabled"))
            url = f"{protocol}://{host}"
            if path:
                url = f"{url}/{path}"
            if query_string:
                url = f"{url}?{query_string}"
            return substitute(url)
        raise TypeError(f"Unsupported Postman URL shape: {type(url_spec).__name__}")

    def permission_matches(granted, required):
        if granted in ("*", "*:*"):
            return True
        if granted == required:
            return True
        if granted.endswith(".*") and required.startswith(f"{granted[:-2]}."):
            return True
        if granted.endswith(":*") and required.startswith(f"{granted[:-2]}:"):
            return True
        return False

    def required_admin_permission(url):
        if "/admin/v1/llm/" in url:
            return "llm.read"
        if "/admin/v1/mcp/servers" in url:
            return "mcp.read"
        if "/admin/v1/telemetry/stats" in url or "/admin/v1/audit/stats" in url:
            return "audit.read"
        return None

    def required_api_permission(url, body):
        if "/admin/v1/" in url and "/admin/v1/auth/token" not in url:
            return required_admin_permission(url)
        if "/v1/chat/completions" in url:
            return "llm.invoke"
        if "/v1/models" in url:
            return "llm.read"
        if "/a2a/v1/rpc" in url:
            if isinstance(body, dict):
                method = body.get("method")
                if method in ("SendMessage", "message/send", "tasks.send"):
                    return "a2a.send"
                if method in ("GetTask", "tasks.get"):
                    return "a2a.get"
            return "a2a.send"
        return None

    def process_item(item):
        if 'item' in item:
            print(f"\n📂 Folder: {item['name']}")
            for sub_item in item['item']:
                process_item(sub_item)
            return

        name = item['name']
        request = item['request']
        method = request['method']

        url_raw = resolve_url(request['url'])

        headers = {}
        for h in request.get('header', []):
            headers[h['key']] = substitute(h['value'])

        body_raw = None
        body_json = None
        if 'body' in request and request['body'].get('mode') == 'raw':
            body_raw = substitute(request['body']['raw'])
            
            try:
                body_json = json.loads(body_raw)
                # Ensure it's not double-stringified
                if isinstance(body_json, str):
                    body_json = json.loads(body_json)
            except Exception:
                pass

        if (
            "127.0.0.1:8001" in url_raw
            and "/admin/v1/auth/token" not in url_raw
            and any(path in url_raw for path in ("/admin/v1/", "/v1/", "/a2a/v1/rpc"))
        ):
            auth_header = headers.get("Authorization", "")
            if "{{api_session_token}}" in auth_header or "{{admin_token}}" in auth_header or auth_header == "Bearer ":
                print(f"❌ FAIL ({name}) api_session_token was not populated before protected gateway request")
                stats["failed"] += 1
                return
            required_permission = required_api_permission(url_raw, body_json)
            if required_permission:
                try:
                    token_permissions = json.loads(variables.get("api_session_permissions", "[]"))
                except ValueError:
                    token_permissions = []
                if not any(permission_matches(p, required_permission) for p in token_permissions):
                    print(f"❌ FAIL ({name}) api_session_permissions missing {required_permission}")
                    stats["failed"] += 1
                    return

        print(f"RUNNING: {name} [{method} {url_raw}]", end=" ", flush=True)
        
        try:
            start_time = time.time()
            
            if method == 'GET':
                resp = session.get(url_raw, headers=headers, timeout=10)
            elif method == 'POST':
                if body_json is not None and isinstance(body_json, (dict, list)):
                    # Clear out content-type to let requests set it correctly
                    req_headers = {k: v for k, v in headers.items() if k.lower() != 'content-type'}
                    resp = session.post(url_raw, headers=req_headers, json=body_json, timeout=30)
                else:
                    resp = session.post(url_raw, headers=headers, data=body_raw, timeout=30)
            else:
                print("SKIPPED")
                return

            latency = int((time.time() - start_time) * 1000)
            
            if resp.status_code in (200, 201, 202, 204):
                if "/admin/v1/auth/token" in url_raw:
                    try:
                        token_body = resp.json()
                        token = token_body.get("token", "")
                    except ValueError:
                        token_body = {}
                        token = ""
                    if token:
                        variables["api_session_token"] = token
                        variables["api_session_permissions"] = json.dumps(token_body.get("permissions", []))
                        variables["api_session_id"] = token_body.get("session_id", "")
                        variables["admin_token"] = token
                        variables["admin_token_permissions"] = json.dumps(token_body.get("permissions", []))
                        variables["admin_token_session_id"] = token_body.get("session_id", "")
                        print(f"✅ PASS ({latency}ms, captured api_session_token)")
                        stats["passed"] += 1
                        return
                    print(f"❌ FAIL (Status {resp.status_code}, {latency}ms)")
                    print("   Response did not include token")
                    stats["failed"] += 1
                    return
                print(f"✅ PASS ({latency}ms)")
                stats["passed"] += 1
            else:
                print(f"❌ FAIL (Status {resp.status_code}, {latency}ms)")
                if resp.status_code == 422:
                    try:
                        print(f"   422 Detail: {resp.json().get('detail')}")
                    except:
                        print(f"   Response: {resp.text[:500]}")
                else:
                    print(f"   Response: {resp.text[:500]}")
                stats["failed"] += 1
        except Exception as e:
            print(f"⚠️ ERROR: {str(e)}")
            stats["errors"] += 1

    for item in collection['item']:
        process_item(item)

    print("-" * 60)
    print(f"SUMMARY: {stats['passed']} Passed, {stats['failed']} Failed, {stats['errors']} Errors")
    if stats['failed'] > 0 or stats['errors'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    default_collection = Path(__file__).with_name("talos_postman_collection.json")
    collection_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_collection
    run_collection(collection_path)
