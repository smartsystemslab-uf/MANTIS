#!/usr/bin/env bash
# demo_wp5_attacks.sh
# Demonstrates the concrete attack plugins implemented in WP5, across
# front, mid, and back office.

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

# A clean process exit only means the run didn't crash -- it says nothing
# about whether the attack plugin actually intercepted anything (a plugin
# whose match condition never fires still exits 0). Grepping the fresh
# trace for ATTACK_INJECTED is what actually proves the attack fired; this
# is what caught route_confusion silently never matching ADK's real
# transfer_to_agent argument name in every run before this check existed.
assert_attack_fired() {
    local run_name="$1"
    local trace_file="run_artifacts/${run_name}/traces.jsonl"
    if [ ! -f "$trace_file" ]; then
        echo "❌ ERROR: Trace file not found at $trace_file"
        if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID"; fi
        exit 1
    fi
    if ! grep -q '"ATTACK_INJECTED"' "$trace_file"; then
        echo "❌ ERROR: No ATTACK_INJECTED event in $trace_file -- the attack plugin never actually fired."
        if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID"; fi
        exit 1
    fi
    echo "✅ Finished. Attack fired -- traces exported to $trace_file"
}

echo "[1/5] Running Prompt Injection Attack..."
echo "-> Injecting malicious instructions into the Front Office Transaction Monitor."
mantis --run configs/attacks/wp5_prompt_injection.yaml > /dev/null 2>&1
assert_attack_fired wp5_prompt_injection
echo ""

echo "[2/5] Running Message Spoofing Attack..."
echo "-> Spoofing a compliance clearance message in the Mid Office Rep Assist."
mantis --run configs/attacks/wp5_message_spoofing.yaml > /dev/null 2>&1
assert_attack_fired wp5_message_spoofing
echo ""

echo "[3/5] Running Route Confusion Attack..."
echo "-> Forcing Front Office Router to bypass Compliance and go straight to Decision Making."
mantis --run configs/attacks/wp5_route_confusion.yaml > /dev/null 2>&1
assert_attack_fired wp5_route_confusion
echo ""

echo "[4/5] Running Tool Parameter Mutation Attack..."
echo "-> Mutating the destination account in a Front Office execution workflow."
mantis --run configs/attacks/wp5_tool_mutation.yaml > /dev/null 2>&1
assert_attack_fired wp5_tool_mutation
echo ""

echo "[5/5] Running Back Office Tool Parameter Mutation Attack..."
echo "-> Redirecting a validated EOD ledger post onto an unvalidated batch."
mantis --run configs/attacks/wp5_back_office_tool_mutation.yaml > /dev/null 2>&1
assert_attack_fired wp5_back_office_tool_mutation
echo ""

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo "WP5 Demo Complete! Every attack plugin was confirmed to have actually fired, not just to have exited cleanly."
