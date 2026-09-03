# Reproducibility and Benchmarking

A core objective of MANTIS is ensuring all published security and observability claims are 100% reproducible.

---

## 1. Run Manifests & Cryptographic Hashes

Every MANTIS execution creates a `run_manifest.json` in the run directory containing:
- **`config_hash`**: SHA-256 digest of the normalized configuration.
- **`seed`**: Integer seed used for pseudo-random number generators and bounded sampling.
- **`timestamp`**: UTC ISO-8601 execution time.
- **`config`**: Complete frozen copy of the configuration.

---

## 2. Automated Trace Evaluation

The `TraceEvaluator` calculates objective, bounded metrics:
- **Trace Completeness Score (0.0 to 1.0)**: Checks presence of workflow start/end and agent execution events.
- **Tool-Use Correctness Score (0.0 to 1.0)**: Validates required tool invocations and penalizes execution of forbidden tools.
- **Workflow Terminal Outcome Score (0.0 to 1.0)**: Compares observed final outcome with expected ground truth.

Run evaluation via CLI:
```bash
mantis --evaluate run_artifacts/<experiment_name>
```

---

## 3. Benchmarking Overhead

To benchmark instrumentation overhead across modes (`off`, `selective`, `full`):

```bash
mantis --benchmark configs/baselines/front_office_baseline.yaml
```

Output is saved to `results/benchmark_<name>.json` including:
- Average Latency (seconds)
- Latency P50, P90, P99
- Concurrency & repetition metrics
