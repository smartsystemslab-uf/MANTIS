#!/usr/bin/env bash
# scripts/quickstart.sh
# MANTIS Quickstart Script: Validates, inspects, and evaluates an adversarial security scenario.

set -e

echo "=========================================================="
echo "🛡️  MANTIS Research Testbed Quickstart 🛡️"
echo "=========================================================="

# 1. Environment check
if command -v mantis >/dev/null 2>&1; then
    MANTIS_CMD="mantis"
elif [ -f ".venv/bin/mantis" ]; then
    MANTIS_CMD=".venv/bin/mantis"
else
    MANTIS_CMD="python -m mantis.cli.main"
fi

echo "Using MANTIS runner: $MANTIS_CMD"

# 2. Generate and validate schemas
echo ""
echo "[Step 1/5] Generating JSON Schemas..."
$MANTIS_CMD --generate-schemas

# 3. Validate baseline & attack configs
echo ""
echo "[Step 2/5] Validating Configurations..."
$MANTIS_CMD --validate configs/baselines/front_office_baseline.yaml
$MANTIS_CMD --validate configs/attacks/advanced_attack_test.yaml

# 4. Inspect scenario and plugin control points
echo ""
echo "[Step 3/5] Inspecting Attack Plugin & Scenario..."
$MANTIS_CMD --inspect prompt_injection
$MANTIS_CMD --inspect front_office_monitoring

# 5. Check System Inventory
echo ""
echo "[Step 4/5] Checking Banking System Inventory..."
$MANTIS_CMD --inventory > /dev/null
echo "✅ System inventory generated successfully."

# 6. Evaluation of Security Experiment
echo ""
echo "[Step 5/5] Evaluating Pre-computed or Live Experiment Artifacts..."
if [ -d "run_artifacts/advanced_attack_test" ]; then
    $MANTIS_CMD --evaluate run_artifacts/advanced_attack_test
    echo "✅ Evaluation completed successfully."
elif [ -d "run_artifacts/wp5_prompt_injection" ]; then
    $MANTIS_CMD --evaluate run_artifacts/wp5_prompt_injection
    echo "✅ Evaluation completed successfully."
else
    echo "Notice: No prior run artifact found. Initializing sample workspace."
    $MANTIS_CMD --init sample_workspace
    echo "✅ Quickstart initialization completed."
fi

echo ""
echo "=========================================================="
echo "🎉 MANTIS Quickstart Completed Successfully! 🎉"
echo "=========================================================="
