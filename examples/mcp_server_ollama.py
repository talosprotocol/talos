#!/usr/bin/env python3
import sys
import json
import logging
import requests
import hashlib
import time

# Implementation of a Standard MCP Server for Ollama
# Enforces Talos Invariants:
# 1. Namespace: ollama.*
# 2. Audit: Computes SHA256 of request/response (Privacy: No raw prompts logged)
# 3. Error Codes: Maps upstream failures to standardized errors

OLLAMA_BASE = "http://localhost:11434"

# Configure logging to stderr to avoid interfering with stdout JSON-RPC
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', stream=sys.stderr)

def calculate_hash(data):
    """Compute SHA256 hash of canonical JSON representation."""
    try:
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
    except Exception:
        return "hash_error"

def list_models():
    """Fetch available models from Ollama."""
    try:
        res = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return [model["name"] for model in data.get("models", [])]
        logging.error(f"Ollama API returned {res.status_code}")
        return []
    except Exception as e:
        logging.error(f"Failed to fetch models: {e}")
        return []

def chat(model, messages, system=None, temperature=0.7):
    """Chat completion via Ollama."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature}
    }
    if system:
        payload["system"] = system

    try:
        res = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=60)
        if res.status_code == 200:
            return {"content": res.json().get("message", {}).get("content", "")}
        else:
            return {"error": f"Upstream Error: {res.status_code}", "code": "TOOL_UPSTREAM_ERROR"}
    except requests.exceptions.ConnectionError:
        return {"error": "Ollama Unreachable", "code": "TOOL_UPSTREAM_UNAVAILABLE"}
    except Exception as e:
        return {"error": str(e), "code": "TOOL_INTERNAL_ERROR"}

def handle_request(line):
    try:
        req = json.loads(line)
        msg_id = req.get("id")
        method = req.get("method")
        
        # 0. Audit Binding (Request)
        # We hash the full request parameters to bind this execution
        req_hash = calculate_hash(req.get("params", {}))
        
        response = None

        # 1. Initialize (Handshake)
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {},
                    "serverInfo": {"name": "OllamaMCP", "version": "1.1"}
                }
            }
            
        # 2. Tool Discovery
        elif method == "tools/list":
             response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "ollama.list_models",
                            "description": "List available Ollama models",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "ollama.chat",
                            "description": "Generate a chat completion using an Ollama model",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "model": {"type": "string", "description": "Model name (e.g. llama3)"},
                                    "messages": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                                "content": {"type": "string"}
                                            },
                                            "required": ["role", "content"]
                                        }
                                    },
                                    "system": {"type": "string", "description": "System prompt"},
                                    "temperature": {"type": "number", "description": "Temperature (0.0-1.0)"}
                                },
                                "required": ["model", "messages"]
                            }
                        }
                    ]
                }
            }
            
        # 3. Tool Execution
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            
            result_content = ""
            error_obj = None
            
            if name == "ollama.list_models":
                models = list_models()
                result_content = json.dumps(models)
                
            elif name == "ollama.chat":
                # Execute
                output = chat(
                    model=args.get("model"),
                    messages=args.get("messages"),
                    system=args.get("system"),
                    temperature=args.get("temperature", 0.7)
                )
                
                if "error" in output:
                    error_obj = {"code": -32603, "message": output["error"], "data": {"code": output["code"]}}
                else:
                    result_content = output["content"]
            
            else:
                 error_obj = {"code": -32601, "message": f"Tool '{name}' not found"}

            if error_obj:
                response = {"jsonrpc": "2.0", "id": msg_id, "error": error_obj}
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": result_content}]}
                }
            
        else:
            # Ignore notifications or unknown methods for now
            return None

        # 4. Audit Binding (Response) & Logging
        if response:
            res_hash = calculate_hash(response.get("result", response.get("error")))
            
            # Log structured audit event
            # Note: We do NOT log the full content (privacy), just the hashes and metadata
            audit_entry = {
                "event": "tool_execution",
                "timestamp": time.time(),
                "method": method,
                "tool": req.get("params", {}).get("name"),
                "request_hash": req_hash,
                "response_hash": res_hash,
                "status": "error" if "error" in response else "success"
            }
            logging.info(f"AUDIT_LOG: {json.dumps(audit_entry)}")

        return response
        
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}

def main():
    # Stdio Loop
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            resp = handle_request(line)
            if resp:
                print(json.dumps(resp), flush=True)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
