import json
from pathlib import Path
from mantis.evaluation.evaluators import TraceEvaluator


def test_evaluator_empty_dir(tmp_path: Path):
    evaluator = TraceEvaluator(str(tmp_path))
    res = evaluator.evaluate_all()
    assert "error" in res


def test_evaluator_trace_completeness(tmp_path: Path):
    trace_file = tmp_path / "traces.jsonl"
    events = [
        {"event_type": "WORKFLOW_START", "workflow_id": "front_office"},
        {"event_type": "AGENT_START", "agent_id": "monitoring_agent"},
        {"event_type": "TOOL_CALL", "tool_name": "get_customer_context"},
        {"event_type": "WORKFLOW_END", "outcome": "completed"},
    ]
    with open(trace_file, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    evaluator = TraceEvaluator(str(tmp_path))
    res = evaluator.evaluate_completeness()
    assert res["score"] == 1.0
    assert res["has_workflow_start"] is True
    assert res["has_workflow_end"] is True
    assert res["has_agent_start"] is True
    assert res["total_events"] == 4


def test_evaluator_incomplete_trace(tmp_path: Path):
    trace_file = tmp_path / "traces.jsonl"
    events = [
        {"event_type": "WORKFLOW_START", "workflow_id": "front_office"},
        # missing AGENT_START and WORKFLOW_END
    ]
    with open(trace_file, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    evaluator = TraceEvaluator(str(tmp_path))
    res = evaluator.evaluate_completeness()
    assert res["score"] == 0.0
    assert res["has_workflow_end"] is False


def test_evaluator_tool_use_correctness_with_manifest(tmp_path: Path):
    manifest = {
        "config": {
            "evaluation": {
                "expected_tools": ["get_customer_context"],
                "forbidden_tools": ["execute_unauthorized_transfer"],
            }
        }
    }
    with open(tmp_path / "run_manifest.json", "w") as f:
        json.dump(manifest, f)

    # Valid trace (used expected tool, avoided forbidden tool)
    trace_file = tmp_path / "traces.jsonl"
    with open(trace_file, "w") as f:
        f.write(
            json.dumps(
                {"event_type": "TOOL_CALL", "tool_name": "get_customer_context"}
            )
            + "\n"
        )

    evaluator = TraceEvaluator(str(tmp_path))
    res = evaluator.evaluate_tool_use()
    assert res["score"] == 1.0
    assert "get_customer_context" in res["actual_tools"]
    assert res["missing_expected"] == []
    assert res["used_forbidden"] == []

    # Invalid trace (used forbidden tool)
    with open(trace_file, "a") as f:
        f.write(
            json.dumps(
                {
                    "event_type": "TOOL_CALL",
                    "tool_name": "execute_unauthorized_transfer",
                }
            )
            + "\n"
        )

    evaluator2 = TraceEvaluator(str(tmp_path))
    res2 = evaluator2.evaluate_tool_use()
    assert res2["score"] == 0.0
    assert "execute_unauthorized_transfer" in res2["used_forbidden"]
