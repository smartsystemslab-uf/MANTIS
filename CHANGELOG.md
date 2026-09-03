# Changelog

All notable changes to the MANTIS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
