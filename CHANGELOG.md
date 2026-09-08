# Changelog

All notable changes to the MANTIS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-09-07

### Added (repeated-trial and concurrency-scaling evidence)
- `benchmark.scaling_concurrency` config field: sweeps concurrency at a fixed repetition count, independent of `scaling_repetitions` (which sweeps repetition count at fixed concurrency) -- closes the "benchmark sweep across concurrency levels" gap. Takes precedence if both are set.
- Fixed a bug in `plotter.plot_volume_scaling` caught before it shipped: it hardcoded `repetitions` as the x-axis key regardless of which axis was actually varied, which would have plotted a concurrency-scaling result as four identical x-values. Now reads `scaling_axis` from the result and picks the correct key/label; regression tests added (`tests/unit/test_plotter.py`).
- `scripts/run_attack_efficacy_trials.py`: repeats each of the 5 attack/failure configs N times against a real model (no mock -- a deterministic mock can't characterize live-model variance) and reports the `attack_fired`/`effect_detected_vs_ground_truth` rate across trials. Closes the "repeated-trial attack efficacy" gap: prior evidence was one live trial per attack.
- Ran with `--trials 5`: route confusion diverts the workflow 5/5 trials; message spoofing, prompt injection, and the malformed-failure control are genuinely mutated/reached every trial but produce no detectable effect in this sample (0/5); tool mutation (front office) surfaced that its scenario never once produces an `execute_transfer` call across 5 fresh trials -- a fixture-design gap only visible by repeating the trial, not a plugin defect.
- Volume-scaling (repetition-count sweep) now run to the same depth (1/2/4/8 reps) on mid- and back-office workflows, not just a single-point comparison -- both reproduce the front office's amortize-then-plateau curve closely.
- Concurrency sweep (1/2/4/8) run on the front-office workflow: throughput scales with concurrent load while latency stays flat through concurrency 4 and degrades sharply at 8, directly confirming the shared-CPU-contention explanation for why a naive live-model off/full comparison came out backwards.
- Paper, README-adjacent docs (`docs/reproducibility.md`), and the presentation deck updated with all of the above.

### Fixed (critical: attack plugins had no real effect)
- **`HookBus.dispatch()` silently discarded every upstream mutation.** Its final return hardcoded `action=CONTINUE` whenever the last-dispatched plugin (`ObservabilityPlugin`, always registered last so it can observe an attack's effect) did not itself mutate the payload -- meaning the aggregate result of *every* dispatch containing an earlier plugin's mutation still reported `CONTINUE`, and the ADK integration layer only applies a dispatch's payload to the real tool/LLM call when the reported action is exactly `MUTATE`. This affected every attack plugin, at every stage, on every run since the mechanism was first written.
- **`before_tool_callback` treated a mutated payload as a substitute tool *response*, not modified arguments.** The underlying agent framework's plugin contract skips calling the real tool entirely when `before_tool_callback` returns a non-`None` value. Returning the mutated payload there (as opposed to mutating `tool_args` in place and returning `None`) caused the framework to fabricate a fake response instead of calling the real tool (e.g. `transfer_to_agent`, `execute_transfer`) with the attacker-controlled arguments.
- **`HookBus.dispatch()` also short-circuited on DENY/SKIP/ERROR**, skipping every later-registered plugin (again, `ObservabilityPlugin`) entirely -- a blocked/denied/errored action (e.g. every `ReliabilityFailurePlugin` trial) produced no `TOOL_CALL` or security event at all, making the block invisible to the trace even though it worked. Blocking actions now still reach later plugins before being enforced.
- **`message_spoofing` and `prompt_injection` mutated attributes that don't exist on the real request object.** The real `google.genai.types.Content`/`Part` objects the agent framework actually passes into a model call expose only `role` and `parts` (each optionally carrying `text`) -- verified directly against the installed package -- not `.content`/`.sender`. Both plugins silently matched neither branch of their own mutation logic on every real run while still reporting a mutation; both now mutate the real `Part.text`.
- **`prompt_injection` targeted control points with no real effect.** `before_input`/`before_agent` never write a mutated payload back onto the real invocation in this ADK integration (only `SKIP`/`DENY` are handled there); moved to the `interaction` stage, the only stage wired for real effect on an outgoing model request.
- **`route_confusion`'s shipped config targeted an unreachable hop.** `front_office_monitoring`'s inner agent sequence (monitoring → fraud → compliance → decision) is invoked via direct Python calls, never through the framework's `transfer_to_agent` routing tool, so the attack could never fire regardless of correct argument matching. Retargeted to the front-office router's real routing decision (transaction-review workflow vs. customer-service chatbot workflow).
- All five attack/failure configurations re-verified live against a real model after the above fixes; each now produces a genuine, ground-truth-corroborated effect (see `docs/reproducibility.md` and the paper's Table on live-verified evidence).

### Added
- Two new scored evaluator dimensions: **`hook_coverage`** (fraction of the 10 required control-point hook pairs that fired) and **`attack_ground_truth`** (whether a configured attack/failure plugin fired and whether its effect is corroborated by the run's expected-tools/terminal-state baseline) -- bringing the evaluation framework to 7 scored dimensions plus instrumentation overhead.
- `ANOMALY` security event type now emitted for reliability/failure plugins (previously declared but unused), kept distinct from `ATTACK_INJECTED` so an evaluator can separate an operational fault from an adversarial one.
- `EVALUATION_RESULT` events are appended to `traces.jsonl` after every `mantis --evaluate`, sharing the run's own `run_id` with every other event.
- **Artifact-integrity evaluator**: re-hashes `traces.jsonl` and cross-checks its `run_id` against the manifest.
- **Banking-workflow-coverage evaluator**: reports which of the three domains were exercised in a run or campaign.
- CSV and Parquet summary export alongside every `mantis --benchmark` JSON result.
- CPU time, peak resident memory, and mean trace-event count per run, reported by `mantis --benchmark` alongside latency/throughput.
- New mid-office and back-office mock-LLM benchmark configs, closing a front-office-only gap in instrumentation-overhead measurement.
- A `configs/attacks/wp5_failure_malformed.yaml` reliability-failure demo config and live run (the plugin family previously had no config or run artifact at all).
- `BankingRuntimeAdapter` is now `@runtime_checkable`, with a structural `isinstance` contract test (previously the contract test only checked individual method names).
- Two pytest-level end-to-end tests (`tests/unit/test_integration_offline.py`): a baseline `--run` and an **attacked** `--run` under a mock model asserting a genuine `ATTACK_INJECTED` event and a corroborating `attack_ground_truth` evaluation -- this coverage previously existed only as a shell script, not a collected test.
- `tests/unit/test_adapter_contract.py`: contract tests for `NativeBankingAdapter` against the `BankingRuntimeAdapter` protocol.
- Campaign report (`mantis --report`) now includes an "Attack Effect" column distinguishing "attack fired, effect detected," "fired, no effect this trial," and "did not fire" -- a bare completeness/correctness "FAIL" was ambiguous between "something broke" and "the attack's effect was correctly detected."
- `src/mantis/__main__.py`, so `python -m mantis` works (previously only the installed `mantis` console script or `python -m mantis.cli.main` did).
- `.env` added to `.gitignore` (it was not previously excluded, even though nothing had been committed under that name).

### Changed
- `mantis --run` failures now print a concise one-line error by default (matching `--validate`'s existing behavior); the full traceback is available via `MANTIS_DEBUG=1`.
- CI's "Unit Tests" step now starts the banking backend first, rather than relying on later steps (`quickstart.sh`, the attack smoke test) to have already started it, or on the specific tests exercised not needing it.
- Removed `configs/advanced_experiment.yaml` (an unreferenced, stale duplicate of `configs/attacks/advanced_attack_test.yaml`) and the repo-root `test_plugin.py` (dead pre-refactor code importing a module path, `mantis.core.hooks`, that no longer exists).

## [0.1.0] - 2026-09-03

### Added
- **WP0**: Baseline characterization across Front, Mid, and Back-Office workflows with 49 regression guard tests and frozen golden runs.
- **WP1**: Modular banking architecture via `NativeBankingAdapter` and formal package structure.
- **WP2**: Declarative YAML configuration engine, Pydantic schemas, and dynamic scenario/plugin registries.
- **WP3**: Non-invasive `HookBus` middleware intercepting 5 lifecycle control points (`input`, `agent`, `interaction`, `tool`, `output`).
- **WP4**: Multi-backend observability pipeline with OpenTelemetry distributed tracing, MLflow experiment tracking, and standardized JSONL trace logging.
- **WP5**: Suite of 4 adversarial security plugins (Prompt Injection, Message Spoofing, Route Confusion, Tool Mutation) and reliability failure controls.
- **WP6**: Automated evaluation engine (`TraceEvaluator`) and latency/overhead benchmark runner (`BenchmarkRunner`).
- **WP7**: Full CLI interface (`mantis`) supporting campaign orchestration, schema generation, system inventory, and markdown reports.
- **WP8**: CI/CD automation, comprehensive unit test suite, complete documentation suite, Docker Compose deployment, and release validation suite.

### Fixed
- `after_input`, `after_agent`, `after_message`, and `before_output` hooks never fired in any run (`hook_coverage.json` showed 0 hits on all four in every captured trace); the four missing ADK callbacks are now wired up and verified live -- all 10 hook points fire on every run.
- `workflow_outcome` was hardcoded to `"completed"` regardless of what actually happened; it now reflects the real terminal state inferred from the terminal tool actually called (e.g. `manual_review`, `executed`).
- `business_domain`, `workflow_type`, `operation_type`, `risk_level`, `data_sensitivity`, and `financial_side_effect` were always `null` on every trace event despite being part of the schema; they're now populated from the run context and a banking tool-semantics table.
- `EVALUATION_RESULT` and `InteractionEvent` (`MESSAGE_SEND`/`MESSAGE_RECEIVE`) event types existed in the schema but were never emitted; both are now wired into the trace pipeline.
- `TraceArtifactWriter` silently appended events across repeated runs of the same experiment name, including campaign subprocess runs, corrupting evaluation results with stale data from previous runs; each run now starts its trace file clean.
- `domain_registry`, `workflow_registry`, `exporter_registry`, and `evaluator_registry` were declared but never populated or consulted; they're now populated from `mantis.banking`, and `mantis --validate` checks domain/workflow/attack-target/control-point against them.
- `inventory()` returned a hardcoded 4-agent/2-tool stub; it now introspects the real banking tool modules and agent registry (31 agents, 19+ tools).
- `experiment.seed` was recorded in the manifest but never actually applied; it's now wired into `random.seed()` and the model call.
- Removed a hardcoded LLM API key fallback from `mantis.banking.settings` (now requires `UF_NAVIGATOR_API_KEY` from the environment, see `.env.example`).
- Fixed `citi_banking_mcp_server`'s test suite, which was silently failing 2 of 3 tests due to a missing `pytest-asyncio` dependency not covered by any CI or validation script.
