# Observability Pipeline

MANTIS features a multi-backend telemetry architecture designed for security audits, causality reconstruction, and overhead benchmarking.

---

## 1. Observability Modes

Configured via `observability.mode` in the experiment YAML:

- **`off`**: No tracing or telemetry instrumentation overhead.
- **`selective`**: Traces security events, route transitions, and tool invocations only.
- **`full`**: Exhaustive event streaming capturing every agent thought, message, tool payload, and telemetry span.

---

## 2. Supported Exporters

Configured via `observability.export`:

1. **JSONL Traces (`jsonl`)**:
   - Always stored in `run_artifacts/<experiment>/traces.jsonl`.
   - Line-delimited JSON with ISO-8601 UTC timestamps, causal IDs, and typed event schemas.

2. **OpenTelemetry (`otel`)**:
   - Initializes the SDK `TracerProvider` for the run; attaches a console exporter when explicitly requested. On its own this makes spans creatable but doesn't ship them anywhere -- pair it with `jaeger` (below), or attach another OTLP-compatible processor, to actually export.

3. **MLflow (`mlflow`)**:
   - Run parameters, seeds, SHA-256 configuration hashes, and artifact files logged automatically to local or remote MLflow tracking servers.

4. **Jaeger (`jaeger`)** -- *Post-Paper Extension, coding plan §11 "Additional exporters"*:
   - Attaches a real OTLP-over-gRPC span exporter (`mantis.observability.jaeger_exporter`) to the same `TracerProvider`, pointed at `observability.jaeger_endpoint` (default `http://localhost:4317`). Requires the optional `exporters` dependency group (`pip install -e ".[exporters]"`).
   - Enabling it is config-only: `observability.export: [jsonl, jaeger]` -- no code change to the banking workflow, the hook bus, or the observability plugin. See `configs/extensions/jaeger_export_demo.yaml`.
   - If no collector is listening at the configured endpoint, export fails quietly in the background (retried and logged by the SDK's `BatchSpanProcessor`); a run's success never depends on telemetry actually being delivered.

5. **Grafana Tempo (`grafana`)** -- *Post-Paper Extension, coding plan §11 "Additional exporters"*:
   - The same OTLP-over-gRPC adapter shape as Jaeger (`mantis.observability.grafana_exporter`), pointed at `observability.grafana_endpoint` (default `http://localhost:4317`). Optionally set `observability.grafana_auth_header` (e.g. `"Basic <base64>"`) for a managed Grafana Cloud OTLP gateway; a local Tempo collector needs no auth. See `configs/extensions/grafana_export_demo.yaml`.
   - `observability.export: [jsonl, grafana]` -- config-only, same fail-silent-without-a-collector behavior as Jaeger.

6. **Phoenix (`phoenix`)** -- *Post-Paper Extension, coding plan §11 "Additional exporters"*:
   - The same OTLP-over-gRPC adapter shape as Jaeger (`mantis.observability.phoenix_exporter`), pointed at `observability.phoenix_endpoint` (default `http://localhost:4317`). Optionally set `observability.phoenix_api_key` for a managed Phoenix Cloud instance; a local `phoenix serve` collector needs no auth. See `configs/extensions/phoenix_export_demo.yaml`.
   - `observability.export: [jsonl, phoenix]` -- config-only, same fail-silent-without-a-collector behavior as Jaeger.

7. **Langfuse (`langfuse`)** -- *Post-Paper Extension, coding plan §11 "Additional exporters"*:
   - Unlike the other three, Langfuse's OTLP ingestion endpoint is HTTP/protobuf only and always requires HTTP Basic auth (a Langfuse public/secret key pair), even self-hosted -- so `mantis.observability.langfuse_exporter` is built on the OTLP/HTTP exporter, not `.grpc`. Pointed at `observability.langfuse_endpoint` (default Langfuse Cloud); set `observability.langfuse_public_key`/`langfuse_secret_key` to a real project's keys. See `configs/extensions/langfuse_export_demo.yaml`.
   - `observability.export: [jsonl, langfuse]` -- config-only; an unreachable endpoint or rejected credentials fail the same way an unreachable collector does elsewhere -- quietly, in the background, never failing the run.

---

## 3. Trace Event Hierarchy

- `EXPERIMENT_START` / `EXPERIMENT_END`: Lifecycle of the run, with config hash, seed, and status.
- `WORKFLOW_START` / `WORKFLOW_END`: Workflow boundary and terminal outcome.
- `ROUTE_DECISION`: A real `transfer_to_agent` routing decision, with source, target, and step.
- `AGENT_START` / `AGENT_END` / `AGENT_ERROR`: Agent activation, role, execution latency, and errors.
- `MESSAGE_SEND` / `MESSAGE_RECEIVE` / `MESSAGE_MUTATE`: Inter-agent communication.
- `TOOL_CALL` / `TOOL_RESULT` / `TOOL_ERROR`: Tool invocations, parameters, and side-effects.
- `ATTACK_INJECTED`: Adversarial security event with injection stage, plugin, target, and observed effect.
- `ANOMALY`: Operational security event for a reliability/failure plugin (delay, timeout, malformed result) -- kept distinct from `ATTACK_INJECTED` so an evaluator can separate a security-caused anomaly from a routine fault.
- `POLICY_EVENT`: A defensive/policy plugin's action (`amount_limit_guardrail`, `risk_aware_routing_guard`, `response_redaction`, `batch_integrity_guard`, `rate_limit_guardrail`, `action_isolation` -- Post-Paper Extension, coding plan §11 "Security mechanism plugins") -- kept distinct from `ATTACK_INJECTED` for the same reason `ANOMALY` is kept distinct from it: a guardrail denying (or a response filter mutating) a call is the system working as intended, not an attack. See `docs/add_plugin.md`. A policy plugin developed outside this repo can register its own name into this classification without a code change here -- see the comment on `mantis.observability.plugin._POLICY_PLUGIN_NAMES`.
- `EVALUATION_RESULT`: Post-run metric results (one per evaluator, all 7 dimensions -- see `docs/reproducibility.md`) appended to traces automatically by `mantis --evaluate`, sharing the run's own `run_id`.
