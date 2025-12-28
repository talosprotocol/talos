#!/usr/bin/env python3
"""
Talos Generic MCP Connector
Usage: python3 connector.py [config_file]
"""

import os
import sys
import yaml
import time
import subprocess
import signal
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TalosConnector")

DEFAULT_CONFIG = "mcp_config.yaml"

class TalosConnector:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.processes: list[subprocess.Popen] = []
        self.running = True

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            logger.error(f"Config file not found: {self.config_path}")
            sys.exit(1)
        
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def _init_identity(self):
        """Initialize Talos Identity."""
        identity = self.config.get("identity", {})
        name = identity.get("name", "TalosHost")
        data_dir = os.path.expanduser(identity.get("data_dir", "~/.talos/connector"))
        registry = identity.get("registry", "localhost:8765")

        logger.info(f"🔑 Initializing Identity '{name}' in {data_dir}...")
        
        # Ensure dir exists
        os.makedirs(data_dir, exist_ok=True)

        # Init
        subprocess.run([
            sys.executable, "-m", "src.client.cli",
            "--data-dir", data_dir,
            "init", "--name", name
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Register
        logger.info(f"🌐 Registering with {registry}...")
        subprocess.run([
            sys.executable, "-m", "src.client.cli",
            "--data-dir", data_dir,
            "register", "--server", registry
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return data_dir, registry

    def _validate_policy(self):
        """Validates that a strict security policy is defined."""
        policy = self.config.get("policy", {})
        if not policy.get("require_capability"):
            logger.warning("⚠️  Security Warning: 'policy.require_capability' is NOT enabled.")
        if not policy.get("default_deny_unknown_tools"):
            logger.warning("⚠️  Security Warning: 'policy.default_deny_unknown_tools' is NOT enabled.")
        
        logger.info(f"🛡️  Policy loaded: {len(policy)} rules active.")

    def start(self):
        self._validate_policy()
        data_dir, registry = self._init_identity()
        resources = self.config.get("resources", [])

        if not resources:
            logger.warning("No resources defined in config.")
            return

        logger.info(f"🚀 Starting {len(resources)} MCP Bridges...")

        for res in resources:
            name = res.get("name")
            cmd = res.get("command")
            peers = res.get("allowed_peers", [])

            if not peers:
                logger.warning(f"⚠️  Resource '{name}' has no allowed_peers. Skipping for security.")
                continue

            # For now, we spawn one bridge per peer per resource (or utilize multi-peer support if available)
            # The current mcp-serve command takes one --authorized-peer arg or handles generic? 
            # Looking at source, it accepts a single peer. 
            # We will grab the first peer for MVP or spawn multiples.
            # Let's assume MVP: First peer only.
            peer_id = peers[0]

            logger.info(f"   Drafting Bridge: {name} -> {peer_id}")
            
            # Spawn the bridge
            # python3 -m src.client.cli mcp-serve ...
            proc = subprocess.Popen([
                sys.executable, "-m", "src.client.cli",
                "--data-dir", data_dir,
                "mcp-serve",
                "--authorized-peer", peer_id,
                "--command", cmd,
                "--server", registry,
                "--port", "0" # Random port
            ])
            self.processes.append(proc)

        logger.info("✅ All bridges running. Press Ctrl+C to stop.")
        
        # Wait loop
        try:
            while self.running:
                time.sleep(1)
                # Check health
                for p in self.processes:
                    if p.poll() is not None:
                        logger.error("A bridge process died unexpectedly.")
                        self.stop()
                        break
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("🛑 Stopping bridges...")
        self.running = False
        for p in self.processes:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG
    connector = TalosConnector(cfg)
    connector.start()
