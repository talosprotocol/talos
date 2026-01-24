#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple
import urllib.request

UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}\b")
B64URL_RE = re.compile(r"\b[A-Za-z0-9_-]{16,}\b")
INT_RE = re.compile(r"\b\d+\b")

def _http_get_json(url: str, timeout_s: int = 60) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)

def normalize_action(raw: str) -> str:
    s = raw.strip()
    s = UUID_RE.sub("{uuid}", s)
    s = B64URL_RE.sub("{b64}", s)
    s = INT_RE.sub("{n}", s)
    s = re.sub(r"/+", "/", s)
    return s

def pick(d: Dict[str, Any], *paths: str) -> Optional[Any]:
    # paths like "principal.type" or "request.path"
    for p in paths:
        cur: Any = d
        ok = True
        for part in p.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok:
            return cur
    return None

@dataclass(frozen=True)
class State:
    actor_type: str
    action: str
    outcome: str

def event_to_state(ev: Dict[str, Any]) -> Tuple[State, Dict[str, int]]:
    missing = {"actor_type": 0, "action": 0, "outcome": 0}

    actor_type = pick(ev, "principal.type", "principal.kind", "actor.type")
    if not actor_type:
        actor_type = "unknown"
        missing["actor_type"] = 1

    # Prefer a canonical action field if present
    action = pick(ev, "action", "event.action", "request.route", "request.path", "tool.name", "kind", "type", "event_type")
    if not action:
        action = "unknown_action"
        missing["action"] = 1
    action = normalize_action(str(action))

    # Outcome: ok vs denied vs error:<class>
    outcome = pick(ev, "outcome", "result", "decision", "status")
    if outcome is None:
        # fall back to HTTP status if present
        status = pick(ev, "http.status", "response.status_code")
        if isinstance(status, int):
            outcome = "ok" if 200 <= status < 400 else "error:http"
        else:
            outcome = "unknown_outcome"
            missing["outcome"] = 1
    outcome = str(outcome).lower()
    if outcome in ("allow", "allowed", "permit", "permitted", "ok", "success", "true"):
        outcome = "ok"
    elif outcome in ("deny", "denied", "forbidden", "unauthorized", "false"):
        outcome = "denied"

    return State(str(actor_type), action, outcome), missing

def get_group_key(ev: Dict[str, Any], group_by: str) -> str:
    v = pick(ev, group_by, group_by.replace("_", "."), f"meta.{group_by}")
    if v is None:
        return "unknown_group"
    return str(v)

def get_event_time(ev: Dict[str, Any]) -> str:
    t = pick(ev, "ts", "timestamp", "created_at", "time")
    return str(t or "")

def js_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    # Jensen-Shannon divergence with natural log
    keys = set(p) | set(q)
    m = {k: 0.5 * p.get(k, 0.0) + 0.5 * q.get(k, 0.0) for k in keys}

    def kl(a: Dict[str, float], b: Dict[str, float]) -> float:
        s = 0.0
        for k in keys:
            av = a.get(k, 0.0)
            bv = b.get(k, 0.0)
            if av > 0 and bv > 0:
                s += av * math.log(av / bv)
        return s

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8081", help="Audit service base URL")
    ap.add_argument("--limit", type=int, default=1000)
    ap.add_argument("--group-by", default="correlation_id", help="Group by key (default: correlation_id, formerly trace_id)")
    ap.add_argument("--out", default="artifacts/analysis/markov")
    ap.add_argument("--rare-p", type=float, default=0.05)
    ap.add_argument("--min-count", type=int, default=3)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--baseline-edges", default="", help="Optional baseline edges.jsonl to compute novel edges")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Fetch with pagination
    items: List[Dict[str, Any]] = []
    before: Optional[str] = None
    while len(items) < args.limit:
        url = f"{args.base_url.rstrip('/')}/api/events?limit={min(200, args.limit - len(items))}"
        if before:
            url += f"&before={before}"
        try:
            page = _http_get_json(url)
        except Exception as e:
            print(f"Error fetching from {url}: {e}", file=sys.stderr)
            break
            
        page_items = page.get("items") if isinstance(page, dict) else None
        if not page_items:
            break
        items.extend(page_items)
        before = page.get("next_cursor") or page.get("next") or None
        has_more = page.get("has_more")
        if has_more is False or not before:
            break

    if not items:
        print("ERROR: /api/events returned no items. Fix data flow before analysis.", file=sys.stderr)
        return 2
        
    print(f"Fetched {len(items)} events.", file=sys.stderr)

    # Group events
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in items:
        groups[get_group_key(ev, args.group_by)].append(ev)

    # Build state ids
    state_to_id: Dict[State, int] = {}
    id_to_state: List[State] = []

    def sid(st: State) -> int:
        if st not in state_to_id:
            state_to_id[st] = len(id_to_state)
            id_to_state.append(st)
        return state_to_id[st]

    missing_counts = Counter()
    edge_counts = Counter()  # (src_id, dst_id) -> count
    src_totals = Counter()   # src_id -> total outgoing

    # Deterministic ordering per group
    for _, evs in groups.items():
        evs.sort(key=lambda e: (get_event_time(e), str(pick(e, "event_id", "id") or "")))
        if len(evs) < 2:
            continue
        prev_state, miss = event_to_state(evs[0])
        for k, v in miss.items():
            missing_counts[k] += v
        prev_id = sid(prev_state)

        for ev in evs[1:]:
            st, miss = event_to_state(ev)
            for k, v in miss.items():
                missing_counts[k] += v
            cur_id = sid(st)
            edge_counts[(prev_id, cur_id)] += 1
            src_totals[prev_id] += 1
            prev_id = cur_id

    n_states = len(id_to_state)
    n_edges = len(edge_counts)
    possible_edges = n_states * n_states if n_states else 0
    sparsity = (n_edges / possible_edges) if possible_edges else 0.0

    # Rare edges
    rare = []
    edges_out = []
    for (a, b), c in edge_counts.items():
        p = c / src_totals[a] if src_totals[a] else 0.0
        rec = {"src": a, "dst": b, "count": c, "prob": p}
        edges_out.append(rec)
        if p < args.rare_p and c >= args.min_count:
            rare.append(rec)

    # Stationarity: compare first half vs second half by edge distribution
    # Recompute edge distributions by time chunk (simple split by event index)
    # This is coarse but sufficient for feasibility.
    half = len(items) // 2
    def build_edge_dist(sub_items: List[Dict[str, Any]]) -> Dict[str, float]:
        sub_groups = defaultdict(list)
        for ev in sub_items:
            sub_groups[get_group_key(ev, args.group_by)].append(ev)
        ec = Counter()
        st_map: Dict[State, int] = {}
        def local_id(s: State) -> int:
            if s not in st_map:
                st_map[s] = len(st_map)
            return st_map[s]
        for evs in sub_groups.values():
            evs.sort(key=lambda e: (get_event_time(e), str(pick(e, "event_id", "id") or "")))
            if len(evs) < 2:
                continue
            prev, _ = event_to_state(evs[0])
            prev_i = local_id(prev)
            for ev in evs[1:]:
                cur, _ = event_to_state(ev)
                cur_i = local_id(cur)
                ec[(prev_i, cur_i)] += 1
                prev_i = cur_i
        total = sum(ec.values()) or 1
        # stringify keys to avoid mismatched id spaces across halves
        return {f"{k[0]}->{k[1]}": v / total for k, v in ec.items()}

    dist_a = build_edge_dist(items[:half])
    dist_b = build_edge_dist(items[half:])
    jsd = js_divergence(dist_a, dist_b)

    # Top-K Jaccard
    def topk_keys(d: Dict[str, float], k: int) -> set:
        return set([x[0] for x in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:k]])
    top_a = topk_keys(dist_a, args.top_k)
    top_b = topk_keys(dist_b, args.top_k)
    jaccard = (len(top_a & top_b) / len(top_a | top_b)) if (top_a | top_b) else 1.0

    # Novel edges (optional baseline)
    baseline_set = set()
    if args.baseline_edges:
        with open(args.baseline_edges, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                baseline_set.add((obj["src"], obj["dst"]))

    novel = []
    if baseline_set:
        for e in edges_out:
            if (e["src"], e["dst"]) not in baseline_set:
                novel.append(e)

    summary = {
        "fetched_items": len(items),
        "groups": len(groups),
        "group_by": args.group_by,
        "states": n_states,
        "edges": n_edges,
        "sparsity": sparsity,
        "missing_field_counts": dict(missing_counts),
        "stationarity": {"js_divergence": jsd, "topk_jaccard": jaccard, "top_k": args.top_k},
        "rare_threshold": {"p_lt": args.rare_p, "min_count": args.min_count},
        "novel_edges_enabled": bool(baseline_set),
        "generated_at_utc": datetime.utcnow().isoformat() + "Z",
    }

    # Write artifacts
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)

    with open(os.path.join(args.out, "states.json"), "w", encoding="utf-8") as f:
        json.dump(
            {i: {"actor_type": s.actor_type, "action": s.action, "outcome": s.outcome} for i, s in enumerate(id_to_state)},
            f,
            indent=2,
            sort_keys=True,
        )

    with open(os.path.join(args.out, "edges.jsonl"), "w", encoding="utf-8") as f:
        for e in sorted(edges_out, key=lambda x: (-x["count"], x["src"], x["dst"])):
            f.write(json.dumps(e) + "\n")

    with open(os.path.join(args.out, "rare_edges.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(rare, key=lambda x: (x["prob"], -x["count"])), f, indent=2, sort_keys=True)

    with open(os.path.join(args.out, "novel_edges.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(novel, key=lambda x: (-x["count"], x["src"], x["dst"])), f, indent=2, sort_keys=True)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
