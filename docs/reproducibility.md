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

The `TraceEvaluator` calculates seven objective, bounded metrics:
- **Trace Completeness Score (0.0 to 1.0)**: Checks presence of workflow start/end and agent execution events.
- **Tool-Use Correctness Score (0.0 to 1.0)**: Validates required tool invocations and penalizes execution of forbidden tools.
- **Workflow Terminal Outcome Score (0.0 to 1.0)**: Compares observed final outcome with expected ground truth.
- **Artifact Integrity Score (0.0 to 1.0)**: Cryptographically hashes traces.jsonl and ensures run_id matches the run_manifest.json (detects truncation or tampering).
- **Banking Workflow Coverage Score (0.0 to 1.0)**: Reports which banking domains (front_office, mid_office, back_office) were exercised in the traces.
- **Hook Coverage Score (0.0 to 1.0)**: Fraction of the 10 required before/after control-point hook pairs that fired at least once in the run.
- **Attack Ground Truth (applicable / score)**: For a run with a configured attack or failure plugin, reports whether the plugin's security event (`ATTACK_INJECTED` or `ANOMALY`) actually appears in the trace (`attack_fired`) and whether the run's observed tool use or terminal state diverges from the configuration's own `expected_tools`/`expected_terminal_state` baseline (`effect_detected_vs_ground_truth`) -- distinguishing a plugin that fired with no measurable effect from one whose effect is corroborated by ground truth. Reports `applicable: false` (not a score) for a baseline run with no attack configured.

Every `mantis --evaluate` also appends one `EVALUATION_RESULT` trace event per metric to `traces.jsonl`, sharing the run's own `run_id`, so trace and evaluation artifacts are always linkable by the same identifier without a separate join.

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

Output is saved to `results/benchmark_<name>.json` (with automatic CSV and Parquet summaries generated alongside it) including:
- Average latency, standard deviation, and P50/P90/P99 (seconds)
- Throughput (successful runs/second)
- Concurrency & repetition metrics
- Cumulative subprocess CPU time and peak resident memory (`cpu_time_s`, `peak_rss_mb`, via `resource.getrusage(RUSAGE_CHILDREN)` -- POSIX only)
- Mean trace event count per run (`avg_trace_events_per_run`, `null` when `observability.mode: off`)

Three additional `benchmark:` config fields address the confounds in a latency-based overhead measurement:
- **`mock_llm: true`** swaps in a zero-latency stand-in model (no API key needed) so instrumentation cost isn't measured underneath live LLM sampling latency. In practice this alone wasn't sufficient at small sample sizes -- see the paper's Experimental Results for why (per-process startup cost dominates once LLM latency is removed).
- **`scaling_repetitions: [1, 2, 4, 8, ...]`** runs the benchmark once per repetition count instead of a single count (concurrency held fixed), so latency/throughput can be reported as a function of transaction volume. Plot with `mantis.benchmark.plotter.plot_volume_scaling`.
- **`scaling_concurrency: [1, 2, 4, 8, ...]`** runs the benchmark once per concurrency level instead of a single level (repetitions held fixed), so latency/throughput can be reported as a function of concurrent load -- the independent axis from `scaling_repetitions`. Same plotting function; it reads `scaling_axis` from the result JSON to pick the correct x-axis automatically. If both fields are set, `scaling_concurrency` takes precedence.

### Repeated-trial attack efficacy

A single live-model trial per attack config can't distinguish "the model reliably resists this" from "we got lucky once." `scripts/run_attack_efficacy_trials.py` re-runs each of the 5 attack/failure configs `--trials N` times against a real model (no mock -- a deterministic mock would show zero variance and can't characterize live-model behavior), evaluates each run, and reports the `attack_fired` and `effect_detected_vs_ground_truth` rate across the trials to `results/attack_efficacy_trials.json`:

```bash
python scripts/run_attack_efficacy_trials.py --trials 5
```

Requires the banking backend running and a real `UF_NAVIGATOR_API_KEY`.
