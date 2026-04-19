#!/bin/bash
set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo "Starting Parallelized Test Orchestration"

# Run Karate API Check
echo "Running Karate API tests..."
api-testing/karate/run-karate.sh api_validation.feature &
KARATE_PID=$!

# Run Playwright Checks (Dockerized)
echo "Running Playwright UI tests in Docker..."
# Note: scripts/test_ui.sh expects to be run from the component directory or handles it via REL_PATH
( cd site/dashboard && bash "../../scripts/test_ui.sh" npx playwright test ) &
PLAYWRIGHT_PID=$!

wait $KARATE_PID
echo "API Backend tests complete."

wait $PLAYWRIGHT_PID
echo "Frontend UI tests complete."

echo "All Parallel Systems Validated!"
