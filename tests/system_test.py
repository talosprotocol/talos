import subprocess
import time
import sys
import os
import shutil
import re
from pathlib import Path
import threading
import queue

# Config
PYTHON = sys.executable
BASE_DIR = Path("live_test_data")
SERVER_DIR = BASE_DIR / "server"
ALICE_DIR = BASE_DIR / "alice"
BOB_DIR = BASE_DIR / "bob"

def clean_dirs():
    if BASE_DIR.exists():
        shutil.rmtree(BASE_DIR)
    SERVER_DIR.mkdir(parents=True)
    ALICE_DIR.mkdir(parents=True)
    BOB_DIR.mkdir(parents=True)

def run_cmd(cmd, cwd=None, env=None):
    return subprocess.run(
        cmd, 
        cwd=cwd, 
        env=env, 
        capture_output=True, 
        text=True, 
        check=True
    )

class ProcessRunner:
    def __init__(self, name, cmd, cwd=None, env=None):
        self.name = name
        self.cmd = cmd
        self.process = None
        self.output_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        print(f"[{self.name}] Starting: {' '.join(self.cmd)}")
        self.process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        self.thread = threading.Thread(target=self._read_output)
        self.thread.daemon = True
        self.thread.start()

    def _read_output(self):
        for line in self.process.stdout:
            self.output_queue.put(line)
            # print(f"[{self.name}] {line.strip()}")
            if self.stop_event.is_set():
                break

    def wait_for(self, pattern, timeout=10):
        start_time = time.time()
        buffer = ""
        while time.time() - start_time < timeout:
            try:
                line = self.output_queue.get(timeout=0.1)
                buffer += line
                if re.search(pattern, line):
                    return re.search(pattern, line)
            except queue.Empty:
                continue
        raise TimeoutError(f"[{self.name}] Timed out waiting for '{pattern}'")

    def stop(self):
        self.stop_event.set()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

def main():
    print("=== LIVE SYSTEM TEST ORCHESTRATOR ===")
    
    # 1. Cleanup
    clean_dirs()
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()

    # 2. Start Server
    server = ProcessRunner(
        "SERVER", 
        [PYTHON, "-m", "src.server.server", "--port", "8765"],
        env=env
    )
    
    try:
        server.start()
        server.wait_for(r"Listening on: 0.0.0.0:8765")
        print("✅ Server started")

        # 3. Init Alice
        print("Initializing Alice...")
        res_alice = run_cmd(
            [PYTHON, "-m", "src.client.cli", "--data-dir", str(ALICE_DIR), "init", "--name", "Alice"],
            env=env
        )
        alice_address = re.search(r"Address: ([a-f0-9]+)", res_alice.stdout).group(1)
        print(f"✅ Alice initialized: {alice_address[:16]}...")

        # 4. Init Bob
        print("Initializing Bob...")
        res_bob = run_cmd(
            [PYTHON, "-m", "src.client.cli", "--data-dir", str(BOB_DIR), "init", "--name", "Bob"],
            env=env
        )
        bob_address = re.search(r"Address: ([a-f0-9]+)", res_bob.stdout).group(1)
        print(f"✅ Bob initialized: {bob_address[:16]}...")

        # 5. Start Alice Listener
        alice_listener = ProcessRunner(
            "ALICE_LISTENER",
            [PYTHON, "-m", "src.client.cli", "--data-dir", str(ALICE_DIR), "listen", "--port", "8766"],
            env=env
        )
        alice_listener.start()
        alice_listener.wait_for(r"Registered")
        print("✅ Alice listening")

        # 6. Start Bob Listener
        bob_listener = ProcessRunner(
            "BOB_LISTENER",
            [PYTHON, "-m", "src.client.cli", "--data-dir", str(BOB_DIR), "listen", "--port", "8767"],
            env=env
        )
        bob_listener.start()
        bob_listener.wait_for(r"Registered")
        print("✅ Bob listening")

        # 7. Alice sends message to Bob
        print("Alice sending message to Bob...")
        msg_content = f"SecretCode-{int(time.time())}"
        
        # We need a separate send call. 
        # Note: 'send' command might fail if it tries to bind to the same port as listener
        # But 'send' command creates a NEW Client instance, which by default binds to port 0 (random)
        # UNLESS the CLI defaults override it.
        # CLI 'send' defaults to port 8766. Alice's listener is on 8766.
        # So we MUST specify a different port for the sender call.
        
        res_send = run_cmd(
            [
                PYTHON, "-m", "src.client.cli", 
                "--data-dir", str(ALICE_DIR), 
                "send", bob_address, msg_content,
                "--port", "8768" 
            ],
            env=env
        )
        if "Message sent!" in res_send.stdout:
            print("✅ Message sent command succeeded")
        else:
            print("❌ Message send command failed")
            print(res_send.stdout)
            print(res_send.stderr)
            sys.exit(1)

        # 8. Verify Bob received it
        print("Waiting for Bob to receive...")
        bob_listener.wait_for(msg_content)
        print("✅ Bob received the message!")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    finally:
        print("Stopping processes...")
        try:
            alice_listener.stop()
        except: pass
        try:
            bob_listener.stop()
        except: pass
        server.stop()
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
