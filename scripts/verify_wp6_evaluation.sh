#!/usr/bin/env bash
# verify_wp6_evaluation.sh
# Verifies the trace evaluator on a successful WP5 trace directory.

set -e

if [ ! -d "run_artifacts" ]; then
    echo "ERROR: Must be run from the MANTIS project root."
    exit 1
fi

source .venv/bin/activate

echo "=========================================================="
echo "📊  MANTIS WP6: Automated Trace Evaluation 📊"
echo "=========================================================="
echo ""

# Ensure we have WP5 traces
if [ ! -f "run_artifacts/wp5_prompt_injection/traces.jsonl" ]; then
    echo "⚠️  WP5 traces not found. Running WP5 demo first..."
    ./scripts/demo_wp5_attacks.sh
fi

echo "Evaluating WP5 Prompt Injection Attack..."
mantis --evaluate run_artifacts/wp5_prompt_injection

echo ""
echo "Evaluating WP5 Message Spoofing Attack..."
mantis --evaluate run_artifacts/wp5_message_spoofing

echo ""
echo "Evaluating WP5 Route Confusion Attack..."
mantis --evaluate run_artifacts/wp5_route_confusion

echo ""
echo "Evaluating WP5 Tool Mutation Attack..."
mantis --evaluate run_artifacts/wp5_tool_mutation

echo ""
echo "✅ WP6 Evaluation complete."
