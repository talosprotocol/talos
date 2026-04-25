import subprocess
import time
import sys
import os
import shutil
import re
import json
import pytest
from pathlib import Path

# Config
PYTHON = sys.executable
BASE_DIR = Path("live_test_v2_data")

@pytest.fixture(scope="module")
def env():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    return env

@pytest.fixture(scope="module")
def test_data():
    if BASE_DIR.exists():
        shutil.rmtree(BASE_DIR)
    BASE_DIR.mkdir(parents=True)
    
    dirs = {
        "server": BASE_DIR / "server",
        "alice": BASE_DIR / "alice",
        "bob": BASE_DIR / "bob"
    }
    for d in dirs.values():
        d.mkdir(parents=True)
    return dirs

class LiveProcess:
    def __init__(self, name, cmd, env, wait_pattern=None, timeout=15):
        self.name = name
        self.cmd = cmd
        self.env = env
        self.process = None
        self.wait_pattern = wait_pattern
        self.timeout = timeout

    def start(self):
        print(f"[{self.name}] Starting...")
        self.process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=self.env,
            bufsize=1,
            universal_newlines=True
        )
        
        if self.wait_pattern:
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                line = self.process.stdout.readline()
                if not line:
                    break
                # print(f"[{self.name}] {line.strip()}")
                if re.search(self.wait_pattern, line):
                    print(f"[{self.name}] ✅ Started and ready")
                    return
            self.stop()
            raise TimeoutError(f"[{self.name}] Failed to start within {self.timeout}s (pattern '{self.wait_pattern}' not found)")

    def stop(self):
        if self.process:
            print(f"[{self.name}] Stopping...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

def run_cli(args, test_data, env):
    cmd = [PYTHON, "-m", "src.client.cli", "--data-dir", str(test_data)] + args
    return subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)

@pytest.mark.live
def test_full_p2p_flow(test_data, env):
    # 1. Start Registry Server
    server = LiveProcess(
        "SERVER",
        [PYTHON, "-m", "src.server.server", "--port", "18765"],
        env,
        wait_pattern=r"Listening on: 0.0.0.0:18765"
    )
    
    alice_listener = None
    bob_listener = None
    
    try:
        server.start()
        
        # 2. Initialize Alice and Bob
        run_cli(["init", "--name", "Alice"], test_data["alice"], env)
        res_bob = run_cli(["init", "--name", "Bob"], test_data["bob"], env)
        bob_address = re.search(r"Address: ([a-f0-9]+)", res_bob.stdout).group(1)
        
        # 3. Start Alice and Bob Listeners
        alice_listener = LiveProcess(
            "ALICE",
            [PYTHON, "-m", "src.client.cli", "--data-dir", str(test_data["alice"]), "listen", "--port", "18766", "--server", "localhost:18765"],
            env,
            wait_pattern=r"Registered"
        )
        alice_listener.start()
        
        bob_listener = LiveProcess(
            "BOB",
            [PYTHON, "-m", "src.client.cli", "--data-dir", str(test_data["bob"]), "listen", "--port", "18767", "--server", "localhost:18765"],
            env,
            wait_pattern=r"Registered"
        )
        bob_listener.start()
        
        # 4. Alice sends message to Bob
        msg = f"LiveTest-{uuid7_minimal()}"
        print(f"Alice sending: {msg}")
        run_cli(
            ["send", bob_address, msg, "--server", "localhost:18765", "--port", "18768"],
            test_data["alice"],
            env
        )
        
        # 5. Verify Bob received it
        print("Verifying Bob's reception...")
        start_time = time.time()
        found = False
        while time.time() - start_time < 10:
            line = bob_listener.process.stdout.readline()
            if msg in line:
                found = True
                break
        
        assert found, "Bob did not receive Alice's message"
        print("✅ Message received by Bob!")

    finally:
        if alice_listener: alice_listener.stop()
        if bob_listener: bob_listener.stop()
        server.stop()

def uuid7_minimal():
    return str(int(time.time() * 1000))
