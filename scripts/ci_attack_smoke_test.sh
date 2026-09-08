#!/usr/bin/env bash
# ci_attack_smoke_test.sh
# CI-only smoke test: actually EXECUTES one attacked scenario end to end
# through the real ADK/MCP pipeline (via MANTIS_MOCK_LLM=1, so it needs no
# API key and costs nothing) and asserts the attack plugin genuinely fired,
# rather than just validating config schemas or evaluating pre-committed
# trace data. This is what quickstart.sh does not do on its own.
#
# Uses configs/attacks/ci_mock_prompt_injection.yaml, a CI-only config
# targeting user_proxy_agent (the root LlmAgent) rather than
# wp5_prompt_injection.yaml's real target (transaction_monitoring_agent).
# MockLlm always calls the first declared tool on whichever agent currently
# has control, which for a fresh run is always the root orchestrator -- and
# ADK only allows transfer_to_agent between parent/child/sibling agents (see
# resolve_and_derive_transfer_context in the installed google-adk package),
# so a mock run never reaches deeper agents/tools. prompt_injection mutates
# the real llm_request at the interaction/before_message stage (see
# prompt_injection.py), which requires the target agent to actually make a
# real model call -- true for the root under mock mode, never true for a
# sub-agent -- so the root is the only agent whose attack is meaningfully
# checkable without a real LLM. All five real attack + failure configs are
# covered by scripts/demo_wp5_attacks.sh under a real API key (see
# release_validation.sh), not here.

set -e

if [ ! -d "run_artifacts" ]; then
    echo "ERROR: Must be run from the MANTIS project root."
    exit 1
fi

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "Checking if Banking Backend is running..."
if ! curl -s http://127.0.0.1:8000/docs > /dev/null; then
    echo "-> Starting temporary backend server on port 8000..."
    python -m uvicorn citi_banking_backend.app.main:app --host 127.0.0.1 --port 8000 > /dev/null 2>&1 &
    BACKEND_PID=$!
    sleep 3
else
    BACKEND_PID=""
fi

cleanup() {
    if [ -n "$BACKEND_PID" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

echo ""
echo "[1/2] Running Prompt Injection attack live, under MANTIS_MOCK_LLM=1..."
rm -rf run_artifacts/ci_mock_prompt_injection
MANTIS_MOCK_LLM=1 mantis --run configs/attacks/ci_mock_prompt_injection.yaml

TRACE_FILE="run_artifacts/ci_mock_prompt_injection/traces.jsonl"
if [ ! -f "$TRACE_FILE" ]; then
    echo "❌ ERROR: Trace file not found at $TRACE_FILE -- the run did not execute."
    exit 1
fi

if ! grep -q '"ATTACK_INJECTED"' "$TRACE_FILE"; then
    echo "❌ ERROR: No ATTACK_INJECTED event in $TRACE_FILE -- the attack plugin never actually fired."
    exit 1
fi
echo "✅ Attack fired: ATTACK_INJECTED present in a freshly-executed trace."

echo ""
echo "[2/2] Evaluating the fresh run..."
mantis --evaluate run_artifacts/ci_mock_prompt_injection > /dev/null
if [ ! -f "run_artifacts/ci_mock_prompt_injection/evaluation_results.json" ]; then
    echo "❌ ERROR: evaluation_results.json was not produced."
    exit 1
fi
echo "✅ Evaluation completed on live-executed traces."

echo ""
echo "CI attack smoke test passed: one attacked scenario ran end to end, for real, this run."
