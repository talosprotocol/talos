#!/bin/bash
# Orchestrate full performance test suite with JSON output and doc updates.
#
# Usage: ./scripts/perf/run_all.sh
#
# This script:
# 1. Collects system metadata
# 2. Runs core performance SLA tests  
# 3. Runs Python SDK benchmarks with multiple runs
# 4. Updates documentation with results
#
# All results saved to: artifacts/perf/<date>-<sha>/

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================================${NC}"
echo -e "${BLUE}  Talos Protocol - Benchmark-Grade Performance Test Suite${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo

# Setup output directory
DATE=$(date +%Y%m%d)
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
OUTDIR="artifacts/perf/${DATE}-${SHA}"

echo -e "${GREEN}Output directory:${NC} $OUTDIR"
mkdir -p "$OUTDIR"
echo

# Step 1: Collect metadata
echo -e "${GREEN}[1/4]${NC} Collecting system metadata..."
python scripts/perf/collect_env.py > "$OUTDIR/metadata.json"
echo -e "      ✅ Metadata saved to $OUTDIR/metadata.json"
echo

# Step 2: Run core SLA tests
echo -e "${GREEN}[2/4]${NC} Running core SLA performance tests..."
PYTHONPATH=src pytest tests/test_performance.py -q \
  --json-report --json-report-file="$OUTDIR/core_sla.json" \
  --json-report-omit=log \
  2>&1 | tee "$OUTDIR/core_sla.txt"
echo -e "      ✅ Results saved to $OUTDIR/core_sla.json"
echo

# Step 3: Run Python SDK benchmarks (with multiple runs)
echo -e "${GREEN}[3/4]${NC} Running Python SDK crypto benchmarks (5 runs, 1 warmup)..."
python scripts/perf/bench_wrapper.py \
  --script "cd sdks/python && PYTHONPATH=src python benchmarks/bench_crypto.py" \
  --output "$OUTDIR/sdk_python_crypto.json" \
  --runs 3 \
  --warmup 1
echo -e "      ✅ Results saved to $OUTDIR/sdk_python_crypto.json"
echo

# Step 4: Update documentation
echo -e "${GREEN}[4/4]${NC} Updating documentation..."
python scripts/perf/update_docs.py \
  --in "$OUTDIR" \
  --docs docs/wiki
echo

# Summary
echo -e "${BLUE}==================================================================${NC}"
echo -e "${GREEN}✅ Performance suite complete!${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo
echo "Results directory: $OUTDIR"
echo
echo "Artifacts created:"
ls -lh "$OUTDIR"
echo
echo "Documentation updated:"
echo "  - docs/wiki/Benchmarks.md"
echo "  - docs/wiki/Testing.md"
echo
