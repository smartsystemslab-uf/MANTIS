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
