#!/usr/bin/env bash
# release_validation.sh
# Master script to validate the entire MANTIS repository before research release.

set -e

if [ ! -d "run_artifacts" ]; then
    echo "ERROR: Must be run from the MANTIS project root."
    exit 1
fi

source .venv/bin/activate

echo "=========================================================="
echo "🚀 MANTIS RELEASE VALIDATION SUITE 🚀"
echo "=========================================================="
echo "This will take 5-10 minutes. Go grab a coffee."
echo ""

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
echo "[1/7] WP0: Verifying Baseline Regression Suite..."
./scripts/verify_baseline_regression.sh

echo ""
echo "[2/7] WP2: Verifying Configuration and Registries..."
./scripts/verify_wp2_config.sh

echo ""
echo "[3/7] WP3: Verifying Hook Bus Interceptions..."
./scripts/demo_wp3_hooks.sh

echo ""
echo "[4/7] WP4: Verifying Observability Trace Artifacts..."
./scripts/verify_wp4_observability.sh

echo ""
echo "[5/7] WP5: Verifying Attack and Failure Plugins..."
./scripts/demo_wp5_attacks.sh

echo ""
echo "[6/7] WP6: Verifying Evaluators and Benchmarking Overhead..."
./scripts/verify_wp6_evaluation.sh
./scripts/demo_wp6_benchmarks.sh

echo ""
echo "[7/7] WP7: Verifying CLI Campaign Orchestration..."
./scripts/demo_wp7_campaign.sh

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo "=========================================================="
echo "✅✅ ALL SYSTEMS GO. MANTIS IS READY FOR RELEASE! ✅✅"
echo "=========================================================="
