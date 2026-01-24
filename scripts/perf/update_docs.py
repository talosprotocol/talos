#!/usr/bin/env python3
"""Update documentation with latest benchmark results from JSON artifacts.

This script reads JSON benchmark results and updates the relevant documentation
files while preserving historical data and honoring sentinel markers.
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
import sys

try:
    import jsonschema  # type: ignore
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


SENTINEL_BEGIN = "<!-- PERF-AUTO:BEGIN -->"
SENTINEL_END = "<!-- PERF-AUTO:END -->"


def validate_artifact(data: dict, schema_path: Path):
    """Validate data against a JSON schema."""
    if not HAS_JSONSCHEMA:
        return
    
    if not schema_path.exists():
        print(f"Warning: Schema file {schema_path} not found, skipping validation")
        return
        
    with open(schema_path) as f:
        schema = json.load(f)
        
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"❌ Schema validation FAILED for {schema_path.name}: {e.message}")
        sys.exit(1)


def format_benchmark_table(benchmarks: dict, metadata: dict) -> str:
    """Format benchmarks as a markdown table."""
    lines = []
    lines.append(f"### Latest Results ({metadata.get('timestamp', 'N/A')[:10]})")
    lines.append("")
    lines.append(f"**Hardware:** {metadata.get('cpu', {}).get('model', 'Unknown')}, "
                 f"{metadata.get('cpu', {}).get('cores', 'N/A')} cores, "
                 f"{metadata.get('ram_gb', 'N/A')}GB RAM")
    lines.append(f"**Environment:** {'Container' if metadata.get('containerized') else 'Local'}, "
                 f"Power: {metadata.get('power_mode', 'N/A')}, "
                 f"Thermal: {metadata.get('thermal_state', 'N/A')}")
    if metadata.get('is_non_baseline'):
        lines.append("> ⚠️ **Note:** Results marked as non-baseline (battery or thermal throttling detected)")
    lines.append(f"**Git SHA:** `{metadata.get('git_sha_short', 'N/A')}`")
    lines.append("")
    lines.append("| Operation | Median (ms) | p95 (ms) | Throughput (ops/sec) |")
    lines.append("|-----------|-------------|----------|---------------------|")
    
    for name, data in sorted(benchmarks.items()):
        stats = data.get('stats', {})
        # Note: We use median_ms as specified in the lock-ins
        median = stats.get('median_ms', 0)
        p95 = stats.get('p95_ms', 0)
        ops = stats.get('ops_per_sec', 0)
        lines.append(f"| {name} | {median:.4f} | {p95:.4f} | {ops:,.0f} |")
    
    return '\n'.join(lines)


def update_content_with_sentinel(content: str, new_perf_data: str) -> str:
    """Replace content between sentinel markers."""
    pattern = re.compile(
        f"{re.escape(SENTINEL_BEGIN)}.*?{re.escape(SENTINEL_END)}",
        re.DOTALL
    )
    
    replacement = f"{SENTINEL_BEGIN}\n\n{new_perf_data}\n\n{SENTINEL_END}"
    
    if pattern.search(content):
        return pattern.sub(replacement, content)
    else:
        # If no sentinel found, append it (though better if user adds it)
        return content + f"\n\n{replacement}\n"


def update_benchmarks_md(perf_dir: Path, docs_dir: Path, schemas_dir: Path):
    """Update Benchmarks.md with latest results."""
    benchmarks_file = docs_dir / "Benchmarks.md"
    if not benchmarks_file.exists():
        print(f"Warning: {benchmarks_file} not found")
        return

    # Read metadata
    metadata_file = perf_dir / "metadata.json"
    with open(metadata_file) as f:
        metadata = json.load(f)
    validate_artifact(metadata, schemas_dir / "metadata.schema.json")
    
    # Results by platform
    platforms = [
        ("Python SDK", perf_dir / "sdk_python_crypto.json"),
        ("Go SDK", perf_dir / "sdk_go_crypto.json"),
    ]
    
    all_perf_md = []
    for name, json_path in platforms:
        if json_path.exists():
            with open(json_path) as jf:
                data = json.load(jf)
                validate_artifact(data, schemas_dir / "bench_result.schema.json")
                benchmarks = data.get('benchmarks', {})
            
            all_perf_md.append(f"## {name} Benchmarks\n")
            all_perf_md.append(format_benchmark_table(benchmarks, metadata))
            all_perf_md.append("")
    
    if not all_perf_md:
        return

    perf_data = "\n".join(all_perf_md)
    
    with open(benchmarks_file, 'r') as f:
        content = f.read()
    
    new_content = update_content_with_sentinel(content, perf_data)
    
    with open(benchmarks_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated {benchmarks_file} (sentinel-safe)")


def main():
    parser = argparse.ArgumentParser(description='Update docs from performance benchmark results')
    parser.add_argument('--in', dest='perf_dir', required=True, help='Performance results directory')
    parser.add_argument('--docs', required=True, help='Documentation directory')
    parser.add_argument('--schemas', required=True, help='Schemas directory')
    
    args = parser.parse_args()
    
    perf_dir = Path(args.perf_dir)
    docs_dir = Path(args.docs)
    schemas_dir = Path(args.schemas)
    
    if not all(d.exists() for d in [perf_dir, docs_dir, schemas_dir]):
        print("Error: Required directory not found")
        return 1
    
    update_benchmarks_md(perf_dir, docs_dir, schemas_dir)
    return 0


if __name__ == '__main__':
    exit(main())
