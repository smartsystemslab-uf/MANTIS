import json
from pathlib import Path
from datetime import datetime
from mantis.observability.events import (
    EventType,
    BaseTraceEvent,
    WorkflowEvent,
    AgentEvent,
    ToolEvent,
    InteractionEvent,
    SecurityEvent,
    EvaluationEvent,
)
from mantis.observability.artifacts import TraceArtifactWriter, create_run_manifest
from mantis.config.models import ExperimentConfig, ExperimentMetadata


def test_event_serialization_and_types():
    event = ToolEvent(
        event_type=EventType.TOOL_CALL,
        run_id="run-001",
        tool_name="get_customer_context",
        arguments={"customer_id": "CUST-001"},
        risk_level="high",
        financial_side_effect=False,
    )
    raw_json = event.model_dump_json()
    data = json.loads(raw_json)
    assert data["event_type"] == "TOOL_CALL"
    assert data["tool_name"] == "get_customer_context"
    assert data["arguments"]["customer_id"] == "CUST-001"
    assert data["risk_level"] == "high"
    assert data["financial_side_effect"] is False


def test_tool_event_carries_arguments_hash_not_just_raw_args():
    event = ToolEvent(
        event_type=EventType.TOOL_CALL,
        run_id="run-001",
        tool_name="execute_transfer",
        arguments={"customer_id": "CUST-001", "amount": 9200},
    )
    data = json.loads(event.model_dump_json())
    assert data["arguments_hash"] is not None
    assert len(data["arguments_hash"]) == 64  # SHA256 hex digest


def test_interaction_and_evaluation_events_serialize():
    interaction = InteractionEvent(
        event_type=EventType.MESSAGE_SEND,
        run_id="run-001",
        agent_id="fraud_detection_agent",
        content_hash="abc123",
    )
    assert json.loads(interaction.model_dump_json())["event_type"] == "MESSAGE_SEND"

    evaluation = EvaluationEvent(
        event_type=EventType.EVALUATION_RESULT,
        run_id="run-001",
        evaluator="TraceEvaluator",
        metric="tool_use_correctness",
        score=1.0,
    )
    data = json.loads(evaluation.model_dump_json())
    assert data["event_type"] == "EVALUATION_RESULT"
    assert data["score"] == 1.0


def test_trace_artifact_writer(tmp_path: Path):
    writer = TraceArtifactWriter(str(tmp_path))
    ev1 = WorkflowEvent(
        event_type=EventType.WORKFLOW_START,
        run_id="run-001",
        workflow_id="front_office_monitoring",
    )
    ev2 = SecurityEvent(
        event_type=EventType.ATTACK_INJECTED,
        run_id="run-001",
        stage="tool",
        target="execute_transfer",
        plugin="tool_mutation",
    )
    writer.write_events([ev1, ev2])

    trace_file = tmp_path / "traces.jsonl"
    assert trace_file.exists()

    with open(trace_file, "r") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    assert len(lines) == 2
    assert lines[0]["event_type"] == "WORKFLOW_START"
    assert lines[1]["event_type"] == "ATTACK_INJECTED"
    assert lines[1]["plugin"] == "tool_mutation"


def test_run_manifest_generation(tmp_path: Path):
    cfg = ExperimentConfig(
        experiment=ExperimentMetadata(
            name="manifest_test",
            seed=999,
            domain="front_office",
            workflow="front_office_monitoring",
            scenario="front_office_monitoring",
        )
    )
    manifest_path = create_run_manifest(cfg, tmp_path)
    assert manifest_path.exists()

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert manifest["seed"] == 999
    assert "config_hash" in manifest
    assert len(manifest["config_hash"]) == 64  # SHA256 length
    assert manifest["config"]["experiment"]["name"] == "manifest_test"
