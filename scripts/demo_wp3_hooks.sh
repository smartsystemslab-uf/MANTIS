#!/usr/bin/env bash
# demo_wp3_hooks.sh
# Demonstrates the WP3 HookBus intercepting an execution flow natively.

set -e

echo "Starting WP3 Hook Bus Demo..."

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
echo "🚀 [1/2] Injecting Mock Attack Plugin into Front Office Workflow..."
echo "Running: mantis --run configs/attacks/advanced_attack_test.yaml"

set +e
mantis --run configs/attacks/advanced_attack_test.yaml > /dev/null 2>&1
set -e

echo "✅ Execution finished."
echo ""
echo "📊 [2/2] Validating Hook Coverage Metadata..."
COVERAGE_FILE="run_artifacts/advanced_attack_test/hook_coverage.json"

if [ ! -f "$COVERAGE_FILE" ]; then
    echo "❌ ERROR: Hook coverage file not found at $COVERAGE_FILE"
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    exit 1
fi

echo "Coverage Report Generated:"
cat "$COVERAGE_FILE"
echo ""

if grep -q "prompt_injection" "$COVERAGE_FILE"; then
    echo "SUCCESS: The Hook Bus successfully injected and executed the attack plugin during runtime!"
else
    echo "❌ ERROR: The attack plugin was not executed by the HookBus."
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    exit 1
fi

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo ""
echo "WP3 Hook Bus Demo Completed Successfully."
