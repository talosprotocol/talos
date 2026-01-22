#!/usr/bin/env python3
import os
import sys
import yaml
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Configuration
REPOS = [
    "contracts",
    "core",
    "services/ai-gateway",
    "sdks/typescript",
    "sdks/python"
]

ARTIFACTS_DIR = Path("artifacts/coverage")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

class Coordinator:
    def __init__(self, repos: List[str]):
        self.repos = [Path(r) for r in repos]
        self.results = {}

    def run_command(self, cmd: str, cwd: Path) -> bool:
        print(f"  ➜ Running: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True, cwd=cwd)
            return True
        except subprocess.CalledProcessError:
            print(f"  ❌ Command failed: {cmd}")
            return False

    def load_manifest(self, repo_path: Path) -> Dict[str, Any]:
        manifest_path = repo_path / ".agent" / "test_manifest.yml"
        if not manifest_path.exists():
            print(f"❌ Manifest not found for {repo_path}")
            return None
        with open(manifest_path) as f:
            return yaml.safe_load(f)

    def process_repo(self, repo_path: Path):
        print(f"\n📦 Processing Repo: {repo_path}")
        start_time = time.time()
        repo_results = {"steps": {}}
        
        # 1. Verify Manifest
        print("🔹 Step 1: Verifying Manifest")
        # Calculate absolute path to validator script to handle different repo depths
        validator_script = Path(__file__).parent / "verify_manifest.sh"
        # We use relative path from the cwd (repo_path) to the validator for cleanliness in logs, 
        # or just use absolute path in command. Using absolute is safer.
        cmd = f"'{validator_script.resolve()}' .agent/test_manifest.yml"
        
        if not self.run_command(cmd, cwd=repo_path):
            repo_results["status"] = "failed"
            repo_results["failed_step"] = "verify_manifest"
            self.results[str(repo_path)] = repo_results
            return

        manifest = self.load_manifest(repo_path)
        if not manifest:
            return

        # 2. Interop Gate
        if manifest.get("interop", {}).get("enabled"):
            print("🔹 Step 2: Interop Gate")
            cmd = manifest["interop"]["command"]
            if not self.run_command(cmd, cwd=repo_path):
                print("❌ Interop/Vector Compliance Failed!")
                repo_results["status"] = "failed"
                repo_results["failed_step"] = "interop"
                self.results[str(repo_path)] = repo_results
                return

        # 3. Unit Tests (Ratchet Enforced)
        print("🔹 Step 3: Unit Tests")
        unit_cmd = manifest["entrypoints"]["unit"]
        if not self.run_command(unit_cmd, cwd=repo_path):
            print("❌ Unit Tests Failed!")
            repo_results["status"] = "failed"
            repo_results["failed_step"] = "unit"
            self.results[str(repo_path)] = repo_results
            return

        # 4. Integration Tests (Report Only for now)
        if "integration" in manifest["entrypoints"]:
            print("🔹 Step 4: Integration Tests")
            int_cmd = manifest["entrypoints"]["integration"]
            if not self.run_command(int_cmd, cwd=repo_path):
                 print("⚠️ Integration Tests Failed (Proceeding as report-only)")
                 repo_results["integration_status"] = "failed"
            else:
                 repo_results["integration_status"] = "passed"

        repo_results["status"] = "passed"
        repo_results["duration"] = time.time() - start_time
        self.results[str(repo_path)] = repo_results
        print(f"✅ Repo {repo_path} Completed Successfully")

    def run(self):
        print("🚀 Starting Coverage Coordinator")
        for repo in self.repos:
            self.process_repo(repo)
        
        # Write Summary
        summary_path = ARTIFACTS_DIR / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Summary written to {summary_path}")
        
        # Determine overall exit code
        if any(r["status"] == "failed" for r in self.results.values()):
            print("❌ Overall Status: FAILED")
            sys.exit(1)
        print("✅ Overall Status: PASSED")

if __name__ == "__main__":
    coordinator = Coordinator(REPOS)
    coordinator.run()
