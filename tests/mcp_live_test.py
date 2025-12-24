import subprocess
import time
import sys
import os
import shutil
import re
import json
from pathlib import Path
import threading
import queue

# Config
PYTHON = sys.executable
BASE_DIR = Path("mcp_test_data")
SERVER_DIR = BASE_DIR / "server"
ALICE_DIR = BASE_DIR / "alice"
BOB_DIR = BASE_DIR / "bob"

MOCK_TOOL = os.path.abspath("tests/mock_mcp_tool.py")

def clean_dirs():
    if BASE_DIR.exists():
        shutil.rmtree(BASE_DIR)
    SERVER_DIR.mkdir(parents=True)
    ALICE_DIR.mkdir(parents=True)
    BOB_DIR.mkdir(parents=True)

class ProcessRunner:
    def __init__(self, name, cmd, cwd=None, env=None, stdin=False):
        self.name = name
        self.cmd = cmd
        self.process = None
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None
        self.stdin_mode = stdin

    def start(self):
        print(f"[{self.name}] Starting: {' '.join(self.cmd)}")
        self.process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Capture stderr for debug logging
            stdin=subprocess.PIPE if self.stdin_mode else None,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.thread = threading.Thread(target=self._read_output)
        self.thread.daemon = True
        self.thread.start()
        
        # Start stderr reader
        self.err_thread = threading.Thread(target=self._read_stderr)
        self.err_thread.daemon = True
        self.err_thread.start()

    def _read_output(self):
        # If we are an interactive proxy (stdin_mode), we treat stdout as data stream
        # If not, it's just logs.
        if self.process and self.process.stdout:
            for line in self.process.stdout:
                self.output_queue.put(("STDOUT", line))
                if self.stop_event.is_set():
                    break
    
    def _read_stderr(self):
        if self.process and self.process.stderr:
            for line in self.process.stderr:
                 self.output_queue.put(("STDERR", line))
                 if self.stop_event.is_set():
                    break

    def write_stdin(self, data):
        if self.process and self.process.stdin:
            self.process.stdin.write(data + "\n")
            self.process.stdin.flush()

    def wait_for_log(self, pattern, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                line_type, line = self.output_queue.get(timeout=0.1)
                # Print stderr logs to console for debugging
                if line_type == "STDERR":
                    # print(f"[{self.name} ERR] {line.strip()}")
                    pass
                
                # Check match
                if re.search(pattern, line):
                    return True
            except queue.Empty:
                continue
        raise TimeoutError(f"[{self.name}] Timed out waiting for log '{pattern}'")

    def read_json_response(self, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                line_type, line = self.output_queue.get(timeout=0.1)
                if line_type == "STDOUT":
                    # This should be the JSON RPC response
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        print(f"[{self.name} JUNK] {line.strip()}")
                        continue
            except queue.Empty:
                continue
        raise TimeoutError(f"[{self.name}] Timed out waiting for JSON response")

    def stop(self):
        self.stop_event.set()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

def run_cmd(cmd, env=None):
    return subprocess.run(
        cmd, 
        capture_output=True, 
        text=True, 
        check=True,
        env=env
    )

def main():
    print("=== LIVE MCP TEST ===")
    
    # 1. Cleanup
    clean_dirs()
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    # 2. Start Registry Server
    server = ProcessRunner(
        "SERVER", 
        [PYTHON, "-m", "src.server.server", "--port", "9765"],
        env=env
    )
    
    try:
        server.start()
        server.wait_for_log(r"Listening on: 0.0.0.0:9765")
        print("✅ Registry Server started")

        # 3. Init Alice (Client/User)
        print("Initializing Alice...")
        res = run_cmd([PYTHON, "-m", "src.client.cli", "--data-dir", str(ALICE_DIR), "init", "--name", "Alice"], env=env)
        alice_id = re.search(r"Address: ([a-f0-9]+)", res.stdout).group(1)
        print(f"✅ Alice initialized: {alice_id[:16]}...")

        # 4. Init Bob (Host/Tool)
        print("Initializing Bob...")
        res = run_cmd([PYTHON, "-m", "src.client.cli", "--data-dir", str(BOB_DIR), "init", "--name", "Bob"], env=env)
        bob_id = re.search(r"Address: ([a-f0-9]+)", res.stdout).group(1)
        print(f"✅ Bob initialized: {bob_id[:16]}...")

        # 5. Start Bob serving Mock Tool
        # mcp-serve --authorized-peer <Alice> --command "python mock_tool.py"
        # Using port 9766 for Bob
        bob_serve = ProcessRunner(
            "BOB_MCP_HOST",
            [
                PYTHON, "-m", "src.client.cli", 
                "--data-dir", str(BOB_DIR),
                "mcp-serve",
                "--server", "localhost:9765",
                "--port", "9766",
                "--authorized-peer", alice_id,
                "--command", f"{PYTHON} {MOCK_TOOL}"
            ],
            env=env
        )
        bob_serve.start()
        bob_serve.wait_for_log(r"MCP Proxy running")
        print("✅ Bob hosting Mock Tool")

        # 6. Start Alice Connecting
        # mcp-connect <Bob>
        # Using port 9767 for Alice
        # This process expects JSON-RPC on stdin
        alice_connect = ProcessRunner(
            "ALICE_MCP_CLIENT",
            [
                PYTHON, "-m", "src.client.cli",
                "--data-dir", str(ALICE_DIR),
                "mcp-connect",
                "--server", "localhost:9765",
                "--port", "9767",
                bob_id
            ],
            env=env,
            stdin=True
        )
        alice_connect.start()
        # Wait a moment for connection establishment (CLI doesn't output to stdout in mcp-connect mode easily visible without parsing stderr)
        # We can wait for "Connected" in stderr
        # alice_connect.wait_for_log(r"Tunnel established", timeout=10) # Log might be in stderr
        
        print("✅ Alice connected (waiting 5s for P2P handshake)...")
        time.sleep(5) 

        # 7. Test: Send 'initialize' request
        print("Testing: Sending 'initialize'...")
        init_req = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            },
            "id": 1
        }
        alice_connect.write_stdin(json.dumps(init_req))
        
        resp = alice_connect.read_json_response()
        print(f"Received: {json.dumps(resp, indent=2)}")
        
        assert resp["id"] == 1
        assert resp["result"]["serverInfo"]["name"] == "mock-mcp-tool"
        print("✅ Verified 'initialize' response")

        # 8. Test: Send 'tools/list'
        print("Testing: Sending 'tools/list'...")
        list_req = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        }
        alice_connect.write_stdin(json.dumps(list_req))
        
        resp = alice_connect.read_json_response()
        # print(f"Received: {json.dumps(resp, indent=2)}")
        
        tools = resp["result"]["tools"]
        assert len(tools) == 1
        assert tools[0]["name"] == "echo"
        print("✅ Verified 'tools/list' response")

        # 9. Test: Call Tool
        print("Testing: Calling 'echo' tool...")
        call_req = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {"message": "Hello from Blockchain!"}
            },
            "id": 3
        }
        alice_connect.write_stdin(json.dumps(call_req))
        
        resp = alice_connect.read_json_response()
        print(f"Received: {json.dumps(resp, indent=2)}")
        
        content = resp["result"]["content"][0]["text"]
        assert content == "Echo: Hello from Blockchain!"
        print("✅ Verified 'tools/call' response")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("Stopping processes...")
        try:
            alice_connect.stop() 
        except Exception:
            pass
        try:
            bob_serve.stop()
        except Exception:
            pass
        server.stop()

if __name__ == "__main__":
    main()
