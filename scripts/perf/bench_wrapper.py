#!/usr/bin/env python3
"""Wrapper to run benchmarks multiple times and output JSON with statistics.

This wrapper runs any benchmark script N times, collects statistics,  
and outputs machine-readable JSON results.

Usage:
    python scripts/perf/bench_wrapper.py \\
        --script "PYTHONPATH=src python benchmarks/bench_crypto.py" \\
        --output artifacts/perf/sdk_python_crypto.json \\
        --runs 5 \\
        --warmup 1
"""

import argparse
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone


def parse_text_output(output: str) -> dict:
    """Parse benchmark text output and extract metrics.
    
    This is a simple parser that looks for common patterns like:
    - "Operation: X.XXX ms (Y,YYY ops/sec)"
    - Table formats with | delimiters
    
    Returns dict with benchmark names and timing data.
    """
    benchmarks = {}
    lines = output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip separator lines, headers, empty lines
        if not line or line.startswith('=') or line.startswith('#') or '---' in line:
            continue
            
        # Try to extract benchmark results
        # Pattern: "Name X.XXX ms (Y,YYY ops/sec)"
        if 'ms' in line and 'ops/sec' in line:
            parts = line.split()
            try:
                # Find the part with ms
                ms_idx = next(i for i, p in enumerate(parts) if 'ms' in p)
                ms_val = float(parts[ms_idx].replace('ms', ''))
                
                # Name is everything before the ms value
                name = ' '.join(parts[:ms_idx]).strip()
                if name.startswith('|'):
                    name = name[1:].strip()
                
                benchmarks[name] = {'avg_ms': ms_val}
            except (ValueError, StopIteration):
                continue
    
    return benchmarks


def run_benchmark(command: str, warmup: bool = False) -> dict:
    """Run benchmark command once and return results."""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        sys.stderr.write(f"Benchmark failed: {result.stderr}\n")
        sys.exit(1)
    
    # Parse output
    benchmarks = parse_text_output(result.stdout)
    
    if not warmup:
        # Print to console (so user sees progress)
        print(result.stdout)
    
    return benchmarks


def calculate_stats(runs: list[dict]) -> dict:
    """Calculate statistics across multiple runs."""
    # Get all benchmark names from first run
    if not runs:
        return {}
    
    all_benchmarks = {}
    benchmark_names = runs[0].keys()
    
    for name in benchmark_names:
        # Collect all timing values for this benchmark
        values = [run[name]['avg_ms'] for run in runs if name in run]
        
        if values:
            sorted_values = sorted(values)
            n = len(sorted_values)
            p95_idx = int(n * 0.95)
            
            all_benchmarks[name] = {
                'runs': values,
                'stats': {
                    'median_ms': statistics.median(values),
                    'p95_ms': sorted_values[min(p95_idx, n-1)],
                    'mean_ms': statistics.mean(values),
                    'stddev_ms': statistics.stdev(values) if len(values) > 1 else 0.0,
                    'min_ms': min(values),
                    'max_ms': max(values),
                    'ops_per_sec': 1000 / statistics.median(values) if statistics.median(values) > 0 else 0
                }
            }
    
    return all_benchmarks


def main():
    parser = argparse.ArgumentParser(description='Run benchmarks with multiple runs and JSON output')
    parser.add_argument('--script', required=True, help='Command to run benchmark')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    parser.add_argument('--runs', type=int, default=5, help='Number of measured runs')
    parser.add_argument('--warmup', type=int, default=1, help='Number of warmup runs')
    
    args = parser.parse_args()
    
    print(f"Running benchmark: {args.script}")
    print(f"Warmup runs: {args.warmup}, Measured runs: {args.runs}")
    print()
    
    # Warmup
    if args.warmup > 0:
        print(f"Warming up ({args.warmup} runs)...")
        for i in range(args.warmup):
            run_benchmark(args.script, warmup=True)
        print()
    
    # Measured runs
    print(f"Collecting measurements ({args.runs} runs)...")
    runs = []
    for i in range(args.runs):
        print(f"\n--- Run {i+1}/{args.runs} ---")
        result = run_benchmark(args.script, warmup=False)
        runs.append(result)
    
    # Calculate statistics
    benchmarks = calculate_stats(runs)
    
    # Create output
    output = {
        'schema_version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'command': args.script,
        'runs_count': args.runs,
        'warmup_count': args.warmup,
        'benchmarks': benchmarks
    }
    
    # Write JSON
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results written to: {args.output}")
    print(f"   Benchmarks captured: {len(benchmarks)}")


if __name__ == '__main__':
    main()
