#!/usr/bin/env python3
import sys
import json
import logging

# Simple In-Memory Database
DB = {
    "users": [
        {"id": 1, "name": "Alice", "role": "engineer"},
        {"id": 2, "name": "Bob", "role": "manager"}
    ],
    "logs": [
        {"id": 101, "msg": "System start"},
        {"id": 102, "msg": "Connection established"}
    ]
}

def handle_request(line):
    try:
        req = json.loads(line)
        msg_id = req.get("id")
        method = req.get("method")
        
        # Respond to initialize (Handshake)
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {},
                    "serverInfo": {"name": "MockDB", "version": "1.0"}
                }
            }
            
        # Tool Call: query_db
        if method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            
            if name == "query_db":
                table = args.get("table")
                if table in DB:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(DB[table])}]}
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32602, "message": f"Table '{table}' not found"}
                    }
                    
        # List Tools
        if method == "tools/list":
             return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [{
                        "name": "query_db",
                        "description": "Query the in-memory database",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "table": {"type": "string", "enum": ["users", "logs"]}
                            },
                            "required": ["table"]
                        }
                    }]
                }
            }
            
        return None
        
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}

def main():
    logging.basicConfig(level=logging.ERROR)
    # Read from stdin, write to stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            response = handle_request(line)
            if response:
                print(json.dumps(response))
                sys.stdout.flush()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
