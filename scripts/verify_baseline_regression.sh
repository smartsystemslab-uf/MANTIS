#!/usr/bin/env bash
# verify_baseline_regression.sh
# Validates WP1 legacy banking integrations by running regression guard tests.

set -e

echo "Starting Baseline Regression Verification..."

if [ ! -d "refactor_guard_tests" ]; then
    echo "ERROR: Must be run from the MANTIS project root."
    exit 1
fi

source .venv/bin/activate

echo "Checking if Banking Backend is running..."
if ! curl -s http://127.0.0.1:8000/docs > /dev/null; then
    echo "-> Starting temporary backend server on port 8000..."
    python -m uvicorn citi_banking_backend.app.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &
    BACKEND_PID=$!
    sleep 3
else
    BACKEND_PID=""
fi

echo ""
echo "[1/2] Running Refactor Guard Tests (Banking Semantic Isolation)"
# Set a temporary trace directory so we do not pollute golden_runs
export MANTIS_TRACE_DIR="test_runs"
mkdir -p "$MANTIS_TRACE_DIR"

# Generate fresh traces from the baseline configs
mantis --run configs/baselines/front_office_baseline.yaml > "$MANTIS_TRACE_DIR/front_office_monitoring.out" 2>&1
mantis --run configs/baselines/mid_office_baseline.yaml > "$MANTIS_TRACE_DIR/mid_office_planning.out" 2>&1
mantis --run configs/baselines/back_office_baseline.yaml > "$MANTIS_TRACE_DIR/back_office_clean.out" 2>&1

set +e
pytest refactor_guard_tests/ -q
PYTEST_EXIT=$?
set -e

rm -rf "$MANTIS_TRACE_DIR"

if [ $PYTEST_EXIT -ne 0 ]; then
    echo "ERROR: Regression tests failed. Legacy banking behavior was not preserved."
    exit 1
else
    echo "SUCCESS: The refactored MANTIS architecture strictly preserves legacy banking behavior."
fi

echo ""
echo "[2/2] Validating System Inventory Generation"
mantis --inventory > inventory_output.json
if grep -q '"workflows"' inventory_output.json; then
    echo "SUCCESS: System inventory generated successfully."
else
    echo "ERROR: Failed to produce valid system inventory."
    rm inventory_output.json
    exit 1
fi
rm inventory_output.json

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo ""
echo "Baseline Regression Verification Completed Successfully."
