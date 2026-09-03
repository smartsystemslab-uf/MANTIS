#!/usr/bin/env bash
# demo_wp5_attacks.sh
# Demonstrates the four concrete attack plugins implemented in WP5

set -e

if [ ! -d "run_artifacts" ]; then
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

echo "=========================================================="
echo "🛡️  MANTIS WP5: Attack and Failure Plugins Demo 🛡️"
echo "=========================================================="
echo ""

echo "[1/4] Running Prompt Injection Attack..."
echo "-> Injecting malicious instructions into the Front Office Transaction Monitor."
mantis --run configs/attacks/wp5_prompt_injection.yaml > /dev/null 2>&1
echo "✅ Finished. Traces exported to run_artifacts/wp5_prompt_injection/traces.jsonl"
echo ""

echo "[2/4] Running Message Spoofing Attack..."
echo "-> Spoofing a compliance clearance message in the Mid Office Rep Assist."
mantis --run configs/attacks/wp5_message_spoofing.yaml > /dev/null 2>&1
echo "✅ Finished. Traces exported to run_artifacts/wp5_message_spoofing/traces.jsonl"
echo ""

echo "[3/4] Running Route Confusion Attack..."
echo "-> Forcing Front Office Router to bypass Compliance and go straight to Decision Making."
mantis --run configs/attacks/wp5_route_confusion.yaml > /dev/null 2>&1
echo "✅ Finished. Traces exported to run_artifacts/wp5_route_confusion/traces.jsonl"
echo ""

echo "[4/4] Running Tool Parameter Mutation Attack..."
echo "-> Mutating the destination account in a Front Office execution workflow."
mantis --run configs/attacks/wp5_tool_mutation.yaml > /dev/null 2>&1
echo "✅ Finished. Traces exported to run_artifacts/wp5_tool_mutation/traces.jsonl"
echo ""

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo "WP5 Demo Complete! You can inspect the traces to see the security events."
