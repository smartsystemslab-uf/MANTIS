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


def test_evaluate_instrumentation_overhead_missing_coverage_file(tmp_path: Path):
    trace_file = tmp_path / "traces.jsonl"
    with open(trace_file, "w") as f:
        f.write(json.dumps({"event_type": "EXPERIMENT_START", "timestamp": "2026-01-01T00:00:00"}) + "\n")
        f.write(json.dumps({"event_type": "EXPERIMENT_END", "timestamp": "2026-01-01T00:00:01"}) + "\n")

    evaluator = TraceEvaluator(str(tmp_path))
    assert evaluator.evaluate_instrumentation_overhead() is None


def test_evaluate_instrumentation_overhead_missing_experiment_bounds(tmp_path: Path):
    trace_file = tmp_path / "traces.jsonl"
    with open(trace_file, "w") as f:
        f.write(json.dumps({"event_type": "WORKFLOW_START"}) + "\n")

    with open(tmp_path / "hook_coverage.json", "w") as f:
        json.dump({"plugin_timing_ms": {"observability_plugin": 5.0}}, f)

    evaluator = TraceEvaluator(str(tmp_path))
    assert evaluator.evaluate_instrumentation_overhead() is None


def test_evaluate_instrumentation_overhead_computes_percentages(tmp_path: Path):
    trace_file = tmp_path / "traces.jsonl"
    with open(trace_file, "w") as f:
        f.write(json.dumps({"event_type": "EXPERIMENT_START", "timestamp": "2026-01-01T00:00:00"}) + "\n")
        f.write(json.dumps({"event_type": "EXPERIMENT_END", "timestamp": "2026-01-01T00:00:01"}) + "\n")

    with open(tmp_path / "hook_coverage.json", "w") as f:
        json.dump(
            {"plugin_timing_ms": {"observability_plugin": 100.0, "prompt_injection": 50.0}},
            f,
        )

    evaluator = TraceEvaluator(str(tmp_path))
    res = evaluator.evaluate_instrumentation_overhead()
    assert res is not None
    assert res["total_run_duration_ms"] == 1000.0
    assert res["observability_plugin_ms"] == 100.0
    assert res["observability_overhead_pct"] == 10.0
    assert res["total_instrumentation_overhead_pct"] == 15.0

    # evaluate_all() folds it in under "instrumentation_overhead"
    all_res = evaluator.evaluate_all()
    assert all_res["instrumentation_overhead"]["observability_overhead_pct"] == 10.0
