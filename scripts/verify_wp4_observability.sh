#!/usr/bin/env bash
# verify_wp4_observability.sh
# Validates that WP4 Observability pipeline correctly exports traces to JSONL and MLflow

set -e

echo "Starting WP4 Observability Validation..."

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
echo "🚀 [1/3] Running Experiment with Full Observability..."
rm -rf run_artifacts/advanced_attack_test/traces.jsonl
set +e
mantis --run configs/attacks/advanced_attack_test.yaml > /dev/null 2>&1
set -e

echo "✅ Execution finished."
echo ""
echo "📊 [2/3] Validating traces.jsonl..."
TRACE_FILE="run_artifacts/advanced_attack_test/traces.jsonl"

if [ ! -f "$TRACE_FILE" ]; then
    echo "❌ ERROR: Trace file not found at $TRACE_FILE"
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    exit 1
fi

LINES=$(wc -l < "$TRACE_FILE" | tr -d ' ')
echo "SUCCESS: Found $LINES observability events in $TRACE_FILE."
head -n 2 "$TRACE_FILE"

echo ""
echo "📊 [3/3] Validating MLflow database..."
if [ ! -d "mlruns" ]; then
    echo "❌ ERROR: MLflow mlruns directory not created."
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    exit 1
fi
echo "SUCCESS: MLflow directory generated successfully."

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo ""
echo "WP4 Observability Validation Completed Successfully."
