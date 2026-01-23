#!/usr/bin/env python3
"""Update documentation with latest benchmark results from JSON artifacts.

This script reads JSON benchmark results and updates the relevant documentation
files while preserving historical data.

Usage:
    python scripts/perf/update_docs.py \\
        --in artifacts/perf/20260122-a639264 \\
        --docs docs/wiki
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def format_benchmark_table(benchmarks: dict, metadata: dict) -> str:
    """Format benchmarks as a markdown table."""
    lines = []
    lines.append(f"\n### Latest Results ({metadata.get('timestamp', 'N/A')[:10]})")
    lines.append(f"\n**Hardware:** {metadata.get('cpu', {}).get('model', 'Unknown')}, "
                 f"{metadata.get('cpu', {}).get('cores', 'N/A')} cores, "
                 f"{metadata.get('ram_gb', 'N/A')}GB RAM")
    lines.append(f"**Python:** {metadata.get('python', {}).get('version', 'N/A')}")
    lines.append(f"**Git SHA:** `{metadata.get('git_sha_short', 'N/A')}`")
    lines.append("")
    lines.append("| Operation | Median (ms) | p95 (ms) | Throughput (ops/sec) |")
    lines.append("|-----------|-------------|----------|---------------------|")
    
    for name, data in sorted(benchmarks.items()):
        stats = data.get('stats', {})
        median = stats.get('median_ms', 0)
        p95 = stats.get('p95_ms', 0)
        ops = stats.get('ops_per_sec', 0)
        lines.append(f"| {name} | {median:.4f} | {p95:.4f} | {ops:,.0f} |")
    
    return '\n'.join(lines)


def update_benchmarks_md(perf_dir: Path, docs_dir: Path):
    """Update docs/wiki/Benchmarks.md with latest results."""
    benchmarks_file = docs_dir / "Benchmarks.md"
    
    if not benchmarks_file.exists():
        print(f"Warning: {benchmarks_file} not found, skipping")
        return
    
    # Read metadata
    metadata_file = perf_dir / "metadata.json"
    if not metadata_file.exists():
        print(f"Warning: {metadata_file} not found")
        metadata = {}
    else:
        with open(metadata_file) as f:
            metadata = json.load(f)
    
    # Read SDK Python benchmarks
    sdk_python_file = perf_dir / "sdk_python_crypto.json"
    if sdk_python_file.exists():
        with open(sdk_python_file) as f:
            sdk_data = json.load(f)
            benchmarks = sdk_data.get('benchmarks', {})
        
        # Format table
        table = format_benchmark_table(benchmarks, metadata)
        
        # Append to Benchmarks.md
        with open(benchmarks_file, 'a') as f:
            f.write("\n\n---\n")
            f.write(f"\n## Automated Benchmark Run - {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(table)
        
        print(f"✅ Updated {benchmarks_file}")


def update_testing_md(perf_dir: Path, docs_dir: Path):
    """Update docs/wiki/Testing.md with performance testing guidance."""
    testing_file = docs_dir / "Testing.md"
    
    if not testing_file.exists():
        print(f"Warning: {testing_file} not found, skipping")
        return
    
    # Read existing content
    with open(testing_file) as f:
        content = f.read()
    
    # Check if performance section already exists
    if "## Performance Testing" in content:
        print(f"Performance testing section already exists in {testing_file}")
        return
    
    # Add performance testing section
    perf_section = """

## Performance Testing

### Running Performance Tests

The project includes comprehensive performance tests to ensure SLA compliance and track performance regressions.

#### Core SLA Tests

Core authorization and capability tests with strict latency targets:

```bash
# From repo root
PYTHONPATH=src pytest tests/test_performance.py -v
```

#### Python SDK Benchmarks

Cryptographic operations benchmarks (wallet, double ratchet, A2A):

```bash
cd sdks/python
PYTHONPATH=src python benchmarks/bench_crypto.py
```

#### Full Performance Suite

Run all performance tests with JSON output and multiple runs:

```bash
./scripts/perf/run_all.sh
```

Results are saved to `artifacts/perf/<date>-<sha>/` with full metadata.

### Performance SLAs

- Authorization (cached session): <1ms p99
- Signature verification: <500μs
- Total Talos overhead: <5ms p99
- Authorization throughput: >10,000 auth/sec

See [Benchmarks](Benchmarks.md) for detailed results and historical data.
"""
    
    # Append to file
    with open(testing_file, 'a') as f:
        f.write(perf_section)
    
    print(f"✅ Updated {testing_file}")


def main():
    parser = argparse.ArgumentParser(description='Update docs from performance benchmark results')
    parser.add_argument('--in', dest='perf_dir', required=True, help='Performance results directory')
    parser.add_argument('--docs', required=True, help='Documentation directory')
    
    args = parser.parse_args()
    
    perf_dir = Path(args.perf_dir)
    docs_dir = Path(args.docs)
    
    if not perf_dir.exists():
        print(f"Error: Performance results directory not found: {perf_dir}")
        return 1
    
    if not docs_dir.exists():
        print(f"Error: Documentation directory not found: {docs_dir}")
        return 1
    
    print(f"Updating documentation from: {perf_dir}")
    print(f"Documentation directory: {docs_dir}")
    print()
    
    update_benchmarks_md(perf_dir, docs_dir)
    update_testing_md(perf_dir, docs_dir)
    
    print("\n✅ Documentation update complete")
    return 0


if __name__ == '__main__':
    exit(main())
