#!/usr/bin/env python3
"""
Talos Traffic Generator
Generates synthetic traffic for Chat (Ollama) and Audit Events (A2A simulation).
Targets Talos Gateway available endpoints.
"""

import asyncio
import aiohttp
import argparse
import time
import uuid
import random
import logging
from statistics import median

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("traffic-gen")

GATEWAY_URL = "http://localhost:8080"  # Default to 8080
HEADERS = {
    "x-talos-internal-service": "traffic-generator",
    "Content-Type": "application/json"
}

class Stats:
    def __init__(self):
        self.requests = 0
        self.errors = 0
        self.latencies = []
        self.start_time = time.time()

    def record(self, latency_ms, error=False):
        self.requests += 1
        if error:
            self.errors += 1
        else:
            self.latencies.append(latency_ms)

    def report(self, mode):
        duration = time.time() - self.start_time
        if not self.latencies:
            p50 = 0
            p95 = 0
        else:
            self.latencies.sort()
            p50 = median(self.latencies)
            p95_idx = int(len(self.latencies) * 0.95)
            p95 = self.latencies[p95_idx]
        
        rps = self.requests / duration if duration > 0 else 0
        logger.info(f"[{mode.upper()}] Req: {self.requests} | Err: {self.errors} | RPS: {rps:.1f} | p50: {p50:.1f}ms | p95: {p95:.1f}ms")

async def run_chat(session, sem, stats, model="ollama"):
    """Simulate Chat using the MCP Tool endpoint which is available."""
    async with sem:
        url = f"{GATEWAY_URL}/mcp/tools/chat"
        # Matches ChatRequest in gateway/main.py
        payload = {
            "session_id": str(uuid.uuid4()),
            "model": model,
            "messages": [{"role": "user", "content": "Hello world"}],
            "capability": "cap_stress_test",
            "temperature": 0.7,
            "max_tokens": 10,
            "timeout_ms": 5000
        }
        start = time.time()
        try:
            # We expect 500 or 200 depending on if upstream connector is ready
            # But the gateway itself will verify and return.
            # actually connector is on 8082. Gateway calls it.
            async with session.post(url, headers=HEADERS, json=payload) as resp:
                # 200 OK means success. 500 means connector fail (still counts as traffic)
                if resp.status == 200:
                    await resp.json()
                    stats.record((time.time() - start) * 1000)
                else:
                    text = await resp.text()
                    # logger.warning(f"Chat status {resp.status}: {text[:100]}")
                    # Count as success for 'traffic' if it hit the gateway, but error for stats
                    stats.record((time.time() - start) * 1000, error=True)
        except Exception as e:
            logger.error(f"Chat Exception: {e}")
            stats.record((time.time() - start) * 1000, error=True)

async def run_a2a_sim(session, sem, stats):
    """Simulate A2A by generating Audit Events directly."""
    async with sem:
        url = f"{GATEWAY_URL}/api/events"
        payload = {
            "event_type": "A2A_FRAME_EXCHANGED",
            "actor": f"agent-{uuid.uuid4().hex[:6]}",
            "action": "send_frame",
            "resource": f"session-{uuid.uuid4().hex[:6]}",
            "metadata": {"size": 128, "encrypted": True}
        }
        start = time.time()
        try:
            async with session.post(url, headers=HEADERS, json=payload) as resp:
                if resp.status == 200:
                    await resp.json()
                    stats.record((time.time() - start) * 1000)
                else:
                    stats.record((time.time() - start) * 1000, error=True)
        except Exception as e:
            logger.error(f"Event Exception: {e}")
            stats.record((time.time() - start) * 1000, error=True)

async def main():
    parser = argparse.ArgumentParser(description="Talos Traffic Generator")
    parser.add_argument("--mode", choices=["chat", "a2a", "all"], default="all")
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--url", default="http://localhost:8080")
    args = parser.parse_args()

    global GATEWAY_URL
    GATEWAY_URL = args.url

    stats_chat = Stats()
    stats_a2a = Stats()
    
    sem = asyncio.Semaphore(args.concurrency)
    
    logger.info(f"Starting traffic gen: {args.mode} | Concurrency: {args.concurrency} | Duration: {'Inf' if args.duration == 0 else str(args.duration) + 's'} | Target: {GATEWAY_URL}")
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = []
        while True:
            # Check duration limit
            if args.duration > 0 and (time.time() - start_time) > args.duration:
                break

            if args.mode in ["chat", "all"]:
                tasks.append(asyncio.create_task(run_chat(session, sem, stats_chat)))
            if args.mode in ["a2a", "all"]:
                tasks.append(asyncio.create_task(run_a2a_sim(session, sem, stats_a2a)))
            
            if len(tasks) > args.concurrency * 2:
                await asyncio.gather(*tasks)
                tasks = []
                
            # Periodic Report (every ~5s)
            if random.random() < 0.05:
                if args.mode in ["chat", "all"]: stats_chat.report("chat")
                if args.mode in ["a2a", "all"]: stats_a2a.report("a2a")
            
            # await asyncio.sleep(0.1)  # Removed to maximize throughput
        
        if tasks:
            await asyncio.gather(*tasks)

    print("\n--- Final Report ---")
    if args.mode in ["chat", "all"]: stats_chat.report("chat")
    if args.mode in ["a2a", "all"]: stats_a2a.report("a2a (simulated)")

if __name__ == "__main__":
    asyncio.run(main())
