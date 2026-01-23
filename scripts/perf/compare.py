#!/usr/bin/env python3
"""Automated regression comparator for performance results.

Compares a candidate result directory against a base results directory,
normalizing by environment class (OS, CPU, Container status).
"""

import argparse
import json
import sys
from pathlib import Path

def get_env_class(metadata: dict) -> str:
    """Determine environment class for normalization."""
    os_sys = metadata.get('os', {}).get('system', 'unknown')
    cpu_model = metadata.get('cpu', {}).get('model', 'unknown')
    container = 'container' if metadata.get('containerized') else 'local'
    return f"{os_sys}-{cpu_model}-{container}"

def compare_results(base_data: dict, cand_data: dict, threshold: float = 0.20):
    """Compare candidate benchmarks against base results."""
    regressions = []
    improvements = []
    
    base_benches = base_data.get('benchmarks', {})
    cand_benches = cand_data.get('benchmarks', {})
    
    for name, cand_res in cand_benches.items():
        if name in base_benches:
            base_res = base_benches[name]
            
            base_ms = base_res.get('stats', {}).get('median_ms', 0)
            cand_ms = cand_res.get('stats', {}).get('median_ms', 0)
            
            if base_ms > 0:
                diff = (cand_ms - base_ms) / base_ms
                
                res = {
                    "name": name,
                    "base_ms": base_ms,
                    "candidate_ms": cand_ms,
                    "diff_percent": diff * 100
                }
                
                if diff > threshold:
                    regressions.append(res)
                elif diff < -threshold:
                    improvements.append(res)
                    
    return regressions, improvements

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Path to base results directory")
    parser.add_argument("--candidate", required=True, help="Path to candidate results directory")
    parser.add_argument("--threshold", type=float, default=0.20, help="Regression threshold (default 0.20)")
    args = parser.parse_args()
    
    base_dir = Path(args.base)
    cand_dir = Path(args.candidate)
    
    # Load metadata
    with open(base_dir / "metadata.json") as f:
        base_meta = json.load(f)
    with open(cand_dir / "metadata.json") as f:
        cand_meta = json.load(f)
        
    base_env = get_env_class(base_meta)
    cand_env = get_env_class(cand_meta)
    
    env_match = base_env == cand_env
    
    print(f"Base environment:      {base_env}")
    print(f"Candidate environment: {cand_env}")
    
    if not env_match:
        print("⚠️  Environments do not match. Comparison will be informational only.")
    
    # Compare common artifacts
    artifacts = ["sdk_python_crypto.json", "sdk_go_crypto.json"]
    
    all_regressions = []
    all_improvements = []
    
    for art in artifacts:
        base_art = base_dir / art
        cand_art = cand_dir / art
        
        if base_art.exists() and cand_art.exists():
            print(f"\nComparing {art}...")
            with open(base_art) as f: b_data = json.load(f)
            with open(cand_art) as f: c_data = json.load(f)
            
            regs, imps = compare_results(b_data, c_data, args.threshold)
            all_regressions.extend(regs)
            all_improvements.extend(imps)
            
            for r in regs:
                print(f"  ❌ REGRESSION: {r['name']} (+{r['diff_percent']:.1f}%)")
            for i in imps:
                print(f"  ✅ IMPROVEMENT: {i['name']} ({i['diff_percent']:.1f}%)")
            if not regs and not imps:
                print("  ✅ No significant changes detected.")
    
    # Write regression.json
    output = {
        "base_run": args.base,
        "candidate_run": args.candidate,
        "environment_match": env_match,
        "threshold": args.threshold,
        "regressions": all_regressions,
        "improvements": all_improvements
    }
    
    reg_file = cand_dir / "regression.json"
    with open(reg_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nRegression report saved to {reg_file}")
    
    # Fail closed if environments match and regressions exist
    if env_match and all_regressions:
        print("\n❌ FAILED: Performance regressions detected in matching environment.")
        sys.exit(1)
        
    print("\n✅ Performance comparison complete.")

if __name__ == "__main__":
    main()
