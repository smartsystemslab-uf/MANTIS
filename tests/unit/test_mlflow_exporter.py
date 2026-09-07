import mlflow
from mantis.observability.mlflow_exporter import MLflowExporter


def test_full_run_lifecycle_is_queryable_afterward(tmp_path):
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    exporter = MLflowExporter(tracking_uri=tracking_uri, experiment_name="mantis_contract_test")

    trace_file = tmp_path / "traces.jsonl"
    trace_file.write_text('{"event_type": "WORKFLOW_START"}\n')

    exporter.start_run(run_name="contract_test_run", config_hash="abc123", seed=42)
    run_id = exporter.active_run_id
    assert run_id, "start_run should set an active_run_id"

    exporter.log_metrics({"trace_completeness": 1.0})
    exporter.log_artifact(str(trace_file))
    exporter.end_run()

    assert exporter.active_run_id is None  # end_run clears it

    # Verify against MLflow's own store, not just "no exception was raised".
    mlflow.set_tracking_uri(tracking_uri)
    run = mlflow.get_run(run_id)
    assert run.data.params["config_hash"] == "abc123"
    assert run.data.params["seed"] == "42"
    assert run.data.metrics["trace_completeness"] == 1.0
    assert run.info.status == "FINISHED"

    client = mlflow.tracking.MlflowClient(tracking_uri=tracking_uri)
    artifacts = [a.path for a in client.list_artifacts(run_id)]
    assert "traces.jsonl" in artifacts


def test_operations_before_start_run_are_safely_no_ops(tmp_path):
    tracking_uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    exporter = MLflowExporter(tracking_uri=tracking_uri, experiment_name="mantis_contract_test_2")

    # No start_run() call -- these must not raise, per their own
    # "if not self.active_run_id: return" guards.
    exporter.log_metrics({"x": 1.0})
    exporter.log_artifact(str(tmp_path / "does_not_exist.jsonl"))
    exporter.end_run()
