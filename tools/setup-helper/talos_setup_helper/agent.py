import time
import time
import requests
import logging
from pathlib import Path
from typing import Optional

from .auth import AuthManager
from .manifest import ManifestManager
from .jail import WorkspaceJail

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, config_dir: Path):
        self.auth = AuthManager(config_dir)
        self.manifest = ManifestManager()
        self.jail = WorkspaceJail(config_dir / "workspace")
        self.running = False
        
    def pair(self, dashboard_url: str, token: str):
        self.auth.pair(dashboard_url, token)
        logger.info("Successfully paired with dashboard")

    def run(self):
        """Main event loop"""
        if not self.auth.is_paired():
            raise RuntimeError("Agent not paired. Run 'pair' command first.")
            
        self.running = True
        logger.info("Agent starting polling loop...")
        
        while self.running:
            try:
                self._poll()
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                time.sleep(5) # Backoff
                
    def _poll(self):
        """Poll dashboard for jobs"""
        base_url = self.auth.get_dashboard_url()
        headers = self.auth.get_headers()
        agent_id = headers["X-Talos-Agent-ID"]
        
        # Long poll (timeout logic to be added on server side usually, or just short intervals)
        try:
            url = f"{base_url}/api/setup/agents/{agent_id}/poll"
            resp = requests.post(
                url, 
                json={"status": "idle", "agent_id": agent_id}, # Schema: agent_poll_request
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                job = data.get("job")
                if job:
                    self._execute_job(job)
            elif resp.status_code == 204:
                time.sleep(2) # Idle wait
            else:
                logger.warning(f"Poll returned {resp.status_code}")
                time.sleep(5)
                
        except requests.exceptions.Timeout:
            pass # Just retry on timeout
            
    def _execute_job(self, job: dict):
        """Execute a job payload"""
        logger.info(f"Received job: {job}")
        job_id = job.get("job_id")
        recipe_id = job.get("recipe_id")

        if not job_id or not isinstance(job_id, str):
            logger.error(f"Invalid job_id: {job_id}")
            return
            
        if not recipe_id or not isinstance(recipe_id, str):
             self._send_event(job_id, "failed", {"error": "Missing recipe_id"})
             return

        # 1. Verify Recipe in Manifest
        try:
            # We don't have the recipe content here, but we check if ID exists
            # In Phase 1 we assume built-in recipes logic for execution
            recipe_def = self.manifest.get_recipe(recipe_id)
            logger.info(f"Executing recipe: {recipe_def['description']}")
            
            # 2. Setup Workspace
            job_dir = self.jail.create_job_dir(job_id)
            
            # 3. Simulate Execution (Phase 1 Placeholder)
            self._send_event(job_id, "started", {"message": f"Starting job {job_id}"})
            time.sleep(1)
            self._send_event(job_id, "completed", {"message": "Job executed successfully (simulation)"})
            
        except Exception as e:
            logger.error(f"Job failed: {e}")
            self._send_event(job_id, "failed", {"error": str(e)})

    def _send_event(self, job_id: str, status: str, payload: dict):
        base_url = self.auth.get_dashboard_url()
        headers = self.auth.get_headers()
        url = f"{base_url}/api/setup/jobs/{job_id}/events"
        requests.post(url, json={
            "job_id": job_id,
            "status": status,
            "payload": payload,
            "timestamp": "2024-01-01T00:00:00Z" # TODO: Real timestamp
        }, headers=headers)
