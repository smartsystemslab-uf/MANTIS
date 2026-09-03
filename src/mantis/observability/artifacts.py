import json
import hashlib
from datetime import datetime
from pathlib import Path
from mantis.config.models import ExperimentConfig

def create_run_manifest(config: ExperimentConfig, output_dir: Path) -> Path:
    config_dict = config.model_dump(exclude_none=True)
    config_str = json.dumps(config_dict, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()
    
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "config_hash": config_hash,
        "seed": config.experiment.seed,
        "config": config_dict
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    return manifest_path

import os
from typing import List, Any
from mantis.observability.events import BaseTraceEvent

class TraceArtifactWriter:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir
        self.trace_file = os.path.join(run_dir, "traces.jsonl")
        os.makedirs(self.run_dir, exist_ok=True)
        # Each run gets exactly one TraceArtifactWriter; start its trace file
        # empty so repeated runs of the same experiment name (including
        # campaign subprocess runs) don't silently merge events across runs.
        open(self.trace_file, "w").close()

    def write_event(self, event: BaseTraceEvent):
        """Append a single event to the JSONL trace file."""
        with open(self.trace_file, "a") as f:
            # Pydantic v2 model_dump_json handles datetime serialization
            f.write(event.model_dump_json() + "\n")

    def write_events(self, events: List[BaseTraceEvent]):
        """Append multiple events to the JSONL trace file."""
        with open(self.trace_file, "a") as f:
            for event in events:
                f.write(event.model_dump_json() + "\n")


def append_trace_events(run_dir: str, events: List[BaseTraceEvent]) -> None:
    """Append events (e.g. post-run EVALUATION_RESULT) to an existing run's
    traces.jsonl without truncating it. Unlike constructing a fresh
    TraceArtifactWriter (which intentionally starts a run's trace file empty
    -- see its docstring), this is for appending to a run that already ran.
    """
    trace_file = os.path.join(run_dir, "traces.jsonl")
    if not os.path.exists(trace_file):
        return
    with open(trace_file, "a") as f:
        for event in events:
            f.write(event.model_dump_json() + "\n")
