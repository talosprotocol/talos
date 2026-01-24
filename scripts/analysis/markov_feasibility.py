#!/usr/bin/env python3
"""
Markov Chain Feasibility Analysis
---------------------------------
Reads audit events and builds a Transition Probability Matrix (TPM) to model
system behavior. Helps identify missing states, absorbing states, or 
anomalous zero-probability transitions.

Usage:
    python3 markov_feasibility.py --url http://localhost:8081 --limit 1000
"""

import requests
import argparse
import pandas as pd
import numpy as np
from collections import defaultdict
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("markov-analysis")

def fetch_events(base_url, limit=1000):
    """Fetch recent events from Audit Service using cursor-based pagination."""
    url = f"{base_url}/api/events"
    all_events = []
    cursor = None
    batch_size = 200 # Max allowed by service
    
    logger.info(f"Fetching last {limit} events from {url}...")
    
    while len(all_events) < limit:
        # Calculate remaining needed, capped at batch_size
        remaining = limit - len(all_events)
        current_limit = min(remaining, batch_size)
        
        params = {"limit": current_limit}
        if cursor:
            params["before"] = cursor # API uses 'before' for cursor pagination (newest first)
            
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            items = data.get("items", [])
            if not items:
                logger.info("No more items returned.")
                break
                
            all_events.extend(items)
            logger.info(f"Fetched {len(items)} events. Total: {len(all_events)}/{limit}")
            
            if not data.get("has_more"):
                break
                
            next_cursor = data.get("next_cursor")
            if not next_cursor or next_cursor == cursor:
                # Break if cursor doesn't move to prevent infinite loop
                break
            cursor = next_cursor
            
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            break
            
    logger.info(f"✅ Retrieved {len(all_events)} events total.")
    return all_events

def extract_state(event):
    """
    Derive a discrete state from an audit event.
    State Definition: (Actor Type, Action, Outcome)
    Example: ('USER', 'chat', 'OK')
    """
    try:
        principal = event.get("principal", {})
        if isinstance(principal, dict):
            actor_type = principal.get("type", "UNKNOWN")
        else:
            actor_type = str(principal)

        # Simplify action to avoid state explosion
        # Priority: 'action' -> 'method' -> 'http.path'
        action = event.get("action")
        if not action or isinstance(action, dict):
            action = event.get("method")
        
        if not action or isinstance(action, dict):
             action = event.get("http", {}).get("path") or "unknown"
        
        # Ensure string and normalize
        action_str = str(action)
        if "/api/events" in action_str: action_str = "emit_audit"
        if "/mcp/tools" in action_str: action_str = "tool_use"
        if "{" in action_str: action_str = "complex_resource" # Fallback for dict leakage
        
        outcome = event.get("outcome", "OK")
        
        return f"{actor_type}:{action_str}:{outcome}"
    except Exception:
        return "ERROR:INVALID_SCHEMA"

def build_transition_matrix(events):
    """
    Constructs a transition matrix from a time-ordered sequence of events.
    We assume events are global time-ordered.
    For more granular analysis, we should group by session_id.
    """
    # Sort by timestamp to ensure causal ordering
    # Audit service returns DESC usually, so we reverse
    events_sorted = sorted(events, key=lambda x: x.get("ts", ""))
    
    # Group by session_id/correlation_id to find logical flows
    sessions = defaultdict(list)
    for e in events_sorted:
        # Prefer session_id, fallback to correlation_id
        sid = e.get("meta", {}).get("session_id") or e.get("request_id")
        if sid:
            sessions[sid].append(e)
            
    transitions = defaultdict(int)
    state_counts = defaultdict(int)
    
    logger.info(f"Analyzing {len(sessions)} unique sessions/flows...")
    
    for sid, flow in sessions.items():
        if not flow: continue
        
        # Pad with START/END states?
        # For now, just transitions between observed events
        for i in range(len(flow) - 1):
            current_state = extract_state(flow[i])
            next_state = extract_state(flow[i+1])
            
            transitions[(current_state, next_state)] += 1
            state_counts[current_state] += 1
            
        # Count the last state
        last_state = extract_state(flow[-1])
        state_counts[last_state] += 1

    return transitions, state_counts

def print_matrix(transitions, state_counts):
    """Print ASCII Matrix."""
    states = sorted(list(state_counts.keys()))
    if not states:
        logger.warning("No states found.")
        return

    logger.info("\n--- Transition Probability Matrix ---")
    
    # Header
    print(f"{'State':<40} | " + " | ".join([f"{s[:10]:<10}" for s in states]))
    print("-" * (40 + 13 * len(states)))
    
    for src in states:
        row = f"{src:<40} | "
        total = state_counts[src]
        # Adjust total to simple sum of outgoing for calculation if simplified
        # Real Markov: Sum(P_ij) = 1. Here we calculate empirical prob.
        
        # Re-calc denominator based on actual observed transitions from src
        outgoing_total = sum(transitions[(src, dst)] for dst in states)
        
        for dst in states:
            count = transitions.get((src, dst), 0)
            prob = count / outgoing_total if outgoing_total > 0 else 0.0
            # Highlight high probability
            val_str = f"{prob:.2f}"
            if prob > 0.5: val_str = f"*{val_str}*"
            row += f"{val_str:<10} | "
        print(row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8081")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    
    events = fetch_events(args.url, args.limit)
    if not events:
        return
        
    transitions, counts = build_transition_matrix(events)
    print_matrix(transitions, counts)
    
    # Feasibility Check
    print("\n--- Feasibility Assessment ---")
    if len(counts) > 3:
        print("✅ Sufficient state diversity detected.")
    else:
        print("⚠️ Low state diversity. Generate more varied traffic.")
        
    if len(transitions) > len(counts):
        print("✅ Connected graph structure detected.")
    else:
        print("⚠️ Sparse transitions. Flows may be disconnected or too simple.")

if __name__ == "__main__":
    main()
