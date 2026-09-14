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
   - If no collector is listening at the configured endpoint, export fails quietly in the background (retried and logged by the SDK's `BatchSpanProcessor`); a run's success never depends on telemetry actually being delivered. Grafana, Langfuse, and Phoenix are documented, not-yet-built extension points that would follow this exact same adapter pattern -- register a `setup_<backend>_otel`-shaped function in `exporter_registry`, and wiring into `observability.export` is unchanged.

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
- `POLICY_EVENT`: Reserved for a future policy/guardrail plugin (Zero Trust extension point); declared in the event model but not currently emitted by any shipped plugin.
- `EVALUATION_RESULT`: Post-run metric results (one per evaluator, all 7 dimensions -- see `docs/reproducibility.md`) appended to traces automatically by `mantis --evaluate`, sharing the run's own `run_id`.
