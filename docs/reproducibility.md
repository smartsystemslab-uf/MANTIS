# Reproducibility and Benchmarking

A core objective of MANTIS is making every published security and observability claim traceable back to a specific configuration, environment, and (bounded, not exact) execution. Agents are backed by a live LLM, so a fixed seed narrows run-to-run variance in exact wording but does not eliminate it -- evaluators score bounded, semantic properties (which tools were called, what terminal state was reached) rather than exact text.

---

## 1. Run Manifests & Cryptographic Hashes

Every MANTIS execution creates a `run_manifest.json` in the run directory containing:
- **`config_hash`**: SHA-256 digest of the normalized configuration.
- **`seed`**: Integer seed used for pseudo-random number generators and bounded sampling.
- **`timestamp`**: UTC ISO-8601 execution time.
- **`config`**: Complete frozen copy of the configuration.
- **`environment`**: Python interpreter version, installed versions of every framework-critical dependency, platform string, and the source repository's git commit -- so a result can be traced back to exactly what produced it, not just the config that requested it.

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
- Average latency, standard deviation, and P50/P90/P99 (seconds)
- Throughput (successful runs/second)
- Concurrency & repetition metrics

Two additional `benchmark:` config fields address the two biggest confounds in a latency-based overhead measurement:
- **`mock_llm: true`** swaps in a zero-latency stand-in model (no API key needed) so instrumentation cost isn't measured underneath live LLM sampling latency. In practice this alone wasn't sufficient at small sample sizes -- see the paper's Experimental Results for why (per-process startup cost dominates once LLM latency is removed).
- **`scaling_repetitions: [1, 2, 4, 8, ...]`** runs the benchmark once per repetition count instead of a single count, so latency/throughput can be reported as a function of transaction volume. Plot with `mantis.benchmark.plotter.plot_volume_scaling`.
