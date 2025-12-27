#!/usr/bin/env python3
import sys
import json
import logging

# Configure logging to stderr so it doesn't interfere with stdio JSON-RPC
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[MOCK-TOOL] %(message)s")

def main():
    logging.info("Starting mock MCP tool...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            req = json.loads(line)
            logging.info(f"Received request: {req.get('method')}")

            response = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
            }

            method = req.get("method")

            if method == "initialize":
                response["result"] = {
                    "protocolVersion": "2024-11-05", # current mcp version
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mock-mcp-tool",
                        "version": "1.0.0"
                    }
                }
            elif method == "tools/list":
                response["result"] = {
                    "tools": [
                        {
                            "name": "echo",
                            "description": "Echoes back the input",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"}
                                }
                            }
                        }
                    ]
                }
            elif method == "tools/call":
                params = req.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})

                if name == "echo":
                    response["result"] = {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Echo: {args.get('message', '')}"
                            }
                        ]
                    }
                else:
                    response["error"] = {"code": -32601, "message": "Method not found"}
            elif method == "ping":
                response["result"] = {}
            else:
                 # Default generic response for other lifecycle methods
                 response["result"] = {}

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            logging.error("Invalid JSON")
        except Exception as e:
            logging.error(f"Error: {e}")
            break

if __name__ == "__main__":
    main()
