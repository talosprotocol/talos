#!/usr/bin/env python3
import sys
import json
import logging
import requests

# Implementation of a Standard MCP Server for Ollama
# This script has NO dependencies on Talos. It is a pure MCP implementation.

OLLAMA_BASE = "http://localhost:11434"

def list_models():
    """Fetch available models from Ollama."""
    try:
        res = requests.get(f"{OLLAMA_BASE}/api/tags")
        if res.status_code == 200:
            data = res.json()
            return [model["name"] for model in data.get("models", [])]
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
        res = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload)
        if res.status_code == 200:
            return res.json().get("message", {}).get("content", "")
        else:
            return f"Error: Ollama API returned {res.status_code}"
    except Exception as e:
        return f"Error connecting to Ollama: {e}"

def handle_request(line):
    try:
        req = json.loads(line)
        msg_id = req.get("id")
        method = req.get("method")
        
        # 1. Initialize (Handshake)
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {},
                    "serverInfo": {"name": "OllamaMCP", "version": "1.0"}
                }
            }
            
        # 2. Tool Discovery
        if method == "tools/list":
             return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "list_models",
                            "description": "List available Ollama models",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "chat",
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
        if method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            
            result_content = ""
            
            if name == "list_models":
                models = list_models()
                result_content = json.dumps(models)
                
            elif name == "chat":
                answer = chat(
                    model=args.get("model"),
                    messages=args.get("messages"),
                    system=args.get("system"),
                    temperature=args.get("temperature", 0.7)
                )
                result_content = answer
            
            else:
                 return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Tool '{name}' not found"}
                }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": [{"type": "text", "text": result_content}]}
            }
            
        return None
        
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}

def main():
    logging.basicConfig(level=logging.ERROR)
    # Stdio Loop
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            response = handle_request(line)
            if response:
                print(json.dumps(response), flush=True)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
