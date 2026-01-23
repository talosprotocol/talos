#!/bin/bash
# Orchestrate full performance test suite with JSON output and doc updates.
# 
# Usage: ./scripts/perf/run_all.sh

# Handle arguments
BASE_RUN=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --base)
      BASE_RUN="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCHEMAS_DIR="$REPO_ROOT/contracts/schemas/perf/v1"
SCRIPTS_DIR="$REPO_ROOT/scripts/perf"

# Setup output directory
DATE=$(date +%Y%m%d)
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
OUTDIR="$REPO_ROOT/artifacts/perf/${DATE}-${SHA}"

echo -e "${GREEN}Output directory:${NC} $OUTDIR"
mkdir -p "$OUTDIR"
echo

# Step 1: Collect metadata
echo -e "${GREEN}[1/6]${NC} Collecting system metadata..."
python3 "$SCRIPTS_DIR/collect_env.py" > "$OUTDIR/metadata.json"

# Check battery status
ON_BATTERY=$(python3 -c "import json; print(json.load(open('$OUTDIR/metadata.json')).get('on_battery', False))")
if [[ "$ON_BATTERY" == "True" ]]; then
    echo -e "${YELLOW}⚠️  WARNING: Running on battery power!${NC}"
    echo -e "${YELLOW}   Results marked as NON-BASELINE and may be throttled.${NC}"
    echo
fi

echo -e "      ✅ Metadata saved to $OUTDIR/metadata.json"
echo

# Step 2: Run core SLA tests
echo -e "${GREEN}[2/6]${NC} Running core SLA performance tests..."
PYTHONPATH="$REPO_ROOT/python:$REPO_ROOT/core" pytest "$REPO_ROOT/tests/test_performance.py" -q \
  --json-report --json-report-file="$OUTDIR/core_sla.json" \
  --json-report-omit=log \
  2>&1 | tee "$OUTDIR/core_sla.txt"
echo -e "      ✅ Results saved to $OUTDIR/core_sla.json"
echo

# Step 3: Run Python SDK benchmarks
echo -e "${GREEN}[3/6]${NC} Running Python SDK crypto benchmarks (3 runs, 1 warmup)..."
python3 "$SCRIPTS_DIR/bench_wrapper.py" \
  --script "cd $REPO_ROOT/sdks/python && PYTHONPATH=src python3 benchmarks/bench_crypto.py" \
  --output "$OUTDIR/sdk_python_crypto.json" \
  --runs 3 \
  --warmup 1 \
  --schema "$SCHEMAS_DIR/bench_result.schema.json"
echo -e "      ✅ Results saved to $OUTDIR/sdk_python_crypto.json"
echo

# Step 4: Run Go SDK benchmarks (using native JSON output)
echo -e "${GREEN}[4/6]${NC} Running Go SDK crypto benchmarks (Go iterations)..."
python3 "$SCRIPTS_DIR/bench_wrapper.py" \
  --script "cd $REPO_ROOT/sdks/go && go test -bench . -benchmem -run '^$' ./benchmarks -json" \
  --output "$OUTDIR/sdk_go_crypto.json" \
  --is-go-json \
  --runs 1 \
  --warmup 0 \
  --schema "$SCHEMAS_DIR/bench_result.schema.json"
echo -e "      ✅ Results saved to $OUTDIR/sdk_go_crypto.json"
echo

# Step 5: Update documentation
echo -e "${GREEN}[5/6]${NC} Updating documentation..."
python3 "$SCRIPTS_DIR/update_docs.py" \
  --in "$OUTDIR" \
  --docs "$REPO_ROOT/docs/wiki" \
  --schemas "$SCHEMAS_DIR"
echo

# Step 6: Generate index.json
echo -e "${GREEN}[6/6]${NC} Generating index.json..."
python3 -c "
import json
from pathlib import Path
out = Path('$OUTDIR')
idx = {
    'schema_version': '1.0',
    'run_id': '${DATE}-${SHA}',
    'artifacts': {
        'metadata': 'metadata.json',
        'core_sla': 'core_sla.json',
        'sdk_python_crypto': 'sdk_python_crypto.json',
        'sdk_go_crypto': 'sdk_go_crypto.json'
    }
}
with open(out / 'index.json', 'w') as f:
    json.dump(idx, f, indent=2)
"
echo -e "      ✅ Index generated: $OUTDIR/index.json"
echo

# Step 7: Regression Comparison (Optional)
if [[ "${BASE_RUN:-}" != "" ]]; then
    echo -e "${GREEN}[7/7]${NC} Comparing against base run: $BASE_RUN..."
    python3 "$SCRIPTS_DIR/compare.py" \
      --base "$BASE_RUN" \
      --candidate "$OUTDIR" \
      --threshold 0.20
    
    # Update index.json to include regression report
    python3 -c "
import json
from pathlib import Path
out = Path('$OUTDIR')
with open(out / 'index.json', 'r+') as f:
    idx = json.load(f)
    idx['artifacts']['regression'] = 'regression.json'
    f.seek(0)
    json.dump(idx, f, indent=2)
    f.truncate()
"
fi

# Summary
echo -e "${BLUE}==================================================================${NC}"
echo -e "${GREEN}✅ Performance suite complete!${NC}"
echo -e "${BLUE}==================================================================${NC}"
echo
echo "Results directory: $OUTDIR"
if [[ "${BASE_RUN:-}" != "" ]]; then
    echo "Regression report: $OUTDIR/regression.json"
fi
echo
