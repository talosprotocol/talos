#!/usr/bin/env python3
"""Wrapper to run benchmarks multiple times and output JSON with statistics.

This wrapper runs any benchmark script N times, collects statistics,  
and outputs machine-readable JSON results validated against schemas.
"""

import argparse
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def validate_artifact(data: dict, schema_path: str):
    """Validate data against a JSON schema."""
    if not HAS_JSONSCHEMA:
        print("Warning: jsonschema not installed, skipping validation")
        return
    
    schema_file = Path(schema_path)
    if not schema_file.exists():
        print(f"Warning: Schema file {schema_path} not found, skipping validation")
        return
        
    with open(schema_file) as f:
        schema = json.load(f)
        
    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f"✅ Schema validation passed for {schema_file.name}")
    except jsonschema.ValidationError as e:
        print(f"❌ Schema validation FAILED for {schema_file.name}: {e.message}")
        sys.exit(1)


def parse_go_json(output: str) -> dict:
    """Parse Go's native -json output format for benchmarks."""
    benchmarks = {}
    lines = output.strip().split('\n')
    
    for line in lines:
        try:
            event = json.loads(line)
            if event.get('Action') == 'output' and 'Benchmark' in event.get('Output', ''):
                raw_line = event['Output'].strip()
                # Example: BenchmarkWalletGenerate-14  110878  10660 ns/op
                parts = raw_line.split()
                if len(parts) >= 4 and 'ns/op' in parts:
                    ns_idx = parts.index('ns/op')
                    name = parts[0].split('-')[0]
                    iterations = int(parts[ns_idx - 2])
                    ns_per_op = float(parts[ns_idx - 1])
                    
                    # Convert to ms
                    ms_per_op = ns_per_op / 1_000_000
                    
                    benchmarks[name] = {
                        'avg_ms': ms_per_op,
                        'iterations': iterations
                    }
        except (json.JSONDecodeError, ValueError, IndexError):
            continue
            
    return benchmarks


def parse_text_output(output: str) -> dict:
    """Parse benchmark text output and extract metrics."""
    benchmarks = {}
    lines = output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('=') or line.startswith('#') or '---' in line:
            continue
            
        if 'ms' in line and 'ops/sec' in line:
            parts = line.split()
            try:
                # Find the 'ms' indicator
                ms_idx = next(i for i, p in enumerate(parts) if 'ms' in p)
                
                # The value might be in the same part (e.g., '1.23ms') or previous part ('1.23 ms')
                raw_val = parts[ms_idx].replace('ms', '')
                if not raw_val and ms_idx > 0:
                    raw_val = parts[ms_idx - 1]
                    val_idx = ms_idx - 1
                else:
                    val_idx = ms_idx
                
                ms_val = float(raw_val.replace(',', ''))
                
                # Name is everything before the value part
                name = ' '.join(parts[:val_idx]).strip()
                if name.startswith('|'):
                    name = name[1:].strip()
                
                benchmarks[name] = {'avg_ms': ms_val}
            except (ValueError, StopIteration, IndexError):
                continue
    return benchmarks


def run_benchmark(command: str, is_go_json: bool = False, warmup: bool = False) -> dict:
    """Run benchmark command once and return results."""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    
    # We allow non-zero exit for Go -json if we still got output
    if result.returncode != 0 and not is_go_json:
        sys.stderr.write(f"Benchmark failed (code {result.returncode}): {result.stderr}\n")
        sys.exit(1)
    
    if is_go_json:
        benchmarks = parse_go_json(result.stdout)
    else:
        benchmarks = parse_text_output(result.stdout)
    
    if not warmup and not is_go_json:
        print(result.stdout)
    
    return benchmarks


def calculate_stats(runs: list[dict]) -> dict:
    """Calculate statistics across multiple runs."""
    if not runs:
        return {}
    
    all_benchmarks = {}
    benchmark_names = runs[0].keys()
    
    for name in benchmark_names:
        values = [run[name]['avg_ms'] for run in runs if name in run]
        iterations = sum(run[name].get('iterations', 1) for run in runs if name in run)
        
        if values:
            sorted_values = sorted(values)
            n = len(sorted_values)
            p95_idx = int(n * 0.95)
            
            all_benchmarks[name] = {
                'stats': {
                    'median_ms': statistics.median(values),
                    'p95_ms': sorted_values[min(p95_idx, n-1)],
                    'mean_ms': statistics.mean(values),
                    'stddev_ms': statistics.stdev(values) if len(values) > 1 else 0.0,
                    'ops_per_sec': 1000 / statistics.median(values) if statistics.median(values) > 0 else 0,
                    'iterations': iterations
                }
            }
    
    return all_benchmarks


def main():
    parser = argparse.ArgumentParser(description='Run benchmarks with multiple runs and JSON output')
    parser.add_argument('--script', required=True, help='Command to run benchmark')
    parser.add_argument('--output', required=True, help='Output JSON file path')
    parser.add_argument('--runs', type=int, default=5, help='Number of measured runs')
    parser.add_argument('--warmup', type=int, default=1, help='Number of warmup runs')
    parser.add_argument('--is-go-json', action='store_true', help='Parse Go -json output')
    parser.add_argument('--schema', help='Path to JSON schema for validation')
    
    args = parser.parse_args()
    
    print(f"Running benchmark: {args.script}")
    
    runs = []
    
    run_count = args.runs
    warmup_count = args.warmup

    if warmup_count > 0:
        print(f"Warming up ({warmup_count} runs)...")
        for i in range(warmup_count):
            run_benchmark(args.script, is_go_json=args.is_go_json, warmup=True)
            
    print(f"Collecting measurements ({run_count} runs)...")
    for i in range(run_count):
        if run_count > 1:
            print(f"--- Run {i+1}/{run_count} ---")
        result = run_benchmark(args.script, is_go_json=args.is_go_json, warmup=False)
        if result:
            runs.append(result)
            
    if not runs:
        print("❌ No benchmark results captured!")
        sys.exit(1)
    
    benchmarks = calculate_stats(runs)
    
    output = {
        'schema_version': '1.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'command': args.script,
        'runs_count': run_count,
        'warmup_count': warmup_count,
        'benchmarks': benchmarks
    }
    
    if args.schema:
        validate_artifact(output, args.schema)
    
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results written to: {args.output}")


if __name__ == '__main__':
    main()
