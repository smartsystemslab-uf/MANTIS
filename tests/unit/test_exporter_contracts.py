"""§8 Testing Strategy, Contract row: "Adapter and registries; MLflow plus
JSONL artifact writer." TraceArtifactWriter and MLflowExporter don't share
method names -- one appends line-delimited events, the other manages an
MLflow run lifecycle -- so the contract that actually matters between them
isn't a common Python interface, it's the property spec §5.4/WP4 states
explicitly: "trace and evaluation artifacts share stable IDs." This
verifies that property directly: the same run identity, logged through
both exporters for the same run, is recoverable identically from each --
checked against MLflow's own store and a real re-read JSONL file, not a
mock of either.
"""
import json
from pathlib import Path

import mlflow

from mantis.observability.artifacts import TraceArtifactWriter
from mantis.observability.mlflow_exporter import MLflowExporter
from mantis.observability.events import EventType, ExperimentEvent, WorkflowEvent


def test_jsonl_and_mlflow_exporters_agree_on_the_same_run_identity(tmp_path: Path):
    run_id = "contract_test_run_001"
    config_hash = "deadbeef1234"
    seed = 7

    # Same run, exported through both channels -- exactly what a real
    # `observability.export: [jsonl, mlflow]` run does.
    jsonl_writer = TraceArtifactWriter(str(tmp_path))
    jsonl_writer.write_events([
        ExperimentEvent(event_type=EventType.EXPERIMENT_START, run_id=run_id, config_hash=config_hash, seed=seed, status="running"),
        WorkflowEvent(event_type=EventType.WORKFLOW_START, run_id=run_id, workflow_id="front_office_monitoring"),
        ExperimentEvent(event_type=EventType.EXPERIMENT_END, run_id=run_id, config_hash=config_hash, seed=seed, status="success"),
    ])

    tracking_uri = f"sqlite:///{tmp_path / 'mlflow_contract.db'}"
    mlflow_exporter = MLflowExporter(tracking_uri=tracking_uri, experiment_name="contract_test")
    mlflow_exporter.start_run(run_name=run_id, config_hash=config_hash, seed=seed)
    active_run_id = mlflow_exporter.active_run_id
    mlflow_exporter.log_artifact(str(tmp_path / "traces.jsonl"))
    mlflow_exporter.end_run()

    # Independently re-read each artifact from its own real store -- no
    # mocking either exporter.
    trace_events = [json.loads(line) for line in (tmp_path / "traces.jsonl").read_text().splitlines() if line.strip()]
    mlflow.set_tracking_uri(tracking_uri)
    mlflow_run = mlflow.get_run(active_run_id)

    # The contract: both artifacts, read back independently, agree this
    # was the same run -- same run_id in the trace, same config_hash and
    # seed as MLflow params, for every trace event.
    assert all(e["run_id"] == run_id for e in trace_events)
    assert mlflow_run.data.params["config_hash"] == config_hash
    assert mlflow_run.data.params["seed"] == str(seed)
    assert all(e["config_hash"] == config_hash for e in trace_events if "config_hash" in e)

    # And the JSONL file itself made it into the MLflow run as a real,
    # independently-fetchable artifact -- not just referenced by name.
    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)
    artifact_names = {a.path for a in client.list_artifacts(active_run_id)}
    assert "traces.jsonl" in artifact_names


def test_trace_artifact_writer_round_trips_every_field_of_a_real_event(tmp_path: Path):
    """The JSONL side of the same contract: what goes in comes back out
    identically, for a real typed event, not a hand-built dict."""
    from mantis.observability.events import SecurityEvent

    writer = TraceArtifactWriter(str(tmp_path))
    original = SecurityEvent(
        event_type=EventType.ATTACK_INJECTED,
        run_id="round-trip-run",
        stage="tool",
        target="execute_transfer",
        plugin="tool_mutation",
        observed_impact="mutate",
    )
    writer.write_event(original)

    lines = [json.loads(l) for l in (tmp_path / "traces.jsonl").read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    round_tripped = lines[0]
    original_dict = json.loads(original.model_dump_json())
    assert round_tripped == original_dict
