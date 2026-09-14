"""Minimal UI (Post-Paper Extension, coding plan §11: "Minimal UI -- a
schema-driven editor and trace viewer that invokes the same CLI/API; no
separate business logic").

Every mutating action (validate / run / evaluate) shells out to the exact
same `mantis` console-script entrypoint a terminal user would run --
deliberately not a second, UI-specific code path that could drift from the
real CLI's behavior. Read-only introspection (schema, inventory, registry
listings, reading a run's own trace file) calls the same underlying
models/registries directly, since those are already the single source of
truth `mantis --inventory`/`--generate-schemas` read from too.

Run it with:
    mantis --ui
or directly:
    python -m mantis.ui.server
"""
import asyncio
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from mantis.config.models import ExperimentConfig
from mantis.core.registry import (
    domain_registry, scenario_registry, workflow_registry, plugin_registry, evaluator_registry,
)
from mantis.runtime.adapter import NativeBankingAdapter

REPO_ROOT = Path(__file__).resolve().parents[3]
UI_CONFIG_DIR = REPO_ROOT / "configs" / "ui_generated"
STATIC_DIR = Path(__file__).parent / "static"
MANTIS_CMD = [sys.executable, "-m", "mantis.cli.main"]

app = FastAPI(title="MANTIS Minimal UI")


class RunConfigPayload(BaseModel):
    config: dict[str, Any]


def _write_config(config: dict[str, Any]) -> Path:
    """Validates the submitted dict against the real ExperimentConfig model
    (same schema the CLI parses every config through) before it ever
    touches disk, then writes it as YAML for the CLI subprocess to read --
    the same file format/shape a hand-written experiment config is."""
    try:
        validated = ExperimentConfig(**config)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid config: {e}")

    UI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    name = validated.experiment.name or f"ui_run_{uuid.uuid4().hex[:8]}"
    path = UI_CONFIG_DIR / f"{name}.yaml"
    with open(path, "w") as f:
        yaml.dump(json.loads(validated.model_dump_json(exclude_none=True)), f, sort_keys=False)
    return path


def _run_cli(args: list[str], timeout: int = 180) -> dict[str, Any]:
    result = subprocess.run(
        MANTIS_CMD + args, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=timeout,
    )
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/schema")
def get_schema():
    """The real ExperimentConfig JSON schema -- identical to what
    `mantis --generate-schemas` writes to configs/experiment_schema.json."""
    return JSONResponse(ExperimentConfig.model_json_schema())


@app.get("/api/registries")
def get_registries():
    """Real registry contents -- the same dicts `mantis --validate` checks
    a config's domain/workflow/scenario/plugin references against."""
    return {
        "domains": sorted(domain_registry.all().keys()),
        "workflows": sorted(workflow_registry.all().keys()),
        "scenarios": sorted(scenario_registry.all().keys()),
        "plugins": sorted(plugin_registry.all().keys()),
        "evaluators": sorted(evaluator_registry.all().keys()),
    }


@app.get("/api/inventory")
def get_inventory():
    """The real live inventory -- identical to `mantis --inventory`."""
    inv = NativeBankingAdapter().inventory()
    return json.loads(inv.model_dump_json())


@app.post("/api/validate")
def validate(payload: RunConfigPayload):
    path = _write_config(payload.config)
    return _run_cli(["--validate", str(path)])


@app.post("/api/run")
async def run(payload: RunConfigPayload):
    path = _write_config(payload.config)
    loop = asyncio.get_event_loop()
    # Run/etc. can take tens of seconds against a live LLM -- off the event
    # loop so the server stays responsive to other requests meanwhile.
    result = await loop.run_in_executor(None, lambda: _run_cli(["--run", str(path)], timeout=300))
    result["run_name"] = path.stem
    return result


@app.post("/api/runs/{run_name}/evaluate")
def evaluate(run_name: str):
    run_dir = REPO_ROOT / "run_artifacts" / run_name
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"No run_artifacts directory for '{run_name}'")
    return _run_cli(["--evaluate", str(run_dir)])


@app.get("/api/runs")
def list_runs():
    """Every existing run_artifacts/<name> directory, with its manifest
    summary if one exists -- the same directories `mantis --evaluate` and
    `mantis --report` already read."""
    runs_dir = REPO_ROOT / "run_artifacts"
    if not runs_dir.exists():
        return []
    runs = []
    for entry in sorted(runs_dir.iterdir()):
        if not entry.is_dir():
            continue
        manifest_path = entry / "run_manifest.json"
        manifest_summary = None
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text())
                manifest_summary = {
                    "config_hash": manifest.get("config_hash"),
                    "seed": manifest.get("seed"),
                    "domain": manifest.get("config", {}).get("experiment", {}).get("domain"),
                    "workflow": manifest.get("config", {}).get("experiment", {}).get("workflow"),
                }
            except Exception:
                pass
        runs.append({
            "name": entry.name,
            "has_trace": (entry / "traces.jsonl").exists(),
            "has_evaluation": (entry / "evaluation_results.json").exists(),
            "manifest": manifest_summary,
        })
    return runs


@app.get("/api/runs/{run_name}/trace")
def get_trace(run_name: str):
    trace_file = REPO_ROOT / "run_artifacts" / run_name / "traces.jsonl"
    if not trace_file.exists():
        raise HTTPException(status_code=404, detail=f"No traces.jsonl for run '{run_name}'")
    events = []
    for line in trace_file.read_text().splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


@app.get("/api/runs/{run_name}/evaluation")
def get_evaluation(run_name: str):
    eval_file = REPO_ROOT / "run_artifacts" / run_name / "evaluation_results.json"
    if not eval_file.exists():
        raise HTTPException(status_code=404, detail=f"No evaluation_results.json for run '{run_name}' -- run evaluate first")
    return json.loads(eval_file.read_text())


def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
