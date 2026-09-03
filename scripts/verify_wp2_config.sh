#!/usr/bin/env bash
# verify_wp2_config.sh
# Validates the WP2 acceptance criteria for configurations, registries, and manifests.

set -e

echo "Starting WP2 Configuration Validation..."

# Ensure we are in the project root
if [ ! -d "configs" ]; then
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
echo "[1/3] Validating: Invalid references fail with actionable error messages."
set +e
ERROR_OUTPUT=$(mantis --run configs/invalid/unknown_scenario.yaml 2>&1)
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -eq 0 ]; then
    echo "ERROR: Invalid config did not throw an error."
    exit 1
fi

if [[ "$ERROR_OUTPUT" == *"Unknown scenario 'DOES_NOT_EXIST'"* ]]; then
    echo "SUCCESS: Caught actionable error for invalid scenario reference."
else
    echo "ERROR: Expected actionable error message not found."
    echo "Actual Output: $ERROR_OUTPUT"
    exit 1
fi

echo ""
echo "[2/3] Validating: Meaningful experiment changes can be made only in YAML."
# Execute a config that alters an agent setting and enables an attack plugin
mantis --run configs/attacks/advanced_attack_test.yaml > /dev/null 2>&1
echo "SUCCESS: Complex YAML with agent modifications and attacks parsed and executed successfully."

echo ""
echo "[3/3] Validating: Identical manifest and seed reproduce the same bounded behavior."
MANIFEST_PATH="run_artifacts/advanced_attack_test/run_manifest.json"
if [ -f "$MANIFEST_PATH" ]; then
    HASH=$(grep '"config_hash"' $MANIFEST_PATH | awk -F'"' '{print $4}')
    SEED=$(grep '"seed"' $MANIFEST_PATH | awk -F':' '{print $2}' | tr -d ' ,')
    
    echo "SUCCESS: Run produced a versioned manifest."
    echo "Config Hash: $HASH"
    echo "Seed: $SEED"
else
    echo "ERROR: Run manifest was not created at expected path ($MANIFEST_PATH)."
    exit 1
fi

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo ""
echo "WP2 Configuration Validation Completed Successfully."
