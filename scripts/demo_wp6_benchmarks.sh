#!/usr/bin/env bash
# demo_wp6_benchmarks.sh
# Runs concurrent benchmarks for Observability OFF vs FULL and generates a plot.

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
echo "⏱️  MANTIS WP6: Observability Overhead Benchmarks ⏱️"
echo "=========================================================="
echo ""

# Ensure results directory exists
mkdir -p results

echo "[1/2] Benchmarking Base System (Observability OFF)..."
mantis --benchmark configs/attacks/wp6_benchmark_off.yaml

echo ""
echo "[2/2] Benchmarking System (Observability FULL)..."
mantis --benchmark configs/attacks/wp6_benchmark_full.yaml

echo ""
echo "Creating merged dataset for plotting..."
# Use python to merge the two json files and extract what plotter.py needs
python3 -c '
import json
import os

with open("results/benchmark_wp6_benchmark_off.json") as f:
    d_off = json.load(f)
with open("results/benchmark_wp6_benchmark_full.json") as f:
    d_full = json.load(f)

plot_data = [
    {"mode": "off", "avg_latency_s": d_off.get("avg_latency_s", 0), "concurrency": d_off.get("concurrency", 1)},
    {"mode": "full", "avg_latency_s": d_full.get("avg_latency_s", 0), "concurrency": d_full.get("concurrency", 1)}
]

with open("results/benchmark_merged.json", "w") as f:
    json.dump(plot_data, f)
'

echo "Generating Academic Paper Plot..."
python3 -c '
from mantis.benchmark.plotter import plot_observability_overhead
plot_observability_overhead("results/benchmark_merged.json", "results/observability_overhead.png")
'

if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
fi

echo "WP6 Benchmarks Complete!"
echo "Plots are available in the 'results/' directory."
