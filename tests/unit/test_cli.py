import pytest
import subprocess
from pathlib import Path
import json

def test_cli_help():
    result = subprocess.run(["mantis", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "--run" in result.stdout
    assert "--campaign" in result.stdout

def test_cli_inventory():
    result = subprocess.run(["mantis", "--inventory"], capture_output=True, text=True)
    assert result.returncode == 0
    # Output should be valid JSON
    data = json.loads(result.stdout)
    assert "workflows" in data
    assert "tools" in data

def test_cli_generate_schemas(tmp_path):
    result = subprocess.run(["mantis", "--generate-schemas"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Schema successfully generated" in result.stdout
    schema_file = Path("configs/experiment_schema.json")
    assert schema_file.exists()

def test_cli_validate_valid():
    result = subprocess.run(["mantis", "--validate", "configs/baselines/front_office_baseline.yaml"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "is valid" in result.stdout

def test_cli_validate_invalid():
    result = subprocess.run(["mantis", "--validate", "configs/invalid/unknown_scenario.yaml"], capture_output=True, text=True)
    assert result.returncode != 0

def test_cli_inspect_scenario():
    result = subprocess.run(["mantis", "--inspect", "front_office_monitoring"], capture_output=True, text=True)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["type"] == "registered_scenario"
    assert data["scenario_id"] == "front_office_monitoring"

def test_cli_inspect_plugin():
    result = subprocess.run(["mantis", "--inspect", "prompt_injection"], capture_output=True, text=True)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["type"] == "registered_plugin"
    assert data["plugin_id"] == "prompt_injection"

def test_cli_init_workspace(tmp_path):
    target = tmp_path / "new_workspace"
    result = subprocess.run(["mantis", "--init", str(target)], capture_output=True, text=True)
    assert result.returncode == 0
    assert (target / "configs" / "sample_experiment.yaml").exists()

