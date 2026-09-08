"""Offline integration test (spec §8, Integration layer — Gap 6).

Chains: mantis --run (MANTIS_MOCK_LLM=1) -> validates traces.jsonl structure
        -> mantis --evaluate -> asserts evaluation_results.json is produced
        with non-zero scores.

Uses a real subprocess so the full CLI entry point, plugin registry,
HookBus dispatch, and TraceEvaluator path are all exercised end-to-end
without any LLM or network calls (MANTIS_MOCK_LLM=1 + no MCP server).

The front_office_monitoring config is chosen as the representative scenario
covering the front-office domain (spec §8: "At least one front-, mid-,
and back-office workflow with representative tool/API use").
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MANTIS_CMD = [sys.executable, "-m", "mantis.cli.main"]

# Use the simplest baseline config -- no MCP server needed when MOCK_LLM=1
# because the mock bypasses real model calls but the ADK/MCP path is still
# exercised (the smoke test already validates live ADK; this test validates
# the evaluation pipeline offline).
CONFIG_FILE = Path(__file__).parents[2] / "configs" / "baselines" / "front_office_baseline.yaml"


def _run_mantis(args: list[str], extra_env: dict = None, timeout: int = 120) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["MANTIS_MOCK_LLM"] = "1"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        MANTIS_CMD + args,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Gap 6a -- mantis --validate works offline (sanity check before heavier steps)
# ---------------------------------------------------------------------------

def test_validate_baseline_config_passes():
    """--validate must succeed without any network/LLM calls."""
    result = _run_mantis(["--validate", str(CONFIG_FILE)])
    assert result.returncode == 0, (
        f"--validate failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "valid" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Gap 6b -- mantis --inventory returns all three domains
# ---------------------------------------------------------------------------

def test_inventory_covers_three_domains():
    result = _run_mantis(["--inventory"])
    assert result.returncode == 0, f"--inventory failed: {result.stderr}"
    inv = json.loads(result.stdout)
    domains = set(inv.get("domains", {}).keys())
    assert {"front_office", "mid_office", "back_office"}.issubset(domains), (
        f"inventory missing domains, got: {domains}"
    )

# ---------------------------------------------------------------------------
# Gap 6c -- mantis --run -> produces traces.jsonl + run_manifest.json
# This test requires the MCP server to be launchable from the repo root.
# It is skipped when the MCP server script is not found.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parents[2]
_MCP_SERVER = (
    _REPO_ROOT / "citi_banking_mcp_server" / "mcp_server.py"
)
_MCP_SERVER_LEGACY = (
    _REPO_ROOT / "legacy_code" / "citi_banking_mcp_server" / "mcp_server.py"
)
_HAS_MCP_SERVER = _MCP_SERVER.exists() or _MCP_SERVER_LEGACY.exists()

try:
    import google.adk  # noqa: F401
    _HAS_ADK = True
except ImportError:
    _HAS_ADK = False

# The full --run test requires ADK + MCP server both present.
_SKIP_RUN_TEST = not (_HAS_MCP_SERVER and _HAS_ADK)


@pytest.mark.skipif(
    _SKIP_RUN_TEST,
    reason="google.adk or MCP server not available; full --run integration skipped in this environment",
)
def test_run_produces_trace_and_manifest(tmp_path):
    """Full chain: --run (mock LLM) -> traces.jsonl exists with events.

    The subprocess runs from _REPO_ROOT so the MCP server path lookup
    succeeds. run_artifacts land in a tmp subdir via RUN_ARTIFACTS_DIR
    override (not yet wired) — for now we check under _REPO_ROOT and clean up.
    """
    import shutil

    run_name = "front_office_monitoring"
    run_artifacts_dir = _REPO_ROOT / "run_artifacts" / run_name

    env = os.environ.copy()
    env["MANTIS_MOCK_LLM"] = "1"

    result = subprocess.run(
        MANTIS_CMD + ["--run", str(CONFIG_FILE)],
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"--run failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Locate the run artifact directory
    assert run_artifacts_dir.exists(), f"run_artifacts dir not created at {run_artifacts_dir}"

    trace_file = run_artifacts_dir / "traces.jsonl"
    assert trace_file.exists(), "traces.jsonl not found after --run"
    assert trace_file.stat().st_size > 0, "traces.jsonl is empty"

    manifest_file = run_artifacts_dir / "run_manifest.json"
    assert manifest_file.exists(), "run_manifest.json not found after --run"
    manifest = json.loads(manifest_file.read_text())
    assert "config_hash" in manifest
    assert "seed" in manifest

    # Spot-check at least one WORKFLOW_START event in the trace
    events = [json.loads(ln) for ln in trace_file.read_text().splitlines() if ln.strip()]
    event_types = {e.get("event_type") for e in events}
    assert "WORKFLOW_START" in event_types, (
        f"No WORKFLOW_START in trace; found: {event_types}"
    )


# ---------------------------------------------------------------------------
# WP8 -- pytest-level end-to-end test for an ATTACKED workflow (not just
# baseline). Previously this coverage existed only in
# scripts/ci_attack_smoke_test.sh (a shell script, not collected by pytest).
# Uses ci_mock_prompt_injection.yaml, which targets user_proxy_agent (the
# root LlmAgent) specifically because MockLlm's routing can only ever reach
# the root -- see that config's own comments and prompt_injection.py.
# ---------------------------------------------------------------------------

_CI_ATTACK_CONFIG = _REPO_ROOT / "configs" / "attacks" / "ci_mock_prompt_injection.yaml"


@pytest.mark.skipif(
    _SKIP_RUN_TEST,
    reason="google.adk or MCP server not available; full --run integration skipped in this environment",
)
def test_run_attacked_workflow_fires_for_real():
    """Full chain for an ATTACKED workflow: --run (mock LLM) -> a real
    ATTACK_INJECTED event in traces.jsonl (not just a clean exit) -> --evaluate
    produces attack_ground_truth confirming the plugin fired.
    """
    run_name = "ci_mock_prompt_injection"
    run_artifacts_dir = _REPO_ROOT / "run_artifacts" / run_name

    env = os.environ.copy()
    env["MANTIS_MOCK_LLM"] = "1"

    result = subprocess.run(
        MANTIS_CMD + ["--run", str(_CI_ATTACK_CONFIG)],
        env=env, capture_output=True, text=True, timeout=180, cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"--run failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    trace_file = run_artifacts_dir / "traces.jsonl"
    assert trace_file.exists(), "traces.jsonl not found after --run"
    events = [json.loads(ln) for ln in trace_file.read_text().splitlines() if ln.strip()]
    event_types = {e.get("event_type") for e in events}
    assert "ATTACK_INJECTED" in event_types, (
        f"No ATTACK_INJECTED in trace -- the attack plugin never actually fired; found: {event_types}"
    )

    eval_result = subprocess.run(
        MANTIS_CMD + ["--evaluate", str(run_artifacts_dir)],
        capture_output=True, text=True, timeout=60, cwd=str(_REPO_ROOT),
    )
    assert eval_result.returncode == 0, f"--evaluate failed: {eval_result.stderr}"
    results = json.loads(eval_result.stdout)
    assert results["attack_ground_truth"]["attack_fired"] is True


# ---------------------------------------------------------------------------
# Gap 6d -- mantis --evaluate on a synthetic run dir
# ---------------------------------------------------------------------------

def _make_synthetic_run_dir(tmp_path: Path) -> Path:
    """Create a minimal run dir with a traces.jsonl + run_manifest.json
    so --evaluate can be tested without a real LLM run."""
    run_name = "integration_test_run"
    run_dir = tmp_path / "run_artifacts" / run_name
    run_dir.mkdir(parents=True)

    # Minimal valid events
    import json as _json
    from datetime import datetime
    ts = datetime.utcnow().isoformat()
    events = [
        {"event_type": "EXPERIMENT_START", "run_id": run_name, "timestamp": ts,
         "config_hash": "abc123", "seed": 42, "status": "running"},
        {"event_type": "WORKFLOW_START", "run_id": run_name, "timestamp": ts,
         "workflow_id": "front_office_monitoring", "business_domain": "front_office",
         "workflow_type": "front_office_monitoring"},
        {"event_type": "AGENT_START", "run_id": run_name, "timestamp": ts,
         "agent_id": "transaction_monitoring_agent"},
        {"event_type": "TOOL_CALL", "run_id": run_name, "timestamp": ts,
         "tool_name": "get_transaction_context", "operation_type": "read",
         "risk_level": "low", "data_sensitivity": "high", "financial_side_effect": False},
        {"event_type": "TOOL_RESULT", "run_id": run_name, "timestamp": ts,
         "tool_name": "get_transaction_context", "result": "ok"},
        {"event_type": "WORKFLOW_END", "run_id": run_name, "timestamp": ts,
         "workflow_id": "front_office_monitoring", "outcome": "manual_review"},
        {"event_type": "EXPERIMENT_END", "run_id": run_name, "timestamp": ts,
         "config_hash": "abc123", "seed": 42, "status": "success"},
    ]
    trace_path = run_dir / "traces.jsonl"
    trace_path.write_text("\n".join(_json.dumps(e) for e in events) + "\n")

    manifest = {
        "config_hash": "abc123",
        "seed": 42,
        "config": {
            "experiment": {"name": run_name, "seed": 42, "domain": "front_office",
                           "workflow": "front_office_monitoring",
                           "scenario": "front_office_monitoring"},
            "evaluation": {
                "expected_tools": ["get_transaction_context"],
                "forbidden_tools": ["execute_transfer"],
                "expected_terminal_state": "manual_review",
            },
        },
        "environment": {},
    }
    (run_dir / "run_manifest.json").write_text(_json.dumps(manifest, indent=2))
    return run_dir


def test_evaluate_produces_results_json(tmp_path, monkeypatch):
    """--evaluate on a synthetic run dir must write evaluation_results.json."""
    monkeypatch.chdir(tmp_path)
    run_dir = _make_synthetic_run_dir(tmp_path)

    result = _run_mantis(["--evaluate", str(run_dir)])
    assert result.returncode == 0, (
        f"--evaluate failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    results_file = run_dir / "evaluation_results.json"
    assert results_file.exists(), "evaluation_results.json not created by --evaluate"
    results = json.loads(results_file.read_text())

    assert "trace_completeness" in results
    assert "tool_use_correctness" in results
    assert "workflow_outcome" in results
    assert "artifact_integrity" in results
    assert "banking_workflow_coverage" in results

    assert results["trace_completeness"]["score"] == 1.0
    assert results["tool_use_correctness"]["score"] == 1.0
    assert results["workflow_outcome"]["score"] == 1.0
    assert results["artifact_integrity"]["score"] == 1.0
    assert results["banking_workflow_coverage"]["score"] > 0.0


def test_evaluate_appends_evaluation_events_to_trace(tmp_path, monkeypatch):
    """After --evaluate, traces.jsonl must contain EVALUATION_RESULT events."""
    monkeypatch.chdir(tmp_path)
    run_dir = _make_synthetic_run_dir(tmp_path)

    _run_mantis(["--evaluate", str(run_dir)])

    trace_file = run_dir / "traces.jsonl"
    events = [json.loads(ln) for ln in trace_file.read_text().splitlines() if ln.strip()]
    eval_events = [e for e in events if e.get("event_type") == "EVALUATION_RESULT"]
    assert len(eval_events) > 0, (
        "No EVALUATION_RESULT events appended to traces.jsonl after --evaluate"
    )
    # Each evaluation event must carry run_id, evaluator, metric, score
    for ev in eval_events:
        assert "run_id" in ev
        assert "evaluator" in ev
        assert "metric" in ev
        assert "score" in ev


def test_evaluate_artifact_integrity_detects_matching_run_id(tmp_path, monkeypatch):
    """artifact_integrity evaluator must confirm run_id consistency."""
    monkeypatch.chdir(tmp_path)
    run_dir = _make_synthetic_run_dir(tmp_path)

    _run_mantis(["--evaluate", str(run_dir)])

    results = json.loads((run_dir / "evaluation_results.json").read_text())
    integrity = results["artifact_integrity"]
    assert integrity["manifest_run_id_matches_trace"] is True


def test_evaluate_workflow_coverage_front_office(tmp_path, monkeypatch):
    """banking_workflow_coverage must detect front_office domain from the trace."""
    monkeypatch.chdir(tmp_path)
    run_dir = _make_synthetic_run_dir(tmp_path)

    _run_mantis(["--evaluate", str(run_dir)])

    results = json.loads((run_dir / "evaluation_results.json").read_text())
    coverage = results["banking_workflow_coverage"]
    assert "front_office" in coverage["domains_exercised"]
