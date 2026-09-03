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
