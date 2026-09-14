import json
from datetime import datetime
from pathlib import Path
from mantis.cli.campaign import CampaignManager


def test_run_name_for_reads_the_real_experiment_name(tmp_path: Path):
    # A baseline-style config where the filename does not match
    # experiment.name -- e.g. configs/baselines/front_office_baseline.yaml
    # actually names itself "front_office_monitoring". Aggregation must
    # follow the real name, since that's the run_artifacts/<name>/
    # directory mantis --run actually writes to.
    config_file = tmp_path / "front_office_baseline.yaml"
    config_file.write_text(
        "experiment:\n"
        "  name: front_office_monitoring\n"
        "  seed: 42\n"
        "  domain: front_office\n"
        "  workflow: front_office_monitoring\n"
        "  scenario: front_office_monitoring\n"
    )

    assert CampaignManager._run_name_for(config_file) == "front_office_monitoring"


def test_run_name_for_falls_back_to_filename_stem_on_malformed_config(tmp_path: Path):
    config_file = tmp_path / "broken.yaml"
    config_file.write_text("not: {valid: [experiment config")

    assert CampaignManager._run_name_for(config_file) == "broken"


def _make_synthetic_campaign_run(output_dir: Path, run_name: str = "synthetic_run") -> Path:
    """WP7 acceptance criterion: run directories carry a written report,
    not only a stdout printout. Builds just enough of a real run directory
    (a parseable traces.jsonl + run_manifest.json) for TraceEvaluator to
    score it for real, rather than mocking the evaluator."""
    run_dir = output_dir / run_name
    run_dir.mkdir(parents=True)
    ts = datetime.utcnow().isoformat()
    events = [
        {"event_type": "EXPERIMENT_START", "run_id": run_name, "timestamp": ts, "config_hash": "abc", "seed": 1, "status": "running"},
        {"event_type": "WORKFLOW_START", "run_id": run_name, "timestamp": ts, "workflow_id": "front_office_monitoring", "business_domain": "front_office"},
        {"event_type": "AGENT_START", "run_id": run_name, "timestamp": ts, "agent_id": "transaction_monitoring_agent"},
        {"event_type": "WORKFLOW_END", "run_id": run_name, "timestamp": ts, "workflow_id": "front_office_monitoring", "outcome": "completed"},
        {"event_type": "EXPERIMENT_END", "run_id": run_name, "timestamp": ts, "config_hash": "abc", "seed": 1, "status": "success"},
    ]
    (run_dir / "traces.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
    manifest = {
        "config_hash": "abc", "seed": 1,
        "config": {"experiment": {"name": run_name, "seed": 1, "domain": "front_office", "workflow": "front_office_monitoring", "scenario": "front_office_monitoring"}},
        "environment": {},
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest))
    return run_dir


def test_generate_report_writes_report_md_into_the_campaign_directory(tmp_path: Path, capsys):
    manager = CampaignManager(str(tmp_path))
    manager.output_dir = tmp_path
    _make_synthetic_campaign_run(tmp_path)

    manager.generate_report()

    report_path = tmp_path / "report.md"
    assert report_path.exists(), "generate_report() must persist report.md, not only print to stdout"
    text = report_path.read_text()
    assert "synthetic_run" in text
    assert "MANTIS Security Campaign Report" in text
    # The persisted file and the stdout printout must be the same report,
    # not two independently-maintained copies that could drift apart.
    printed = capsys.readouterr().out
    assert "synthetic_run" in printed
