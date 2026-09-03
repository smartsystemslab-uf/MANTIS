#!/usr/bin/env bash
# demo_wp7_campaign.sh
# Demonstrates running a full security campaign over a directory of configs and generating a report.

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
echo "🚀  MANTIS WP7: Automated Campaign Execution 🚀"
echo "=========================================================="
echo ""

# The CLI outputs the name of the folder it generated, we need to capture it or just find the newest one.
echo "Running mantis --campaign on 'configs/attacks/'..."
mantis --campaign configs/attacks/ | tee campaign_log.txt

# Find the directory created by the campaign
CAMPAIGN_DIR=$(grep -o "run_artifacts/campaign_run_[0-9]*" campaign_log.txt | head -1)

if [ -z "$CAMPAIGN_DIR" ]; then
    echo "❌ Failed to find campaign directory in output."
    rm campaign_log.txt
    if [ -n "$BACKEND_PID" ]; then kill $BACKEND_PID; fi
    exit 1
fi

rm campaign_log.txt

echo ""
echo "=========================================================="
echo "📊  Generating Markdown Report for $CAMPAIGN_DIR"
echo "=========================================================="
mantis --report "$CAMPAIGN_DIR"

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo ""
echo "WP7 Campaign complete!"
